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

candidate_sets = {
    "rel_song": [
        "Song and his team introduced searchable ciphers back in 2000.",
        "Searchable symmetric ciphers started with Song and his colleagues in 2000.",
        "In 2000, Song pioneered searchable symmetric encryption.",
        "Song first introduced searchable encryption in 2000."
    ],
    "rel_curtmola": [
        "Curtmola later defined standard security games for searchable schemes in 2006.",
        "In 2006, Curtmola formalized security models for searchable encryption.",
        "Curtmola introduced formal security games for encrypted search in 2006.",
        "In 2006, Curtmola built formal security definitions for encrypted search."
    ],
    "rel_dynamic": [
        "Later systems let people insert files without re-indexing the whole library.",
        "Dynamic ciphers later allowed file updates without rebuilding full indexes.",
        "Newer schemes allowed file additions without rebuilding the entire index.",
        "Dynamic schemes let users add files without having to re-encrypt everything."
    ],
    "rel_cash": [
        "Cash scaled encrypted search to handle large boolean queries.",
        "Cash made encrypted search scalable for complex boolean lookups.",
        "Cash designed algorithms to handle large boolean search queries.",
        "Cash improved search performance on large boolean queries."
    ],
    "rel_leakage": [
        "In all these schemes, cloud servers still see how many files match each query.",
        "Even with encrypted indexes, servers learn the exact number of matching files.",
        "In earlier schemes, the cloud server sees how many files match each search.",
        "Existing schemes still disclose match counts to cloud servers."
    ],
    "rel_patel": [
        "Patel padded query outputs into bins to reduce volume leakage.",
        "Patel grouped search outputs into bins to hide match numbers.",
        "Patel used fixed bin sizes to hide match counts from servers.",
        "Patel clustered search outputs into fixed bins to cut down volume leakage."
    ],
    "rel_dvh_ours": [
        "We pad result lists to powers of two on the phone without requiring cloud hardware enclaves.",
        "Our scheme rounds search lists to powers of two on the phone without needing cloud enclaves.",
        "We pad candidate lists to powers of two directly on mobile phones.",
        "Our system pads search results to powers of two directly on the client handset."
    ],
    "rel_forward": [
        "Sophos introduced forward privacy so newer files remain hidden from older queries.",
        "Sophos added forward privacy to keep newly added files hidden from older queries.",
        "Forward privacy, introduced by Sophos, prevents old searches from matching new files.",
        "Sophos introduced forward privacy to hide newly added files from past searches."
    ],
    "rel_visiocrypt_updates": [
        "Our app handles file updates on the phone using version numbers and a local filter.",
        "We manage file additions and deletions on the handset using version tags and a Bloom filter.",
        "VisioCrypt handles additions and deletions locally using version tags and a phone-side filter.",
        "We support dynamic additions and deletions on mobile devices using versioned tokens."
    ],
    "sec_arch_enum1": [
        "The phone stores the master secret inside ARM TrustZone and runs isolated workers for encryption and memory wiping.",
        "The mobile client holds the root secret in ARM TrustZone and runs background workers for crypto tasks.",
        "The client phone protects root secrets in ARM TrustZone and clears memory right after encryption.",
        "The phone keeps root secrets in ARM TrustZone and uses background workers to encrypt indexes."
    ],
    "sec_arch_enum2": [
        "The network layer delays search packets slightly so observers cannot trace timing patterns.",
        "The network layer adds random delays to query packets to mask traffic timing.",
        "Our network channel adds tiny random pauses to hide traffic timing.",
        "Network buffers add small random delays to hide query timing."
    ],
    "sec_arch_enum3": [
        "The cloud server stores encrypted index buckets and encrypted document files.",
        "The cloud server holds encrypted index tables and encrypted files.",
        "Cloud storage holds encrypted index entries and document ciphertexts.",
        "The remote server stores encrypted index entries and encrypted files."
    ],
    "eval_bench_suite": [
        "We tested raw file throughput, RAM key lifetimes, search latency, index sizes, and battery drain.",
        "We measured file encryption speed, RAM key retention, search delays, index file sizes, and battery use.",
        "Our test suite benchmarks file speed, memory lifetimes, search delay, index growth, and power use.",
        "We evaluated file encryption speeds, RAM key lifetimes, search delays, index sizes, and power draw."
    ],
    "eval_flush_caches": [
        "We flushed phone memory caches before each test to measure worst-case cold lookups.",
        "We cleared memory caches before each benchmark run to test cold lookup performance.",
        "Clearing OS memory caches before each run allowed us to measure worst-case cold lookups.",
        "We emptied memory caches before every test run to measure cold lookup delays."
    ]
}

all_sents = []
mapping = []
for key, sents in candidate_sets.items():
    for s in sents:
        all_sents.append(s)
        mapping.append(key)

print(f"Scoring {len(all_sents)} sentences across {len(candidate_sets)} sets...", flush=True)
pa = p_ahmed(all_sents, batch_size=32)
pf = p_fakespot(all_sents, batch_size=32)
po = p_openai(all_sents, batch_size=32)

best_per_key = {}
for s, key, a, f, o in zip(all_sents, mapping, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    if key not in best_per_key or comb < best_per_key[key][0]:
        best_per_key[key] = (comb, sa, sf, so, s)

print("\n--- BEST CANDIDATES SECTION II & III & VII ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
