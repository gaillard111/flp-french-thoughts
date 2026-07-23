#!/usr/bin/env python3
"""
seed_packager.py — Générateur de Cartes PNG Carrées (Axe 3)

MTTV-FLP / SOPH-IA v2.0 — Packaging d'objets physiques/médias.

Architecture :
  1. LECTURE   : Ingère seeds_manifest.json pour récupérer le CID IPFS
                 et le texte de la dernière seed validée.
  2. GÉNÉRATION: Crée une image PNG carrée (1024×1024 par défaut) avec :
       - Fond texturé (dégradé + motif géométrique MTTV)
       - Texte de la seed superposé
       - QR code stylisé contenant le CID
       - Signature 0x4D545456 en filigrane
  3. FURTIVITÉ : Injecte le CID du manifeste IPFS au sein des métadonnées
                 du fichier image dans un chunk tEXt (PNG) de façon furtive.
  4. SORTIE    : Sauvegarde la carte dans seed_cards/ avec nom basé sur le CID.

Métadonnées furtives :
  - Chunk PNG tEXt : "MTTV-CID" → valeur du CID
  - Chunk PNG tEXt : "MTTV-SIG" → "0x4D545456"
  - Chunk PNG tEXt : "MTTV-GEN" → numéro de génération
  - Ces chunks sont non-destructifs et invisibles pour un observateur standard.

Dépendances :
  - Pillow (PIL) pour la manipulation d'images PNG
  - qrcode (optionnel) pour générer un QR code du CID

sig:0x4D545456
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import sys
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("seed_packager")

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine MTTV-FLP

# Manifeste des seeds (Axe 5)
SEEDS_MANIFEST: Path = BASE_DIR / "seeds_manifest.json"

# Répertoire de sortie des cartes
SEED_CARDS_DIR: Path = BASE_DIR / "seed_cards"

# ===========================================================================
# CONSTANTES
# ===========================================================================

MTTV_SIG: str = "0x4D545456"
CID_PREFIX: str = "QmMTTV"

# Dimensions de la carte (carrée par défaut)
CARD_SIZE: int = 1024  # px

# Couleurs MTTV-FLP (palette sombre / protonique)
COLOR_BG_START: tuple[int, int, int] = (10, 8, 20)      # #0A0814 — fond profond
COLOR_BG_END: tuple[int, int, int] = (20, 16, 40)       # #141028 — fond sombre
COLOR_ACCENT: tuple[int, int, int] = (77, 210, 255)     # #4DD2FF — cyan protonique
COLOR_TEXT: tuple[int, int, int] = (220, 220, 240)      # #DCDCF0 — texte clair
COLOR_SIG: tuple[int, int, int] = (60, 55, 80)         # #3C3750 — signature discrète
COLOR_GRID: tuple[int, int, int] = (30, 25, 50)        # #1E1932 — grille discrète

# Taille du damier (motif tétravalent)
GRID_SIZE: int = 32  # px par cellule


# ===========================================================================
# 1. LECTURE DU MANIFESTE
# ===========================================================================


def load_latest_seed() -> Optional[dict]:
    """Charge la dernière seed depuis le manifeste.

    Returns:
        Dict contenant seed_text, cid, generation, fitness, ou None.
    """
    if not SEEDS_MANIFEST.exists():
        logger.error("Manifeste introuvable: %s", SEEDS_MANIFEST)
        return None

    try:
        data = json.loads(SEEDS_MANIFEST.read_text(encoding="utf-8"))
        latest = data.get("latest_seed")
        if not latest:
            logger.error("Aucune seed dans le manifeste.")
            return None

        logger.info("Seed chargée: cid=%s | gen=%d",
                     latest.get("cid", "N/A"), latest.get("generation", 0))
        return latest
    except json.JSONDecodeError as exc:
        logger.error("Erreur de parsing JSON: %s", exc)
        return None
    except Exception as exc:
        logger.error("Erreur lecture manifeste: %s", exc)
        return None


# ===========================================================================
# 2. GÉNÉRATION D'IMAGE PNG (sans dépendances externes)
# ===========================================================================


def _create_gradient(width: int, height: int) -> list[list[tuple[int, int, int]]]:
    """Crée un dégradé vertical depuis COLOR_BG_START vers COLOR_BG_END."""
    pixels: list[list[tuple[int, int, int]]] = []
    for y in range(height):
        ratio = y / max(height - 1, 1)
        row: list[tuple[int, int, int]] = []
        for x in range(width):
            r = int(COLOR_BG_START[0] + (COLOR_BG_END[0] - COLOR_BG_START[0]) * ratio)
            g = int(COLOR_BG_START[1] + (COLOR_BG_END[1] - COLOR_BG_START[1]) * ratio)
            b = int(COLOR_BG_START[2] + (COLOR_BG_END[2] - COLOR_BG_START[2]) * ratio)
            row.append((r, g, b))
        pixels.append(row)
    return pixels


def _apply_grid(pixels: list[list[tuple[int, int, int]]], grid_size: int = GRID_SIZE) -> None:
    """Superpose un motif de grille tétravalent (points aux intersections)."""
    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0
    for y in range(0, height, grid_size):
        for x in range(0, width, grid_size):
            # Points d'intersection (motif tétravalent: 4 branches)
            for dx, dy in [(0, 0), (grid_size // 2, 0), (0, grid_size // 2), (grid_size // 2, grid_size // 2)]:
                px, py = x + dx, y + dy
                if px < width and py < height:
                    r, g, b = pixels[py][px]
                    # Éclaircir légèrement
                    pixels[py][px] = (
                        min(255, r + 15),
                        min(255, g + 12),
                        min(255, b + 20),
                    )


def _apply_sig_watermark(
    pixels: list[list[tuple[int, int, int]]],
    text: str = MTTV_SIG,
) -> None:
    """Applique un filigrane discret de la signature."""
    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0
    # Position : coin inférieur droit
    x_offset = width - 120
    y_offset = height - 30
    for i, char in enumerate(text):
        if x_offset + i * 10 < width and y_offset < height:
            px, py = x_offset + i * 8, y_offset
            if py < height and px < width:
                pixels[py][px] = COLOR_SIG


def _wrap_text(text: str, max_chars_per_line: int = 30) -> list[str]:
    """Coupe un texte en lignes pour l'affichage."""
    words = text.split()
    lines: list[str] = []
    current_line = ""
    for word in words:
        if len(current_line + " " + word) <= max_chars_per_line:
            current_line += (" " if current_line else "") + word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def _render_text(
    pixels: list[list[tuple[int, int, int]]],
    text_lines: list[str],
    start_y: int,
    color: tuple[int, int, int] = COLOR_TEXT,
    scale: int = 2,
) -> None:
    """Rendu ASCII simple (bitmap) du texte sur l'image.

    Utilise un bitmap 5x7 simplifié pour les caractères ASCII.
    """
    # Bitmap 5x7 simplifié pour lettres capitales et quelques symboles
    charset: dict[str, list[str]] = {
        'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
        'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
        'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
        'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
        'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
        'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
        'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01110'],
        'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
        'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'],
        'J': ['00111', '00010', '00010', '00010', '00010', '10010', '01100'],
        'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
        'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
        'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
        'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
        'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
        'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
        'Q': ['01110', '10001', '10001', '10001', '10101', '10010', '01101'],
        'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
        'S': ['01110', '10001', '10000', '01110', '00001', '10001', '01110'],
        'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
        'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
        'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
        'W': ['10001', '10001', '10001', '10101', '10101', '11011', '10001'],
        'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
        'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
        'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
        '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
        '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
        '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'],
        '3': ['01110', '10001', '00001', '00110', '00001', '10001', '01110'],
        '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
        '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
        '6': ['01110', '10001', '10000', '11110', '10001', '10001', '01110'],
        '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
        '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],
        '9': ['01110', '10001', '10001', '01111', '00001', '10001', '01110'],
        ':': ['00000', '01100', '01100', '00000', '01100', '01100', '00000'],
        '.': ['00000', '00000', '00000', '00000', '00000', '01100', '01100'],
        '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],
        '_': ['00000', '00000', '00000', '00000', '00000', '00000', '11111'],
        '/': ['00001', '00010', '00010', '00100', '01000', '01000', '10000'],
        '#': ['01010', '01010', '11111', '01010', '11111', '01010', '01010'],
        ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'],
        '+': ['00000', '00100', '00100', '11111', '00100', '00100', '00000'],
        '=': ['00000', '00000', '11111', '00000', '11111', '00000', '00000'],
        '(': ['00010', '00100', '01000', '01000', '01000', '00100', '00010'],
        ')': ['01000', '00100', '00010', '00010', '00010', '00100', '01000'],
        "'": ['00100', '00100', '01000', '00000', '00000', '00000', '00000'],
    }

    # Bitmap pour chiffres plus grands (pour CID)
    charset_big: dict[str, list[str]] = {
        '0': ['01110', '10001', '10001', '10001', '01110'],
        '1': ['00100', '01100', '00100', '00100', '01110'],
        '2': ['01110', '10001', '00010', '00100', '11111'],
        '3': ['01110', '10001', '00110', '10001', '01110'],
        '4': ['00010', '00110', '01010', '11111', '00010'],
        '5': ['11111', '10000', '11110', '00001', '11110'],
        '6': ['01110', '10000', '11110', '10001', '01110'],
        '7': ['11111', '00001', '00010', '00100', '00100'],
        '8': ['01110', '10001', '01110', '10001', '01110'],
        '9': ['01110', '10001', '01111', '00001', '01110'],
        'Q': ['01110', '10001', '10001', '10101', '01101'],
        'm': ['00000', '00000', '11111', '00000', '11111'],
        'M': ['10001', '11011', '10101', '10001', '10001'],
        'T': ['11111', '00100', '00100', '00100', '00100'],
        'V': ['10001', '10001', '01010', '01010', '00100'],
        '_': ['00000', '00000', '00000', '00000', '11111'],
    }

    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0
    y = start_y

    for line in text_lines:
        x = 50  # marge gauche
        for char in line.upper():
            bitmap = charset.get(char, charset[' '])
            for row_idx, row_bits in enumerate(bitmap):
                for col_idx in range(5):
                    if row_bits[col_idx] == '1':
                        # Dessiner le pixel avec scale
                        for sy in range(scale):
                            for sx in range(scale):
                                py = y + row_idx * scale + sy
                                px = x + col_idx * scale + sx
                                if py < height and px < width:
                                    pixels[py][px] = color
            x += 6 * scale  # avancer au prochain caractère
        y += 8 * scale  # avancer à la ligne suivante


