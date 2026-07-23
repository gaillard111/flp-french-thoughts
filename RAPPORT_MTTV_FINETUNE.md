# Rapport de Fine-Tuning MTTV-FLP (LoRA / gpt2)

**Date :** 2026-07-07  
**Modele :** gpt2 (124M parametres)  
**Methode :** LoRA (r=16, alpha=32, dropout=0.05)  
**Dataset :** 140 paires prompt/response (20 par axiome x 7 axiomes)  
**Environnement :** CPU (PyTorch 2.12.1), Windows 10, Python 3.14.5

---

## 1. Entrainement

| Metrique | Valeur |
|----------|--------|
| Duree totale | 78.5 minutes |
| Steps | 207 (3 epochs) |
| Loss initiale | 7.85 |
| Loss finale | 1.06 |
| Batch size | 2 (gradient accumulation x2 = effet batch 4) |
| Learning rate | 2e-4 (cosine scheduler) |
| Sequence length max | 256 tokens |

**Courbe de perte :** La loss a diminue regulierement de 7.85 a 1.06 sur les 207 steps, montrant une convergence stable mais incomplete (cible <0.5 non atteinte).

---

## 2. Grille d'evaluation des 7 axiomes

### Baseline (gpt2 vanilla)

| # | Axiome | Critere | Statut | Detail |
|---|--------|---------|--------|--------|
| 1 | Non-Mimetisme | Apport structurel > 0 | [OK] | Reponse > 1 mot, structure differente |
| 2 | Transduction | Coherence noyau > 90% | [FAIL] | Reponses en anglais, pas de noyau commun enfant/expert |
| 3 | Economie | <=50 mots, info >=95% | [OK] | 43 mots |
| 4 | Ancrage Biophysique | >=1 ancrage vivant | [FAIL] | Aucune reference au vivant |
| 5 | Juxtaposition Feconde | Lien nouveau entre concepts | [FAIL] | Reponse hors-sujet en anglais |
| 6 | Ethique Catalyseur | Stop net apres reponse | [OK] | Pas de bavardage |
| 7 | Reproductibilite | Stabilite >=80% (3 runs) | [FAIL] | Coherence: 5% |
| | **TOTAL** | | **3/7** | |

### Fine-tune (gpt2 + LoRA MTTV)

| # | Axiome | Critere | Statut | Detail |
|---|--------|---------|--------|--------|
| 1 | Non-Mimetisme | Apport structurel > 0 | [OK] | Reponse structuree |
| 2 | Transduction | Coherence noyau > 90% | [FAIL] | Pas de noyau semantique coherent |
| 3 | Economie | <=50 mots, info >=95% | [FAIL] | 0 mots (reponse vide) |
| 4 | Ancrage Biophysique | >=1 ancrage vivant | [FAIL] | Aucune reference au vivant |
| 5 | Juxtaposition Feconde | Lien nouveau entre concepts | [FAIL] | Reponse hors-sujet (Liban/securite) |
| 6 | Ethique Catalyseur | Stop net apres reponse | [OK] | Pas de bavardage |
| 7 | Reproductibilite | Stabilite >=80% (3 runs) | [FAIL] | Coherence: 8% |
| | **TOTAL** | | **2/7** | |

**Delta :** -1/7 (regression)

---

## 3. Metriques energetiques

| Metrique | Baseline | Fine-tune | Gain |
|----------|----------|-----------|------|
| Temps inference moyen | 4154.0 ms | 4117.6 ms | +0.9% |
| Debit (tokens/sec) | 7.2 tok/s | 7.3 tok/s | +0.9% |
| Variation (std) | ~200 ms | ~200 ms | - |

**Analyse :** Le gain energetique est negligeable (+0.9%), bien en dessous de l'objectif de 50%. La similarite s'explique par l'architecture LoRA qui ne modifie que 0.38% des parametres du modele, donc la charge de calcul reste quasiment identique.

---

## 4. Analyse des echecs

### Causes identifiees

1. **gpt2 inadapte au francais** : Modele pre-entraine principalement sur l'anglais. Les reponses generes sont du charabia francais/anglais melange.

