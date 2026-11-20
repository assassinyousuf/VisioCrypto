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
    "rel_song_v3": [
        "Song developed the first searchable encryption scheme in 2000.",
        "Song and his co-workers first proposed searchable encryption in 2000.",
        "Song created the first searchable encryption scheme back in 2000.",
        "In 2000, Song introduced searchable encryption for remote data.",
        "Song and his colleagues published the first searchable encryption scheme in 2000."
    ],
    "rel_curtmola_v3": [
        "Curtmola gave searchable encryption its first formal security proof in 2006.",
        "In 2006, Curtmola gave searchable encryption its formal security foundation.",
        "Curtmola defined formal security definitions for encrypted search in 2006.",
        "Curtmola introduced formal security games for encrypted search in 2006.",
        "In 2006, Curtmola established rigorous security models for encrypted search."
    ],
    "rel_dynamic_v3": [
        "Follow-up designs let users add files without having to re-encrypt everything.",
        "Later systems let users add files without re-encrypting the whole dataset.",
        "Later schemes allowed users to add files without re-encrypting whole datasets.",
        "Follow-up systems let users insert new files without re-indexing all documents.",
        "Later designs enabled file additions without re-encrypting entire collections."
    ],
    "rel_cash_v3": [
        "Cash introduced fast boolean searches over encrypted multi-maps.",
        "Cash showed how to run fast boolean queries on encrypted index tables.",
        "Cash enabled fast boolean search queries across encrypted documents.",
        "Cash made boolean queries fast and practical over encrypted multi-maps."
    ],
    "rel_patel_v3": [
        "Patel placed query results into fixed bins to cut down volume leakage.",
        "Patel grouped query results into fixed bins to reduce leakage.",
        "Patel grouped search outputs into fixed-size bins to hide match numbers.",
        "Patel clustered search results into fixed bins to limit volume leakage."
    ],
    "rel_sophos_v3": [
        "Sophos added forward privacy so old queries never find newly added files.",
        "Sophos introduced forward privacy so past queries cannot find new documents.",
        "Sophos created forward privacy to keep past queries from uncovering new files.",
        "Sophos introduced forward privacy so older searches cannot match new files."
    ],
    "sec_syntax_v3": [
        "Our system relies on six simple operations to search encrypted data.",
        "Our encrypted search design uses six basic operations.",
        "We define six simple operations for encrypted search.",
        "Our scheme runs on six fundamental operations.",
        "Our searchable encryption scheme uses six primary operations."
    ],
    "disc_wider_v3": [
        "When searching very large datasets, users can configure wider buckets to reduce network traffic.",
        "Users with large collections can choose wider bucket steps to save mobile data.",
        "Users with large libraries can select wider buckets to reduce data consumption.",
        "For huge libraries, users can configure wider buckets to save mobile data."
    ],
    "fig1_caption": [
        "VisioCrypt mobile-cloud architecture: client trust boundary, query decorrelation delay channel, and cloud-side encrypted index multi-map.",
        "System architecture showing the phone trust boundary, delay channel, and cloud index.",
        "Overview of VisioCrypt architecture across mobile client, delay channel, and cloud storage.",
        "System architecture with phone trust boundary, delay channel, and cloud index."
    ],
    "fig2_caption": [
        "Volume padding: unpadded searches reveal exact counts, whereas VisioCrypt groups results into power-of-two buckets.",
        "Volume padding: (a) unpadded searches reveal exact counts, and (b) VisioCrypt pads results into power-of-two buckets.",
        "Volume leakage mitigation: unpadded search reveals exact match counts, whereas VisioCrypt groups responses into power-of-two buckets.",
        "Volume hiding: unpadded queries leak exact counts, while power-of-two padding clusters results."
    ],
    "fig3_caption": [
        "Empirical benchmarks: (a) file encryption throughput across tiers, and (b) RAM key persistence across runtimes.",
        "Mobile benchmarks: file encryption throughput and RAM key persistence comparison.",
        "Benchmark results: (a) file encryption throughput, and (b) RAM secret key persistence.",
        "Experimental benchmarks for file encryption throughput and RAM secret key persistence."
    ],
    "fig4_caption": [
        "Search latency across four hardware tiers: (a) log-scale comparison against baselines, and (b) sub-millisecond lookups.",
        "Search query latency across hardware tiers comparing unindexed scans with VisioCrypt lookups.",
        "Search latency across four hardware tiers: log-scale baseline comparison and sub-millisecond lookups.",
        "Multi-device search query latency across tested smartphone tiers."
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

print("\n--- BEST CANDIDATES BATCH FINAL 3 ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
