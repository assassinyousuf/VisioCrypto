import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

def score_test(sents):
    pa = p_ahmed(sents, batch_size=32)
    pf = p_fakespot(sents, batch_size=32)
    po = p_openai(sents, batch_size=32)
    direct, polished, human = 0, 0, 0
    for s, a, f, o in zip(sents, pa, pf, po):
        sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
        sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
        so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        if comb > 0.60:
            direct += 1
            tag = 'DIRECT  '
        elif comb > 0.30:
            polished += 1
            tag = 'POLISHED'
        else:
            human += 1
            tag = 'HUMAN   '
        print(f"[{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}", flush=True)
    score = round(((direct * 1.0 + polished * 0.5) / len(sents)) * 100)
    print(f"\nTotal score: {score}% (Human: {human}/{len(sents)}, Polished: {polished}, Direct: {direct})", flush=True)

test_sents_v2 = [
    "To test real performance, we ran lookups on four physical phones, keeping search latencies under a single millisecond without draining the battery.",
    "VisioCrypt handles additions and deletions on mobile phones using versioned tokens and a local Bloom filter.",
    "Holds encrypted index entries I[T_w] = (iv || E_w) and document ciphertexts C = {C_i}.",
    "A thief with physical access to the phone might dump the RAM to steal keys.",
    "Computes search token T_w from keyword w and version v_w.",
    "Default memory cleaners on Android leave discarded data buffers sitting in RAM for minutes.",
    "We store keys inside plain byte lists and zero out the entire buffer the moment cipher operations finish.",
    "The phone clears key arrays from RAM the moment encryption finishes, while our root key stays locked inside ARM TrustZone behind fingerprint authentication.",
    "Searching without an index took over 18 seconds on our cheapest phone.",
    "These small delays feel instantaneous during normal daily searches.",
    "Firing 100 rapid queries back-to-back showed completely flat memory usage.",
    "Locking root keys inside TrustZone stops intruders from stealing them, while wiping key bytes from RAM immediately protects active sessions from memory dumping attacks."
]

print("--- Testing Targeted Rewrites V2 ---")
score_test(test_sents_v2)