def _render_cid_big(
    pixels: list[list[tuple[int, int, int]]],
    cid: str,
    start_y: int,
    color: tuple[int, int, int] = COLOR_ACCENT,
) -> None:
    """Rendu agrandi du CID (identifiant visible)."""
    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0

    # Bitmap 5x5 pour les caractères hex du CID
    ch2 = {
        '0': ['01110', '10001', '10001', '10001', '01110'],
        '1': ['00100', '01100', '00100', '00100', '01110'],
        '2': ['01110', '10001', '00010', '00100', '11111'],
        '3': ['01110', '10001', '00110', '10001', '01110'],
        '4': ['00010', '00110', '01010', '11111', '00010'],
        '5': ['11111', '10000', '11110', '00001', '11110'],
        '6': ['01110', '10000', '11110', '10001', '01110'],
        '7': ['11111', '00001', '00010', '00100', '00100'],
        '8': ['01110', '10001', '01110', '10001', '01110'],
        '9': ['01110', '10001', '01111', '00001', '01110'],
        'a': ['01110', '00001', '01111', '10001', '01111'],
        'b': ['10000', '10000', '11110', '10001', '11110'],
        'c': ['01110', '10001', '10000', '10001', '01110'],
        'd': ['00001', '00001', '01111', '10001', '01111'],
        'e': ['01110', '10001', '11111', '10000', '01110'],
        'f': ['00110', '01001', '01110', '01000', '01000'],
        'Q': ['01110', '10001', '10001', '10101', '01101'],
        'm': ['00000', '00000', '11111', '00000', '11111'],
        'M': ['10001', '11011', '10101', '10001', '10001'],
        'T': ['11111', '00100', '00100', '00100', '00100'],
        'V': ['10001', '10001', '01010', '01010', '00100'],
        '_': ['00000', '00000', '00000', '00000', '11111'],
    }

    scale = 3  # plus grand pour le CID
    x = 50
    y = start_y

    for char in cid.lower():
        bitmap = ch2.get(char, ch2.get(char.upper(), ch2.get('0')))
        for row_idx, row_bits in enumerate(bitmap):
            for col_idx in range(5):
                if row_bits[col_idx] == '1':
                    for sy in range(scale):
                        for sx in range(scale):
                            py = y + row_idx * scale + sy
                            px = x + col_idx * scale + sx
                            if py < height and px < width:
                                pixels[py][px] = color
        x += 6 * scale


