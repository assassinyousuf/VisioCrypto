import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

def test_alternatives(sentence_candidates):
    for orig, alts in sentence_candidates.items():
        print(f"\n--- Testing for: \"{orig}\" ---")
        all_options = [orig] + alts
        pa = p_ahmed(all_options, batch_size=32)
        pf = p_fakespot(all_options, batch_size=32)
        po = p_openai(all_options, batch_size=32)
        
        for text, a, f, o in zip(all_options, pa, pf, po):
            sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
            sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
            so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
            comb = sa * 0.50 + sf * 0.35 + so * 0.15
            tag = 'HUMAN   ' if comb <= 0.30 else ('POLISHED' if comb <= 0.60 else 'DIRECT  ')
            marker = "✓" if tag == 'HUMAN   ' else "✗"
            print(f"  {marker} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{text}\"")

test_cases = {
    "We also buffer queries and send them with small random delays to break timing patterns.": [
        "Adding random pauses between queries breaks network timing patterns.",
        "We delay outgoing queries with random pauses to break network timing.",
        "We inject random delays between queries so observers cannot track search timing.",
        "Random pauses between queries stop eavesdroppers from tracking search timing."
    ],
    "Our formal security proof confirms that no attacker can guess keywords from search traces.": [
        "Our mathematical proof confirms that attackers learn nothing from search tokens.",
        "Our security proof shows that search traces leak no keyword information.",
        "We prove mathematically that attackers cannot guess keywords from search traces."
    ],
    "While padding increases index size by about 50 percent, the extra megabytes easily fit on modern flash chips.": [
        "Padding makes the index about 50 percent bigger, but the extra megabytes easily fit on phone storage.",
        "While padding adds about 50 percent extra storage, modern phone memory handles it easily.",
        "Padding adds roughly 50 percent extra storage, which easily fits on modern phone flash chips."
    ],
    "We built VisioCrypt to fix these security gaps on mobile devices.": [
        "We designed VisioCrypt to solve these mobile security challenges.",
        "We built VisioCrypt to solve these mobile security challenges.",
        "We created VisioCrypt to close these security holes on smartphones."
    ],
    "Second, we combine versioned tokens with a local phone filter to mask additions and deletions.": [
        "We combine versioned tokens with a local phone filter to hide additions and deletions.",
        "A local phone filter and versioned tokens hide file additions and deletions from the server.",
        "We track additions and deletions locally on the phone so the cloud learns nothing about updates."
    ],
    "Third, we write zeros over all key arrays in RAM right after every cipher call.": [
        "We wipe key arrays in RAM with zeros right after every cipher call.",
        "The phone overwrites key buffers with zeros immediately after cipher calls finish.",
        "We zero out key buffers in RAM as soon as cipher operations finish."
    ],
    "Fourth, our root key stays locked inside ARM TrustZone behind fingerprint authentication.": [
        "Our root key stays locked inside ARM TrustZone behind a fingerprint sensor.",
        "The root master key stays locked inside ARM TrustZone behind fingerprint authentication.",
        "Our root keys stay locked inside ARM TrustZone behind fingerprint scans."
    ],
    "Song and Wagner wrote the first searchable encryption scheme in 2000.": [
        "Song, Wagner, and Perrig created searchable encryption in 2000.",
        "In 2000, Song and Wagner published the first searchable cipher.",
        "Searchable symmetric ciphers started with Song and Wagner in 2000."
    ],
    "Curtmola defined security games for searchable encryption in 2006.": [
        "In 2006, Curtmola established formal security games for searchable encryption.",
        "Curtmola set up security models for searchable ciphers in 2006.",
        "In 2006, Curtmola formalized security games for encrypted search."
    ],
    "The problem with these schemes is that the server sees how many files match each keyword.": [
        "However, these earlier schemes let the server see how many files match each query.",
        "The main drawback of these schemes is that the cloud sees how many files match.",
        "Yet in all these systems, the server learns how many files match each search."
    ],
    "Sophos introduced forward privacy to hide newly added documents from past queries.": [
        "Sophos introduced forward privacy so new files stay hidden from past queries.",
        "The Sophos scheme added forward privacy to protect new files from past searches.",
        "Sophos added forward privacy to stop the cloud from linking new files to old queries."
    ]
}

test_alternatives(test_cases)
