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

glued_tests = [
    "Introduction. We store everything from family photos to bank statements on our phones.",
    "Related Work. We compare our approach against related searchable encryption systems in Table I.",
    "System Architecture. Our setup connects a phone to an untrusted storage server.",
    "Threat Model. We assume the cloud server is honest but curious.",
    "Security Analysis. We analyze our cipher against an adaptive adversary through a sequence of games.",
    "Empirical Evaluation. We evaluated VisioCrypt across four commercial Android smartphone tiers.",
    "Hardware Testbed. We measured encryption throughput and battery draw across our four test phones.",
    "Discussion. We send a little extra data to protect search privacy.",
    "Conclusion. VisioCrypt gives smartphone users private encrypted search without leaking query match counts."
]

pa = p_ahmed(glued_tests, batch_size=32)
pf = p_fakespot(glued_tests, batch_size=32)
po = p_openai(glued_tests, batch_size=32)

for s, a, f, o in zip(glued_tests, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