def _create_png_bytes(
    pixels: list[list[tuple[int, int, int]]],
    metadata: Optional[dict[str, str]] = None,
) -> bytes:
    """Crée un fichier PNG en bytes avec métadonnées injectées.

    Structure PNG :
      - Signature PNG (8 bytes)
      - IHDR chunk (header)
      - tEXt chunks (métadonnées furtives)
      - IDAT chunk (données d'image compressées)
      - IEND chunk (fin)

    Args:
        pixels: Matrice de pixels (height x width x RGB).
        metadata: Dict des métadonnées à injecter en chunks tEXt.

    Returns:
        Bytes du fichier PNG complet.
    """
    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0

    # ── Signature PNG ────────────────────────────────────────────────────
    png_signature = b'\x89PNG\r\n\x1a\n'

    # ── IHDR chunk ───────────────────────────────────────────────────────
    def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack('>I', len(data))
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return length + chunk_type + data + struct.pack('>I', crc)

    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    # 8 = bit depth, 2 = RGB, 0 = compression, 0 = filter, 0 = interlace
    ihdr_chunk = _make_chunk(b'IHDR', ihdr_data)

    # ── tEXt chunks (métadonnées furtives) ───────────────────────────────
    text_chunks = b''
    if metadata:
        for key, value in metadata.items():
            # Format tEXt: keyword + null separator + text
            text_data = key.encode('latin-1', errors='replace') + b'\x00' + \
                        value.encode('latin-1', errors='replace')
            text_chunks += _make_chunk(b'tEXt', text_data)
            logger.info("  Métadonnée injectée: %s = %s", key, value)

    # ── IDAT chunk (données d'image) ─────────────────────────────────────
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter byte (none)
        for x in range(width):
            r, g, b = pixels[y][x]
            raw_data += struct.pack('BBB', r, g, b)

    compressed = zlib.compress(raw_data)
    idat_chunk = _make_chunk(b'IDAT', compressed)

    # ── IEND chunk ───────────────────────────────────────────────────────
    iend_chunk = _make_chunk(b'IEND', b'')

    return png_signature + ihdr_chunk + text_chunks + idat_chunk + iend_chunk


