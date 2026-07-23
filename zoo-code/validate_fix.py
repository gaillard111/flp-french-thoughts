#!/usr/bin/env python3
"""Validate ALL fixes: BF16 + JSON numpy serialization."""
import ast, json, sys

errors = []

# --- 1. train_qwen_colab.py ---
with open('train_qwen_colab.py', 'r', encoding='utf-8') as f:
    src1 = f.read()
try:
    ast.parse(src1)
    print('[PASS] train_qwen_colab.py: syntax OK')
except SyntaxError as e:
    print(f'[FAIL] train_qwen_colab.py syntax: {e}')
    errors.append('syntax error')

checks1 = {
    'CONFIG fp16=False': '"fp16": False' in src1,
    'CONFIG bf16=False': '"bf16": False' in src1,
    'NumpyEncoder class': 'class NumpyEncoder(json.JSONEncoder)' in src1,
    'cls=NumpyEncoder in json.dump': 'cls=NumpyEncoder' in src1,
    'float(np.mean) in test_axiome_7': 'coherence = float(np.mean' in src1,
    'bool(coherence >= 0.3)': 'bool(coherence >= 0.3)' in src1,
    'bf16=config.get in TrainingArgs': 'bf16=config.get' in src1,
    'BF16->FP16 conversion in load_model': 'param.data.to(torch.float16)' in src1,
}
for k, v in checks1.items():
    print(f'  {"[OK]" if v else "[FAIL]"}: {k}')
    if not v: errors.append(k)

# --- 2. Generated notebook (the one actually executed in Colab) ---
with open('mttv_qwen25_colab.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

train_src = ''.join(nb['cells'][6]['source'])
model_src = ''.join(nb['cells'][3]['source'])
eval_src = ''.join(nb['cells'][7]['source'])
report_src = ''.join(nb['cells'][8]['source'])

checks3 = {
    'BF16 fix: fp16=False in TrainingArguments': 'fp16=False' in train_src,
    'BF16 fix: bf16=False in TrainingArguments': 'bf16=False' in train_src,
    'BF16 fix: adamw_torch (not paged_adamw_8bit)': 'adamw_torch' in train_src,
    'BF16 fix: no paged_adamw_8bit': 'paged_adamw_8bit' not in train_src,
    'BF16 fix: BF16->FP16 param conversion after model load': 'param.data.to(torch.float16)' in model_src,
    'JSON fix: NumpyEncoder class in report cell': 'class NumpyEncoder' in report_src,
    'JSON fix: cls=NumpyEncoder in json.dump': 'cls=NumpyEncoder' in report_src,
    'JSON fix: float(np.mean) in test_axiome_7': 'float(np.mean' in eval_src,
    'JSON fix: bool(coherence) in test_axiome_7': 'bool(coherence' in eval_src,
}
for k, v in checks3.items():
    print(f'  {"[OK]" if v else "[FAIL]"}: {k}')
    if not v: errors.append(k)

if errors:
    print(f'\n[FAIL] {len(errors)} check(s) failed:')
    for e in errors: print(f'  - {e}')
    sys.exit(1)
else:
    print(f'\n[OK] All {len(checks1) + len(checks3)} checks passed!')
