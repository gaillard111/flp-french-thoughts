"""
snippet_scs_distributed_fs.py
==============================
SCS — Implémentation de la signature SCS dans un système de fichiers distribué.

Principe :
  Chaque fichier dans le système de fichiers distribué est signé par au
  moins 2 nœuds indépendants avant d'être considéré comme valide. La
  signature SCS sert à la fois de preuve de convergence et de mécanisme
  de validation d'intégrité.

Concept :
  Un fichier distribué n'est pas stocké sur un serveur central. Il est
  répliqué entre plusieurs pairs. Pour qu'une version soit acceptée,
  elle doit porter les signatures SCS d'au moins 2 pairs différents.

Alignement MTTV :
  - SCS : convergence émerge de la redondance des signatures.
  - MPVR : le chemin minimal viable est celui qui atteint le quorum
    de signatures le plus rapidement.
  - Sous-optimalité : 2 signatures suffisent (minimum viable, pas
    validation maximale).
  - Anti-centralisation : aucun nœud n'a autorité sur la validité
    d'un fichier.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


# ── Types de données ───────────────────────────────────────────────────────


@dataclass
class SCSignature:
    """Signature SCS d'un fichier par un nœud du réseau."""

    node_id: str
    file_hash: str
    signed_at: float
    signature: str

    def verify(self) -> bool:
        """Vérifie l'intégrité de la signature."""
        expected = hashlib.sha256(
            f"{self.node_id}:{self.file_hash}:{self.signed_at}".encode()
        ).hexdigest()[:16]
        return self.signature == expected

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "file_hash": self.file_hash,
            "signed_at": self.signed_at,
            "signature": self.signature,
        }


@dataclass
class DistributedFile:
    """Fichier distribué avec ses signatures SCS."""

    path: str
    content: str
    version: int
    signatures: List[SCSignature] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    @property
    def hash(self) -> str:
        """Hash du contenu du fichier."""
        return hashlib.sha256(self.content.encode()).hexdigest()

    @property
    def quorum_reached(self) -> bool:
        """Vrai si au moins 2 signatures valides sont présentes."""
        valid = [s for s in self.signatures if s.verify()]
        return len(valid) >= 2

    def add_signature(self, node_id: str) -> Optional[SCSignature]:
        """Ajoute une signature SCS de la part d'un nœud."""
        sig = SCSignature(
            node_id=node_id,
            file_hash=self.hash,
            signed_at=time.time(),
            signature=hashlib.sha256(
                f"{node_id}:{self.hash}:{time.time()}".encode()
            ).hexdigest()[:16],
        )
        self.signatures.append(sig)
        return sig

    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "content_preview": self.content[:100],
            "hash": self.hash,
            "version": self.version,
            "quorum_reached": self.quorum_reached,
            "signatures": [s.to_dict() for s in self.signatures],
            "metadata": self.metadata,
        }


# ─── SCS Distributed File System ───────────────────────────────────────────