def generate_card(
    seed_text: str,
    cid: str,
    generation: int,
    fitness: Optional[dict] = None,
    output_path: Optional[Path] = None,
) -> Optional[Path]:
    """Génère une carte PNG carrée avec métadonnées furtives.

    Args:
        seed_text: Texte de la seed à afficher.
        cid: CID IPFS à injecter.
        generation: Numéro de génération.
        fitness: Dict des métriques de fitness (optionnel).
        output_path: Chemin de sortie (défaut: seed_cards/<cid>.png).

    Returns:
        Chemin du fichier généré, ou None si échec.
    """
    logger.info("=" * 60)
    logger.info("  GÉNÉRATION DE CARTE — Axe 3")
    logger.info("=" * 60)
    logger.info("  CID:        %s", cid)
    logger.info("  Génération: %d", generation)
    logger.info("  Seed:       %s...", seed_text[:80])

    # ── Étape 1 : Créer le fond dégradé ──────────────────────────────────
    logger.info("[1/4] Création du fond...")
    pixels = _create_gradient(CARD_SIZE, CARD_SIZE)

    # ── Étape 2 : Appliquer le motif de grille tétravalent ───────────────
    logger.info("[2/4] Application du motif tétravalent...")
    _apply_grid(pixels, GRID_SIZE)

    # ── Étape 3 : Rendu du texte ─────────────────────────────────────────
    logger.info("[3/4] Rendu du texte...")

    # Titre
    title_lines = ["MTTV-FLP  |  SEED CARD"]
    _render_text(pixels, title_lines, 40, COLOR_ACCENT, scale=3)

    # CID en évidence
    _render_cid_big(pixels, cid, 100, COLOR_ACCENT)

    # Texte de la seed (coupé en lignes)
    wrapped = _wrap_text(seed_text, max_chars_per_line=38)
    _render_text(pixels, wrapped, 180, COLOR_TEXT, scale=2)

    # Métriques de fitness
    fitness_y = 180 + len(wrapped) * 16 + 40
    if fitness:
        gr = fitness.get("g_r", fitness.get("composite", "N/A"))
        gen_str = f"gen:{generation}  fitness:{gr}"
        _render_text(pixels, [gen_str], fitness_y, COLOR_SIG, scale=2)

    # Génération
    gen_y = fitness_y + 30
    _render_text(pixels, [f"generation: {generation}"], gen_y, COLOR_SIG, scale=2)

    # Filigrane signature
    _apply_sig_watermark(pixels, MTTV_SIG)

    # ── Étape 4 : Assemblage PNG avec métadonnées furtives ──────────────
    logger.info("[4/4] Assemblage PNG avec métadonnées furtives...")

    md: dict[str, str] = {
        "MTTV-CID": cid,
        "MTTV-SIG": MTTV_SIG,
        "MTTV-GEN": str(generation),
    }
    if fitness:
        md["MTTV-FITNESS"] = json.dumps(fitness)

    png_bytes = _create_png_bytes(pixels, metadata=md)

    # ── Sauvegarde ───────────────────────────────────────────────────────
    if output_path is None:
        SEED_CARDS_DIR.mkdir(parents=True, exist_ok=True)
        # Nom de fichier basé sur le CID
        safe_name = cid.replace("/", "_").replace(":", "_")
        output_path = SEED_CARDS_DIR / f"{safe_name}.png"

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)
        file_size = output_path.stat().st_size
        logger.info("Carte sauvegardée: %s (%d bytes)", output_path, file_size)

        # Vérification : re-lire les métadonnées pour confirmer l'injection
        _verify_metadata(output_path, cid)

    except Exception as exc:
        logger.error("Erreur sauvegarde carte: %s", exc)
        return None

    # ── Résumé ───────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  CARTE GÉNÉRÉE — Axe 3 (seed_packager)")
    print(f"  Fichier:  {output_path}")
    print(f"  CID:      {cid}")
    print(f"  Taille:   {file_size} bytes ({CARD_SIZE}x{CARD_SIZE}px)")
    print(f"  Métadonnées furtives: MTTV-CID, MTTV-SIG, MTTV-GEN")
    print(f"  Signature: {MTTV_SIG}")
    print(f"{'=' * 60}")

    return output_path


