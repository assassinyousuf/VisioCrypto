import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

# Compare the glued vs unglued sentences
test_pairs = [
    (
        "DISCUSSION AND PRACTICAL DEPLOYMENT Padding candidate lists trades a small amount of extra bandwidth for solid query privacy.",
        "Padding candidate lists trades a small amount of extra bandwidth for solid query privacy."
    ),
    (
        "CONCLUSION VisioCrypt lets mobile users search encrypted cloud backups without leaking query volumes.",
        "VisioCrypt lets mobile users search encrypted cloud backups without leaking query volumes."
    ),
    (
        "Storage Inflation and Energy Consumption Table V tracks file inflation and power use across different dataset sizes.",
        "Table V tracks file inflation and power use across different dataset sizes."
    ),
    (
        "Multi-Device Search Query Latency Looking up words took 0.23 ms on the K80 and 1.48 ms on the Galaxy A14 for 10,000 keywords.",
        "Looking up words took 0.23 ms on the K80 and 1.48 ms on the Galaxy A14 for 10,000 keywords."
    ),
    (
        "Dynamic Updates and Bloom Filter Scalability Our in-memory filter verified over 22,000 keyword tags each millisecond on the K80.",
        "Our in-memory filter verified over 22,000 keyword tags each millisecond on the K80."
    )
]

for glued, unglued in test_pairs:
    print(f"\n--- Comparing: ---")
    for s, label in [(glued, "GLUED  "), (unglued, "UNGLUED")]:
        pa = p_ahmed([s])[0]
        pf = p_fakespot([s])[0]
        po = p_openai([s])[0]
        sa = pa['score'] if pa['label'] == 'AI' else (1.0 - pa['score'])
        sf = pf['score'] if pf['label'] == 'AI' else (1.0 - pf['score'])
        so = po['score'] if po['label'] == 'Fake' else (1.0 - po['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        tag = 'HUMAN   ' if comb <= 0.30 else ('POLISHED' if comb <= 0.60 else 'DIRECT  ')
        print(f"  [{label}] [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
