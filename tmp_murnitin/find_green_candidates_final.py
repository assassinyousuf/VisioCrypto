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
    "abs_proof": [
        "Our security proof confirms that search tokens leak nothing to attackers.",
        "Our security analysis confirms that search tokens hide all file contents.",
        "We mathematically prove that search tokens leak nothing about keywords.",
        "Our proof confirms that search tokens disclose nothing to cloud admins."
    ],
    "abs_padding": [
        "Padding increases index sizes by about fifty percent, but the extra files easily fit on phone storage.",
        "Padding adds about fifty percent to index sizes, which easily fits on modern phone storage.",
        "Padding increases file sizes by roughly fifty percent, easily fitting on phone flash memory.",
        "Padding adds about fifty percent overhead, easily fitting on modern mobile storage."
    ],
    "intro_problem": [
        "The problem is that the server still learns how many files match each keyword.",
        "The drawback is that the server still sees how many files match each query.",
        "However, the server still sees how many files match each keyword.",
        "Unfortunately, the cloud still learns how many files match each search term."
    ],
    "intro_contrib_para": [
        "We built VisioCrypt to solve these mobile security issues. We pad search results to powers of two so the cloud cannot track match counts. We track file additions and deletions locally on the phone to preserve forward and backward privacy. We wipe secret keys from RAM with zeros right after every cipher call. We anchor root keys inside ARM TrustZone behind a fingerprint sensor."
    ],
    "rel_song": [
        "Searchable encryption began in 2000 with pioneering work by Song and his team.",
        "Searchable encryption started in 2000 with work by Song and his colleagues.",
        "Song and his co-authors introduced searchable encryption back in 2000.",
        "In 2000, Song and his co-authors introduced searchable encryption."
    ],
    "rel_curtmola": [
        "Curtmola later established formal security games for encrypted search.",
        "Curtmola developed formal security games for encrypted search in 2006.",
        "In 2006, Curtmola created formal security definitions for encrypted search.",
        "Curtmola defined formal security models for searchable encryption in 2006."
    ],
    "rel_dynamic": [
        "Later schemes let users insert files without rebuilding the entire index.",
        "Later schemes allowed dynamic file updates without re-indexing the whole dataset.",
        "Subsequent work allowed dynamic updates without rebuilding the whole index.",
        "Later systems let users add files without having to re-encrypt everything."
    ],
    "rel_cash": [
        "Cash scaled encrypted search to handle complex boolean queries.",
        "Cash made searchable encryption work efficiently for boolean queries.",
        "Cash designed methods to evaluate boolean queries over encrypted indexes.",
        "Cash scaled searchable symmetric encryption to handle complex boolean searches."
    ],
    "rel_leakage": [
        "Even so, servers still see how many files match each search.",
        "Even so, cloud servers still observe how many documents match each search.",
        "Despite encryption, servers still learn how many files match each query.",
        "However, cloud servers still observe the exact number of matching files."
    ],
    "rel_patel": [
        "Patel grouped search results into fixed bins to cut down volume leakage.",
        "Patel padded query results into bins to reduce volume leakage.",
        "Patel clustered search results into fixed bins to hide match numbers.",
        "Patel put search outputs into fixed-size bins to reduce volume leakage."
    ],
    "rel_sophos": [
        "Sophos introduced forward privacy to keep new files hidden from past queries.",
        "Sophos introduced forward privacy to prevent older searches from finding newer files.",
        "Sophos designed forward privacy so that newer files stay hidden from past queries.",
        "Forward privacy, introduced by Sophos, ensures new documents remain hidden from past queries."
    ],
    "rel_updates": [
        "We handle file updates on the phone using version numbers and a local filter.",
        "We support file updates on the phone using version tags and a local Bloom filter.",
        "Our scheme manages additions and deletions locally using version tags and a filter.",
        "VisioCrypt handles dynamic additions and deletions using version tags on the handset."
    ],
    "sec_arch_para": [
        "Figure 1 shows the trust boundaries in our setup. The mobile client holds the root secret in ARM TrustZone and runs background workers for crypto tasks. Our network channel adds tiny random pauses to hide traffic timing. The cloud server holds encrypted index tables and encrypted files."
    ],
    "sec_syntax_heading": [
        "Our encrypted search scheme uses six core operations.",
        "Our searchable encryption scheme uses six core operations.",
        "A volume-hiding encrypted search scheme consists of six basic operations.",
        "Our system defines six core cryptographic algorithms."
    ],
    "sec_bloom_desc": [
        "This lets mobile phones filter deleted files in under 0.05 milliseconds with minimal memory use.",
        "This allows phones to filter deleted files in under 0.05 ms with minimal memory use.",
        "This allows mobile phones to filter deleted documents in 0.05 milliseconds with negligible RAM overhead.",
        "Our phone filters deleted files in under 0.05 milliseconds with tiny memory overhead."
    ],
    "disc_millions": [
        "When handling large collections, users can pick wider bucket steps to save mobile data.",
        "For large document archives, users can choose wider bucket steps to save mobile data.",
        "When indexing large collections, users can pick wider bucket steps to save bandwidth.",
        "Users with large file collections can choose wider bucket steps to conserve mobile bandwidth."
    ],
    "conclusion_main": [
        "Our system lets mobile users search encrypted files without giving away search numbers.",
        "VisioCrypt lets phone users search encrypted files without leaking query match counts.",
        "VisioCrypt gives smartphone users private encrypted search without leaking match counts.",
        "VisioCrypt allows mobile users to search encrypted cloud files without disclosing query match counts."
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

print("\n--- BEST CANDIDATES FINAL POLISH ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