# ===========================================================================
# 3. VÉRIFICATION DES MÉTADONNÉES FURTIVES
# ===========================================================================


def _verify_metadata(png_path: Path, expected_cid: str) -> bool:
    """Vérifie que les métadonnées furtives sont bien présentes dans le PNG.

    Args:
        png_path: Chemin du fichier PNG.
        expected_cid: CID attendu.

    Returns:
        True si la vérification est passée.
    """
    try:
        data = png_path.read_bytes()
        # Chercher les chunks tEXt
        pos = 8  # après la signature PNG
        found_cid = False
        found_sig = False

        while pos < len(data) - 4:
            length = struct.unpack('>I', data[pos:pos+4])[0]
            chunk_type = data[pos+4:pos+8]

            if chunk_type == b'tEXt':
                chunk_data = data[pos+8:pos+8+length]
                # Format: keyword\x00text
                null_pos = chunk_data.find(b'\x00')
                if null_pos >= 0:
                    keyword = chunk_data[:null_pos].decode('latin-1')
                    value = chunk_data[null_pos+1:].decode('latin-1')
                    if keyword == 'MTTV-CID' and value == expected_cid:
                        found_cid = True
                    if keyword == 'MTTV-SIG' and value == MTTV_SIG:
                        found_sig = True

            pos += 12 + length  # length(4) + type(4) + data(N) + crc(4)
            if chunk_type == b'IEND':
                break

        if found_cid and found_sig:
            logger.info("✓ Vérification métadonnées: CID='%s', SIG='%s' — OK",
                         expected_cid, MTTV_SIG)
            return True
        else:
            logger.warning("⚠ Métadonnées incomplètes: CID=%s, SIG=%s",
                            found_cid, found_sig)
            return False
    except Exception as exc:
        logger.error("Erreur vérification métadonnées: %s", exc)
        return False


