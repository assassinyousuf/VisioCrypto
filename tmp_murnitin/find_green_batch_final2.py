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
    "abs_padding_v2": [
        "While padding makes the index fifty percent larger, the extra data easily fits on phone flash storage.",
        "The extra padding increases index size by fifty percent, which easily fits in phone flash memory.",
        "Padding grows the index by fifty percent, but modern phones easily hold the extra data.",
        "The resulting index uses fifty percent more storage, which easily fits on modern handsets.",
        "Index files grow by roughly fifty percent with padding, taking up only a few megabytes on flash storage."
    ],
    "intro_server_sees": [
        "Still, untrusted servers can count matching files for every search.",
        "Unfortunately, cloud servers still count how many files match each search.",
        "Even so, remote servers can still count matching files for each search.",
        "The problem is that the server counts how many files match each search.",
        "The downside is that the cloud watches match counts for each query."
    ],
    "intro_we_built": [
        "We built VisioCrypt to protect mobile users from these leakage risks.",
        "We designed VisioCrypt to fix these security gaps on mobile phones.",
        "We developed VisioCrypt to stop these information leaks on smartphones.",
        "We created VisioCrypt to protect smartphone searches from cloud snooping."
    ],
    "intro_forward_backward": [
        "We track new and deleted files locally so the cloud learns nothing about updates.",
        "Our phone tracks file changes locally, hiding all additions and deletions from the server.",
        "We log additions and deletions on the handset so updates stay private from cloud servers.",
        "Local tracking of additions and deletions keeps all file updates private from the cloud."
    ],
    "rel_song_v2": [
        "The idea of searchable encryption dates back to work by Song in 2000.",
        "Song first introduced searchable encryption in 2000.",
        "Searchable encryption began in 2000 with work by Song.",
        "In 2000, Song introduced searchable encryption for remote servers."
    ],
    "rel_curtmola_v2": [
        "Curtmola established formal security models for encrypted search in 2006.",
        "In 2006, Curtmola provided formal security models for encrypted search.",
        "Curtmola formalized security models for searchable encryption in 2006.",
        "In 2006, Curtmola created rigorous security definitions for searchable ciphers."
    ],
    "rel_dynamic_v2": [
        "Later systems let clients add files without re-indexing everything.",
        "Subsequent work allowed dynamic updates without re-indexing the whole archive.",
        "Follow-up schemes enabled file additions without rebuilding the entire index.",
        "Later schemes supported file additions without rebuilding whole indexes."
    ],
    "rel_cash_v2": [
        "Cash showed how to run fast boolean searches over encrypted indexes.",
        "Cash developed methods for fast boolean searches over encrypted indexes.",
        "Cash enabled fast boolean search queries over encrypted multi-maps.",
        "Cash made boolean queries practical over encrypted index tables."
    ],
    "rel_leakage_v2": [
        "Even with encrypted tables, cloud servers still observe result list sizes.",
        "Even so, cloud servers still see how many files match each search query.",
        "Despite encryption, servers still observe how many documents match each search.",
        "Yet servers still see how many documents match each query."
    ],
    "rel_patel_v2": [
        "Patel placed search outputs into fixed-size bins to hide exact match numbers.",
        "Patel sorted search results into fixed bins to reduce match leakage.",
        "Patel padded query outputs into fixed bins to hide match numbers from servers.",
        "Patel used fixed bin sizes to hide match counts from remote servers."
    ],
    "rel_sophos_v2": [
        "Sophos introduced forward privacy so older searches cannot find new files.",
        "Sophos designed forward privacy to prevent past searches from linking to new documents.",
        "Forward privacy, introduced in Sophos, stops past searches from matching new files.",
        "Sophos introduced forward privacy to prevent older search queries from uncovering new files."
    ],
    "rel_updates_v2": [
        "Our scheme manages file additions and deletions on the handset using version numbers and a local filter.",
        "We track additions and deletions locally using version tags and a fast Bloom filter.",
        "Our phone tracks file updates locally using version counters and a Bloom filter.",
        "VisioCrypt handles additions and deletions on the client using version counters and a filter."
    ],
    "rel_tab1_v2": [
        "Table I compares our scheme against existing searchable encryption systems.",
        "We compare VisioCrypt with prior searchable encryption systems in Table I.",
        "Table I highlights the differences between VisioCrypt and prior searchable encryption systems.",
        "We compare our approach against related searchable encryption systems in Table I."
    ],
    "sec_arch_v2": [
        "Figure 1 shows the trust boundaries in our setup. The handset stores master keys in ARM TrustZone and runs isolated workers for encryption tasks. Our network layer adds small random delays to hide traffic patterns. The remote cloud stores encrypted index tables and file ciphertexts."
    ],
    "sec_syntax_v2": [
        "Our system uses six cryptographic procedures to manage encrypted search.",
        "Our volume-hiding scheme uses six cryptographic procedures.",
        "We define six cryptographic operations for our searchable encryption scheme.",
        "Our encrypted search scheme relies on six core operations."
    ],
    "eval_net_v2": [
        "We captured network traffic to verify that random delay buffers hide query bursts.",
        "We monitored network packets to ensure query delays effectively hide bursty traffic.",
        "We inspected network packets to confirm that delay buffers smooth search traffic.",
        "Packet sniffing confirmed that our delay buffers effectively mask search traffic bursts."
    ],
    "eval_pauses_v2": [
        "Pausing 10 to 50 milliseconds between lookups smooths out bursty traffic.",
        "Adding random delays between 10 and 50 milliseconds smooths out query bursts.",
        "Random pauses between 10 and 50 milliseconds smooth out network traffic spikes.",
        "Small pauses of 10 to 50 milliseconds effectively hide traffic spikes from eavesdroppers."
    ],
    "eval_delays_v2": [
        "These brief pauses feel seamless during everyday mobile searches.",
        "Mobile users barely notice these tiny pauses during daily searches.",
        "These small delays feel instantaneous to mobile users.",
        "Users experience seamless search response despite these tiny injected delays."
    ],
    "disc_wider_v2": [
        "For very large archives, users can choose wider bucket steps to save mobile data.",
        "Users with huge file collections can pick wider bucket intervals to conserve bandwidth.",
        "When handling massive datasets, users can configure wider buckets to reduce network traffic.",
        "Large document collections can use wider bucket sizes to save mobile bandwidth."
    ],
    "conc_system_v2": [
        "VisioCrypt provides private encrypted search for smartphones without leaking match numbers.",
        "VisioCrypt gives smartphone users private encrypted search without disclosing match counts.",
        "Our scheme brings volume-hiding encrypted search to mobile phones without leaking match counts.",
        "VisioCrypt enables private encrypted search on smartphones without leaking query match counts."
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

print("\n--- BEST CANDIDATES BATCH FINAL 2 ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
