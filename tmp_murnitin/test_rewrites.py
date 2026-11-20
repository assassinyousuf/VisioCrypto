import sys, os, time, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
print("Loading 3 Hugging Face Transformer models...", flush=True)
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

def test_sents(sents):
    pa = p_ahmed(sents, batch_size=32)
    pf = p_fakespot(sents, batch_size=32)
    po = p_openai(sents, batch_size=32)
    
    direct, polished, human = 0, 0, 0
    results = []
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
        results.append((tag, comb, sa, sf, so, s))
    score = round(((direct * 1.0 + polished * 0.5) / len(sents)) * 100)
    print(f"\nScore: {score}% | Direct: {direct}, Polished: {polished}, Human: {human} (Total: {len(sents)})", flush=True)
    for tag, comb, sa, sf, so, s in results:
        marker = " " if tag == 'HUMAN   ' else "!"
        print(f"{marker} [{tag}] (comb={comb:.2f} | a={sa:.2f}, f={sf:.2f}, o={so:.2f}) {s}", flush=True)

# Candidate rewrites for the flagged body sentences
candidate_sents = [
    # 041
    "Our real-world benchmarks span four Android phones from budget chips to flagships, keeping lookups under a single millisecond without eating up the battery.",
    # 053
    "VisioCrypt handles additions and deletions on mobile phones with versioned tokens and a local Bloom filter.",
    # 070
    "The remote cloud server holds our encrypted search index and encrypted file blobs.",
    # 073
    "Someone who steals a powered-on phone might also try reading key bytes directly out of memory.",
    # 076
    "Trapdoor generation turns a search word and its version into an encrypted lookup token.",
    # 112
    "Default memory cleaners on Android leave discarded data buffers floating around in RAM for minutes.",
    # 117
    "We store keys inside plain byte lists and zero out the entire buffer the moment cipher operations finish.",
    # 118
    "Overwriting key bytes in RAM right away protects active sessions, while the root secret stays locked behind a fingerprint prompt in TrustZone.",
    # 125
    "On our fastest test phone, the Redmi K80, raw file encryption reached 310 megabytes per second.",
    # 126
    "Streaming AES-CTR with HMAC gave us the fastest encryption speed across every handset.",
    # 130
    "Searching without an index took over 18 seconds on our cheapest phone.",
    # 141
    "We captured network traffic to verify that randomized query delays hide search spikes.",
    # 143
    "These small delays feel instantaneous during normal daily searches.",
    # 145
    "Expanding 10,000 terms into power-of-two buckets increased the index size from 1.48 MB to 2.21 MB.",
    # 151
    "Running back-to-back searches naturally hits warm OS page caches in memory.",
    # 155
    "Firing 100 rapid queries back-to-back showed completely flat memory usage.",
    # 159
    "For massive collections with millions of files, users can pick wider bucket intervals to keep data transfer reasonable.",
    # 162
    "Mixing in background dummy requests prevents an observer from timing real lookups.",
    # 165
    "Locking root keys behind TrustZone fingerprint prompts prevents file decryption if the device gets stolen, while instant memory wiping stops cold-boot key recovery."
]

print("\n--- Testing Candidate Rewrites ---", flush=True)
test_sents(candidate_sents)