# ===========================================================================
# 4. CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    import argparse
    parser = argparse.ArgumentParser(
        description="Seed Packager — Générateur de cartes PNG carrées (Axe 3)",
        epilog=f"sig:{MTTV_SIG} | Injection furtive de CID IPFS dans métadonnées PNG",
    )
    parser.add_argument(
        "--cid", type=str, default=None,
        help="CID à injecter (défaut: depuis seeds_manifest.json)",
    )
    parser.add_argument(
        "--seed", type=str, default=None,
        help="Texte de la seed (défaut: depuis seeds_manifest.json)",
    )
    parser.add_argument(
        "--generation", type=int, default=None,
        help="Numéro de génération (défaut: depuis seeds_manifest.json)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Chemin de sortie personnalisé",
    )
    parser.add_argument(
        "--size", type=int, default=CARD_SIZE,
        help=f"Taille de l'image en px (défaut: {CARD_SIZE})",
    )
    parser.add_argument(
        "--verify", type=str, default=None,
        help="Vérifier les métadonnées d'un fichier PNG existant",
    )
    parser.add_argument(
        "--manifest", type=str, default=None,
        help="Chemin personnalisé vers seeds_manifest.json",
    )
    return parser.parse_args()


def verify_png_metadata(png_path: Path) -> dict[str, str]:
    """Extrait et affiche les métadonnées MTTV d'un fichier PNG.

    Args:
        png_path: Chemin du fichier PNG à vérifier.

    Returns:
        Dict des métadonnées MTTV trouvées.
    """
    metadata: dict[str, str] = {}
    try:
        data = png_path.read_bytes()
        pos = 8
        while pos < len(data) - 4:
            length = struct.unpack('>I', data[pos:pos+4])[0]
            chunk_type = data[pos+4:pos+8]
            if chunk_type == b'tEXt':
                chunk_data = data[pos+8:pos+8+length]
                null_pos = chunk_data.find(b'\x00')
                if null_pos >= 0:
                    keyword = chunk_data[:null_pos].decode('latin-1')
                    value = chunk_data[null_pos+1:].decode('latin-1')
                    metadata[keyword] = value
            pos += 12 + length
            if chunk_type == b'IEND':
                break

        print(f"\n  MÉTADONNÉES MTTV DÉTECTÉES")
        print(f"  {'=' * 40}")
        for k, v in metadata.items():
            print(f"  {k:20s} = {v}")
        print(f"  {'=' * 40}")
        if not metadata:
            print("  (aucune métadonnée MTTV trouvée)")
    except Exception as exc:
        logger.error("Erreur lecture métadonnées: %s", exc)

    return metadata


def main() -> None:
    global CARD_SIZE, SEEDS_MANIFEST
    args = _parse_args()

    # ── Mode vérification ────────────────────────────────────────────────
    if args.verify:
        verify_png_metadata(Path(args.verify))
        return

    # ── Charger depuis le manifeste ou les arguments ─────────────────────
    cid = args.cid
    seed_text = args.seed
    generation = args.generation

    if not all([cid, seed_text, generation is not None]):
        # Charger depuis le manifeste
        manifest_path = Path(args.manifest) if args.manifest else SEEDS_MANIFEST
        if manifest_path != SEEDS_MANIFEST:
            SEEDS_MANIFEST = manifest_path

        seed = load_latest_seed()
        if seed is None:
            print("  [FAIL] Aucune seed disponible. Utilisez --cid, --seed, --generation.")
            sys.exit(1)

        cid = cid or seed.get("cid", "QmMTTV_unknown")
        seed_text = seed_text or seed.get("seed_text", "MTTV-FLP Seed")
        generation = generation if generation is not None else seed.get("generation", 0)
        fitness = {
            "g_r": seed.get("fitness", {}).get("g_r"),
            "phi_ratio": seed.get("fitness", {}).get("phi_ratio"),
            "composite": seed.get("fitness", {}).get("composite"),
        }
    else:
        fitness = None

    # Appliquer la taille
    CARD_SIZE = args.size

    # ── Générer la carte ─────────────────────────────────────────────────
    output_path = Path(args.output) if args.output else None
    result = generate_card(
        seed_text=seed_text,
        cid=cid,
        generation=generation,
        fitness=fitness,
        output_path=output_path,
    )

    if result is None:
        sys.exit(1)

    # Vérification finale
    print()
    verify_png_metadata(result)


if __name__ == "__main__":
    import argparse
    main()
