import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

def test_sents(sents):
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
        print(f"[{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
    score = round(((direct * 1.0 + polished * 0.5) / len(sents)) * 100)
    print(f"\nScore: {score}% | Human: {human}/{len(sents)}, Polished: {polished}, Direct: {direct}")

test_batch3 = [
    "A searchable encryption scheme consists of six basic operations.",
    "Key generation creates master secrets inside the phone hardware enclave.",
    "Building the index produces an encrypted lookup table and a local deletion filter.",
    "Trapdoor calculation turns a keyword and version counter into an encrypted lookup token.",
    "Search finds the encrypted bucket on the cloud server.",
    "Updates append encrypted delta records while updating local filter state.",
    "Decryption turns downloaded ciphertexts back into plain documents on the phone.",
    "To stop match count leakage, the phone pads candidate lists to powers of two.",
    "We add dummy entries so every result list has four, eight, sixteen, or thirty-two items.",
    "Rare words stay hidden because list sizes look identical across terms.",
    "Our Bloom filter parameters keep false positive rates below one in ten thousand.",
    "Discarded key bytes can sit in physical RAM for minutes before getting reclaimed.",
    "The phone clears key arrays from RAM the moment encryption finishes, while our root key stays locked inside ARM TrustZone behind a fingerprint sensor.",
    "We tested the app on four physical Android phones from entry-level hardware to flagships.",
    "Searching without an index took 18 seconds on our cheapest phone.",
    "Our in-memory filter verified over twenty-two thousand keyword tags each millisecond on the K80.",
    "We captured network traffic to verify that randomized query delays hide search spikes.",
    "Adding small pauses between 10 and 50 milliseconds smooths out bursty traffic.",
    "These small delays feel instantaneous during normal daily searches.",
    "Expanding 10,000 terms into power-of-two buckets increased the index size from 1.48 MB to 2.21 MB.",
    "An index of ten thousand keywords takes 2.2 megabytes, easily fitting on phone storage.",
    "On our budget test phone, 1,000 full searches use roughly 1.85 millijoules of power.",
    "A typical phone battery hardly registers this draw even after weeks of constant searching.",
    "Running back-to-back searches naturally hits warm OS page caches in memory.",
    "To measure worst-case lookups, we flushed OS page caches before each test run.",
    "Cold lookups added under 0.12 milliseconds of extra delay across all four phones.",
    "Firing 100 rapid queries back-to-back showed completely flat memory usage.",
    "Padding candidate lists trades a small amount of extra bandwidth for strong query privacy.",
    "Using power-of-two buckets conceals match counts while adding roughly fifty percent extra data.",
    "For massive collections with millions of files, users can pick wider bucket intervals to keep data transfer reasonable.",
    "Because VisioCrypt runs purely on the client, standard cloud backends like Google Drive, S3, or private servers work without changes.",
    "Mixing in background dummy requests prevents an observer from timing real lookups.",
    "Locking root keys inside TrustZone stops intruders from stealing them, while wiping key bytes from RAM immediately protects active sessions from memory dumping attacks."
]

test_sents(test_batch3)
