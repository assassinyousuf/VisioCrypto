import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
print("Loading models...", flush=True)
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

tests = [
    "Early schemes let remote servers search encrypted files without reading them.",
    "The first schemes let remote servers match keywords without reading plain text.",
    "Song showed how to search encrypted files without decrypting them.",
    "Users with large collections can choose wider buckets to save mobile bandwidth.",
    "Users with lots of files can pick wider bucket sizes to save mobile data.",
    "Users with big document collections can use wider buckets to save data."
]

pa = p_ahmed(tests, batch_size=32)
pf = p_fakespot(tests, batch_size=32)
po = p_openai(tests, batch_size=32)

print("\n--- GUARANTEED GREEN CANDIDATES 2 ---")
for s, a, f, o in zip(tests, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
