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
    "rel_song_clean": [
        "Song developed the first searchable encryption scheme in 2000.",
        "Song built the first searchable encryption scheme in 2000.",
        "Song introduced searchable encryption in 2000.",
        "Song and his team introduced searchable encryption back in 2000.",
        "Song created practical searchable encryption in 2000."
    ],
    "rel_curtmola_clean": [
        "Curtmola established formal security models in 2006.",
        "Curtmola defined formal security models in 2006.",
        "In 2006, Curtmola established formal security games.",
        "Curtmola provided formal security definitions in 2006.",
        "Curtmola proved security models for encrypted search in 2006."
    ],
    "rel_dynamic_clean": [
        "Kamara added dynamic updates in 2012.",
        "Kamara developed dynamic searchable encryption in 2012.",
        "Later schemes let users add files dynamically.",
        "Follow-up designs enabled dynamic file additions.",
        "Subsequent schemes added dynamic updates without rebuilding indexes."
    ],
    "rel_cash_clean": [
        "Cash made boolean queries fast across large indexes.",
        "Cash scaled boolean search queries over encrypted multi-maps.",
        "Cash showed how to run fast boolean queries on encrypted index tables.",
        "Cash introduced fast boolean searches for encrypted databases."
    ],
    "rel_leakage_clean": [
        "Even so, servers still see how many documents match each search.",
        "Yet servers still observe how many documents match each query.",
        "Unfortunately, cloud servers still count how many files match each search.",
        "Watching search match counts lets attackers reconstruct full databases."
    ],
    "rel_patel_clean": [
        "Patel placed query results into fixed bins to cut down volume leakage.",
        "Patel sorted query results into fixed bins to hide match numbers.",
        "Patel clustered search results into fixed bins to reduce volume leakage.",
        "Patel padded search outputs into fixed-size bins to hide match counts."
    ],
    "rel_table1_clean": [
        "Table I compares VisioCrypt with prior art across key design dimensions.",
        "We compare our scheme with prior work in Table I.",
        "Table I summarizes key features across searchable encryption schemes.",
        "We contrast our scheme with existing systems in Table I."
    ],
    "sec_arch_1": [
        "The phone stores root keys in ARM TrustZone and runs isolated workers for encryption tasks.",
        "The mobile device holds the root key in ARM TrustZone and runs background workers for encryption.",
        "Our phone keeps the root key inside ARM TrustZone and runs isolated encryption workers."
    ],
    "sec_arch_2": [
        "Our network channel inserts tiny random delays to hide traffic patterns.",
        "The network layer adds small random delays to hide query timing.",
        "Our network channel adds tiny random pauses to hide traffic timing."
    ],
    "sec_arch_3": [
        "The cloud server holds encrypted index tables and encrypted files.",
        "The remote server stores encrypted index tables and document ciphertexts.",
        "The untrusted cloud server stores encrypted multi-maps and document ciphertexts."
    ],
    "sec_syntax_clean": [
        "We define six core algorithms for volume-hiding encrypted search.",
        "Our encrypted search scheme relies on six core operations.",
        "Our system defines six cryptographic algorithms for encrypted search.",
        "We build our encrypted search scheme around six basic operations."
    ],
    "eval_net_clean": [
        "We inspected network packets to confirm that delay buffers smooth search traffic.",
        "Packet sniffing confirmed that our delay buffers effectively mask search traffic bursts.",
        "We monitored network packets to make sure query delays hide bursty traffic.",
        "We tested network traffic to confirm that delay buffers hide query bursts."
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

print("\n--- BEST CANDIDATES CLEAN PROSE ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
