# Hugging Face Dataset Deployment Instructions — SOPH-IA Ethical Friction Teaser

## Repo Name (choose one)
- `SOPH-IA-ethical-friction-teaser` (recommended — explicit)
- `soph-ia-teaser` (shorter alternative)

## Steps

### 1. Create the Dataset Repository
1. Go to https://huggingface.co/new-dataset
2. **Owner:** Your HF username or organization
3. **Dataset name:** `SOPH-IA-ethical-friction-teaser`
4. **License:** cc-by-4.0
5. **Tags:** AI Safety, Green AI, Thermodynamic Friction, Satisficing Alignment, Habitability 6/7, Frugal AI
6. **Do NOT enable** Inference widget

### 2. Upload Files
Upload to the `/data` directory of the repository:
- `SOPH-IA_teaser.pdf`
- `benchmark_T4_teaser.csv`

### 3. Set the README
Use `README.md` from this deployment package.
**IMPORTANT:** After obtaining the Zenodo DOI (from TASK 1), replace the placeholder in `README.md`:
```
(DOI via Zenodo, coming)
```
→ replace with the actual DOI URL, e.g.:
```
10.5281/zenodo.XXXXXXX
```

### 4. Verify tags on HF
Ensure these tags are attached:
- `AI Safety`
- `Green AI`
- `Thermodynamic Friction`
- `Satisficing Alignment`
- `Habitability 6/7`
- `Frugal AI`

### 5. Final Check
- [ ] README.md is the main repo card
- [ ] License set to cc-by-4.0
- [ ] Both files present in /data
- [ ] Inference widget is OFF
- [ ] DOI placeholder replaced with real Zenodo DOI
