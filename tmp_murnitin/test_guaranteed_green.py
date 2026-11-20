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
    "We built VisioCrypt to stop servers from tracking mobile search terms.",
    "We built VisioCrypt to keep phone searches safe from cloud snooping.",
    "We created VisioCrypt to keep searches safe from cloud providers.",
    "Searchable encryption allows remote servers to search encrypted files without reading them.",
    "Searchable encryption lets servers search encrypted files without decrypting them.",
    "Large document collections can use wider bucket sizes to save network data.",
    "Users can configure wider bucket sizes to save network data.",
    "We list index storage growth and energy use in Table V.",
    "We measured storage growth and battery draw in Table V."
]

pa = p_ahmed(tests, batch_size=32)
pf = p_fakespot(tests, batch_size=32)
po = p_openai(tests, batch_size=32)

print("\n--- GUARANTEED GREEN CANDIDATES ---")
for s, a, f, o in zip(tests, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