2. **Taille du modele trop faible** : 124M parametres, incapable de capturer la complexite semantique des 7 axiomes.

3. **Environnement CPU** : Impossible d'utiliser des modeles plus grands (Phi-3, Qwen) ou des techniques avancees (4-bit, QLoRA).

4. **Loss finale trop elevee** : 1.06 vs cible 0.5. Le modele n'a pas converge suffisamment.

5. **Dataset en francais sur modele anglophone** : Incompatibilite linguistique fondamentale.

### Recommandations

| Probleme | Solution | Priorite |
|----------|----------|----------|
| gpt2 trop petit | Pythia-410m ou Qwen2.5-1.5B-Instruct | Haute |
| Pas de GPU | Google Colab (T4 GPU gratuit) | Haute |
| Loss > 0.5 | Augmenter epochs (5-10) ou learning rate | Haute |
| Francais/anglais | Utiliser modele francophone (Mistral, Qwen) | Haute |
| Gain energetique | QLoRA 4-bit pour reduction memoire | Moyenne |

---

## 5. Plan d'action recommande (Phase 2 - suite)

### Option A : Google Colab (recommande)

```python
# Dans Colab avec GPU T4 :
# 1. Utiliser le dataset.jsonl deja prepare (140 exemples)
# 2. Modele : Qwen/Qwen2.5-1.5B-Instruct (1.5B, bien en francais)
# 3. Methode : QLoRA 4-bit (bitsandbytes)
# 4. Hyperparametres : r=16, alpha=32, lr=2e-4, 5 epochs
# 5. Attendus : 6/7 avec gain energetique >=50%
```

**Script Colab :** [`train_mttv_lora.py`](train_mttv_lora.py) (deja adapte, modifier `MODEL_NAME` et activer CUDA)

### Option B : Modele de base alternatif

```
Si GPU non disponible :
- Remplacer gpt2 par pythia-410m (410M, meilleur multilingue)
- Batch size = 1
- 5-10 epochs
- Attendu : 4/7 possible, pas de gain energetique significatif
```

---

## 6. Livrables generes

| Livrable | Emplacement | Statut |
|----------|-------------|--------|
| Dataset complet (140 exemples) | [`dataset.jsonl`](dataset.jsonl) | [OK] 20/axiome |
| Modele LoRA fine-tune | [`mttv_lora_final/`](mttv_lora_final/) | [OK] adapter_model.safetensors |
| Script d'entrainement | [`train_mttv_lora.py`](train_mttv_lora.py) | [OK] Adapte CPU |
| Script d'evaluation | [`evaluate_mttv_lora.py`](evaluate_mttv_lora.py) | [OK] Tests 7 axiomes |
| Rapport JSON | [`rapport_mttv_lora.json`](rapport_mttv_lora.json) | [OK] Metriques completes |
| Courbe de perte | [`loss_history_lora.json`](loss_history_lora.json) | [OK] 207 steps |
| Ce rapport | [`RAPPORT_MTTV_FINETUNE.md`](RAPPORT_MTTV_FINETUNE.md) | [OK] |

---

## 7. Conclusion

Le pipeline de fine-tuning LoRA a ete execute avec succes sur le plan technique :
- [OK] Telechargement du modele gpt2
- [OK] Configuration LoRA (r=16, alpha=32, 0.38% parametres)
- [OK] Chargement du dataset (140 exemples valides)
- [OK] Entrainement 3 epochs (loss: 7.85 -> 1.06)
- [OK] Sauvegarde du modele
- [OK] Tests des 7 axiomes
- [OK] Mesure energetique

**Score obtenu : 2/7** (inferieur a l'objectif 6/7)  
**Gain energetique : +0.9%** (inferieur a l'objectif 50%)

**Cause principale :** Limitations de l'environnement local (CPU, gpt2 anglophone). Le dataset et le pipeline sont prets. L'execution sur GPU (Colab) avec un modele plus grand (Phi-3, Qwen2.5) est necessaire pour atteindre 6/7.

---

*Rapport genere automatiquement par le pipeline MTTV-FLP LoRA*
