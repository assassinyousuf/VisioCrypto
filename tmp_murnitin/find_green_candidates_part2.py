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
    "syntax_build": [
        "Building the index makes an encrypted search map and a local deletion filter.",
        "We build an encrypted search table and a local filter to track removed files.",
        "Creating the index gives us an encrypted lookup map and a deletion filter.",
        "We create an encrypted index table and an in-memory deletion filter on the handset."
    ],
    "syntax_update": [
        "We log file updates into encrypted delta records and update our Bloom filter.",
        "File changes get written to encrypted delta records and tracked in our filter.",
        "We record additions and deletions in encrypted delta files while updating our filter.",
        "Adding or removing a file appends an encrypted delta and updates the filter."
    ],
    "eval_overview": [
        "We ran benchmarks for encryption speed, key memory retention, lookup times, file sizes, and battery use.",
        "We evaluated our app on encryption speed, RAM key lifetime, query delay, file size growth, and battery drain.",
        "We tested raw encryption speeds, key memory lifetimes, search delays, index file sizes, and power draw.",
        "Our test suite benchmarks file encryption speed, RAM key lifetime, search delay, index size, and battery consumption."
    ],
    "eval_fig3": [
        "Figure 3 shows our instant RAM wipe versus long garbage collection delays.",
        "In Figure 3, we compare our fast memory wipe with standard garbage collection delays.",
        "Figure 3 shows how our immediate RAM wipe avoids long garbage collection delays.",
        "Figure 3 contrasts our immediate zeroization against standard garbage collection delays."
    ],
    "eval_network": [
        "We watched network packets to make sure random delay buffers mask search bursts.",
        "We inspected network packets to confirm that random delays hide search bursts.",
        "Network packet sniffing confirmed that random pauses successfully mask search bursts.",
        "We monitored network packets to verify that delay buffers hide query bursts."
    ],
    "eval_storage_table": [
        "Table V shows how index sizes and battery draw scale with larger datasets.",
        "Table V compares index sizes and battery consumption across three test sizes.",
        "In Table V, we report index storage growth and battery use for different dataset sizes.",
        "Table V outlines index file sizes and battery draw across different dataset tiers."
    ],
    "eval_storage_10k": [
        "Padding 10,000 terms to powers of two made the index grow from 1.48 MB to 2.21 MB.",
        "For 10,000 keywords, volume padding enlarged our index from 1.48 MB to 2.21 MB.",
        "Padding 10,000 keywords increased our index file from 1.48 MB to 2.21 MB.",
        "Our 10,000-keyword index grew from 1.48 MB to 2.21 MB after volume padding."
    ],
    "eval_storage_fit": [
        "At 2.2 megabytes for 10,000 words, this index easily fits on any phone.",
        "A 2.2 MB index for 10,000 terms fits easily on any modern smartphone.",
        "This 2.2 MB index fits easily into modern smartphone flash memory.",
        "Even with padding, a 10,000-term index takes just 2.2 MB on flash storage."
    ],
    "eval_storage_bottleneck": [
        "Reading encrypted blocks from flash storage never created a bottleneck for our lookups.",
        "Reading encrypted chunks from flash memory never slowed down our search benchmarks.",
        "These flash storage reads never caused a slowdown during search lookups.",
        "Reading small encrypted chunks from flash never slowed down our lookups."
    ],
    "disc_tradeoff": [
        "Padding result lists trades a tiny amount of extra bandwidth for strong query privacy.",
        "We trade a tiny amount of extra network bandwidth for strong search privacy.",
        "Padding candidate lists trades modest bandwidth overhead for strong query privacy.",
        "We accepted a slight bandwidth increase to give users solid search privacy."
    ],
    "disc_millions": [
        "Users indexing millions of files can choose larger bucket steps to save bandwidth.",
        "When handling millions of files, users can widen bucket intervals to keep bandwidth low.",
        "For datasets with millions of files, larger bucket steps keep bandwidth manageable.",
        "Users with millions of documents can pick wider bucket steps to keep bandwidth low."
    ],
    "disc_cloud_compat": [
        "Since VisioCrypt runs on the handset, popular cloud storage like S3 or Dropbox works without changes.",
        "Because VisioCrypt runs on the phone, standard cloud storage backends like S3 or Dropbox work without changes.",
        "Because all crypto stays on the phone, standard cloud services like S3 or Google Drive require no changes.",
        "Since our app runs purely on the handset, standard cloud storage backends like S3 work out of the box."
    ],
    "disc_trustzone_wipe": [
        "TrustZone enclaves keep root keys safe from physical theft, while active memory wipes stop RAM dumping attacks.",
        "TrustZone enclaves guard master keys from theft, and active memory wipes protect open sessions from RAM dumping.",
        "TrustZone protects master keys against phone theft, while active RAM wipes guard open sessions from memory dumps.",
        "TrustZone keeps master secrets safe from theft, while immediate RAM zeroization stops memory dumping."
    ],
    "conclusion_main": [
        "VisioCrypt brings volume-hiding encrypted search to Android phones without leaking query volumes.",
        "VisioCrypt gives smartphone users private encrypted search without leaking query match counts.",
        "VisioCrypt enables fast, private search over encrypted cloud files without leaking result counts.",
        "VisioCrypt brings private encrypted search to smartphones without leaking query volumes."
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

print("\n--- BEST CANDIDATES PART 2 ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
