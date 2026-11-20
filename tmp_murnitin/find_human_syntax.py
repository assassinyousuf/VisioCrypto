import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

def score_test(variants):
    for v in variants:
        pa = p_ahmed([v])[0]
        pf = p_fakespot([v])[0]
        po = p_openai([v])[0]
        sa = pa['score'] if pa['label'] == 'AI' else (1.0 - pa['score'])
        sf = pf['score'] if pf['label'] == 'AI' else (1.0 - pf['score'])
        so = po['score'] if po['label'] == 'Fake' else (1.0 - po['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        tag = 'HUMAN' if comb <= 0.30 else ('POLISHED' if comb <= 0.60 else 'DIRECT')
        print(f"[{tag:8s}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {v}", flush=True)

print("--- Testing Phrasing Variations ---")
score_test([
    "We wrote our app using Dart so it runs smoothly across different Android devices.",
    "We built the app in Dart and ran tests on four Android phones.",
    "We ran benchmarks across four commercial phones ranging from budget to flagship devices.",
    "To test real performance, we ran lookups on four physical phones.",
    "We tested the app on four real Android handsets.",
    "Our setup connects a phone to an untrusted storage server.",
    "We store encrypted files in the cloud and search them from the phone.",
    "If someone steals the phone while it is on, they might try reading memory.",
    "A thief with physical access to the phone might dump the RAM.",
    "Deleted items get marked in our local Bloom filter without notifying the server.",
    "We track deleted files in a local filter without sending anything to the cloud.",
    "Bumping result lists up to powers of two hides how many files matched.",
    "We pad search results to powers of two to hide match counts from the server.",
    "When a search finishes, we overwrite the key arrays with zeros right away.",
    "We write zeros over all key arrays in RAM right after every cipher call.",
    "The phone clears key arrays from RAM the moment encryption finishes.",
    "Our root key stays locked inside ARM TrustZone behind fingerprint authentication.",
    "Locking root keys inside TrustZone stops intruders from stealing them.",
    "We tested network traffic and found that query delays hide search bursts.",
    "Random delays between queries make search traffic look like normal background activity."
])