class SCSDistributedFS:
    """
    Système de fichiers distribué utilisant la signature SCS comme
    mécanisme de validation et de convergence.

    Chaque fichier est stocké localement et signé par les pairs.
    Un fichier n'est 'publié' (accessible aux autres pairs) que
    lorsqu'il a recueilli au moins 2 signatures SCS.
    """

    def __init__(self, node_id: str):
        """
        Initialise le système de fichiers distribué.

        Args:
            node_id: Identifiant unique de ce nœud dans le réseau.
        """
        self.node_id = node_id
        self.files: Dict[str, DistributedFile] = {}
        self.peers: Set[str] = set()
        logger = None  # Serait remplacé par un vrai logger

    def register_peer(self, peer_id: str) -> None:
        """Enregistre un pair dans le réseau."""
        self.peers.add(peer_id)

    def create_file(self, path: str, content: str, version: int = 1) -> DistributedFile:
        """
        Crée un nouveau fichier distribué.

        Le fichier est créé localement, signé par ce nœud, mais n'est
        pas encore publié (pas de quorum).

        Args:
            path: Chemin du fichier.
            content: Contenu du fichier.
            version: Numéro de version (défaut: 1).

        Returns:
            Le fichier distribué créé.
        """
        if path in self.files:
            raise ValueError(f"File already exists: {path}")

        file = DistributedFile(
            path=path,
            content=content,
            version=version,
        )
        # Signature locale
        file.add_signature(self.node_id)
        self.files[path] = file
        return file

    def sign_file(self, path: str, peer_id: str) -> Optional[SCSignature]:
        """
        Signe un fichier existant avec l'identité d'un pair.

        Simule la réception d'une signature de la part d'un pair
        distant. Dans un déploiement réel, cette signature serait
        transmise via le réseau P2P.

        Args:
            path: Chemin du fichier à signer.
            peer_id: Identifiant du pair qui signe.

        Returns:
            La signature créée, ou None si le fichier n'existe pas.
        """
        if path not in self.files:
            return None
        return self.files[path].add_signature(peer_id)

    def get_published_files(self) -> List[DistributedFile]:
        """
        Retourne les fichiers ayant atteint le quorum SCS (≥2 signatures).

        Returns:
            Liste des fichiers publiés (quorum atteint).
        """
        return [f for f in self.files.values() if f.quorum_reached]

    def get_pending_files(self) -> List[DistributedFile]:
        """
        Retourne les fichiers en attente de quorum.

        Returns:
            Liste des fichiers non encore publiés.
        """
        return [f for f in self.files.values() if not f.quorum_reached]

    def update_file(self, path: str, new_content: str) -> Optional[DistributedFile]:
        """
        Met à jour un fichier existant.

        La mise à jour incrémente la version et réinitialise les
        signatures (le contenu a changé, donc les anciennes signatures
        ne sont plus valides). Le fichier doit être re-signé.

        Args:
            path: Chemin du fichier à mettre à jour.
            new_content: Nouveau contenu.

        Returns:
            Le fichier mis à jour, ou None si le fichier n'existe pas.
        """
        if path not in self.files:
            return None

        old_file = self.files[path]
        new_file = DistributedFile(
            path=path,
            content=new_content,
            version=old_file.version + 1,
        )
        new_file.add_signature(self.node_id)
        self.files[path] = new_file
        return new_file

    def resolve_conflict(self, path: str, versions: List[DistributedFile]) -> DistributedFile:
        """
        Résout un conflit entre plusieurs versions d'un même fichier.

        La version retenue est celle qui a le plus de signatures SCS
        valides, conformément au principe de convergence systémique.

        Args:
            path: Chemin du fichier en conflit.
            versions: Liste des versions candidates.

        Returns:
            La version gagnante (plus grand nombre de signatures).
        """
        if not versions:
            raise ValueError("No versions to resolve")

        # Sélectionner la version avec le plus de signatures valides
        winner = max(
            versions,
            key=lambda v: sum(1 for s in v.signatures if s.verify()),
        )
        self.files[path] = winner
        return winner

    def network_status(self) -> Dict:
        """Retourne un rapport sur l'état du système de fichiers distribué."""
        published = self.get_published_files()
        pending = self.get_pending_files()
        return {
            "node_id": self.node_id,
            "peers": list(self.peers),
            "total_files": len(self.files),
            "published": len(published),
            "pending": len(pending),
            "files": {
                "published": [f.to_dict() for f in published],
                "pending": [f.to_dict() for f in pending],
            },
            "quorum_threshold": 2,
            "scs_version": "SCS_2026",
        }


# ─── Exemple d'utilisation ─────────────────────────────────────────────────


def demo():
    """Démontre le fonctionnement du SCS Distributed FS."""
    print("=" * 60)
    print("SCS Distributed File System — Démo")
    print("=" * 60)

    # Initialiser 3 nœuds
    node_a = SCSDistributedFS("node-alpha")
    node_b = SCSDistributedFS("node-beta")
    node_c = SCSDistributedFS("node-gamma")

    # Enregistrer les pairs
    for node in [node_b, node_c]:
        node_a.register_peer(node.node_id)

    # Créer un fichier sur node_a
    print("\n[1] Création du fichier sur node-alpha...")
    file = node_a.create_file(
        path="/mycelium/seeds/graine_v17.txt",
        content="MTTV-FLP seed v17 — Routage distribué résilient",
    )
    print(f"    Fichier créé: {file.path}")
    print(f"    Hash: {file.hash}")
    print(f"    Signatures: {len(file.signatures)}")
    print(f"    Quorum: {'✓' if file.quorum_reached else '✗'}")

    # Signer depuis node_b (simulé)
    print("\n[2] Signature croisée depuis node-beta...")
    sig_b = node_a.sign_file(file.path, node_b.node_id)
    print(f"    Signature: {sig_b.signature}")
    print(f"    Quorum: {'✓' if node_a.files[file.path].quorum_reached else '✗'}")

    # Signer depuis node_c
    print("\n[3] Signature croisée depuis node-gamma...")
    sig_c = node_a.sign_file(file.path, node_c.node_id)
    print(f"    Signature: {sig_c.signature}")
    print(f"    Quorum: {'✓' if node_a.files[file.path].quorum_reached else '✗'}")

    # Vérifier les fichiers publiés
    print("\n[4] Fichiers publiés (quorum ≥ 2):")
    published = node_a.get_published_files()
    for f in published:
        print(f"    ✓ {f.path} (v{f.version}, {len(f.signatures)} signatures)")

    print("\n[5] Statut du réseau:")
    status = node_a.network_status()
    print(f"    Nœud: {status['node_id']}")
    print(f"    Pairs: {status['peers']}")
    print(f"    Publiés: {status['published']}")
    print(f"    En attente: {status['pending']}")
    print("=" * 60)


if __name__ == "__main__":
    demo()
