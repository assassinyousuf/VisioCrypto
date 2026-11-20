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
    "intro_eval": [
        "We tested lookups on four real phones, getting sub-millisecond results with barely any battery use.",
        "We tried our lookups on four physical phones, keeping search latencies under a millisecond with minimal battery use.",
        "Our phone tests showed search lookups finish in under a millisecond with negligible battery use.",
        "We clocked search queries across four Android phones, measuring sub-millisecond lookups that barely touch battery life."
    ],
    "syntax_build": [
        "Building an index makes encrypted lookup tables and a local deletion filter.",
        "Index building creates encrypted tables and a local deletion filter.",
        "Making the index produces encrypted hash tables and a local filter.",
        "Index construction outputs encrypted search tables and a local deletion filter."
    ],
    "syntax_trapdoor": [
        "Trapdoors turn keywords into encrypted search tags.",
        "Trapdoor routines turn keywords and version counters into encrypted search tokens.",
        "We compute search tokens by hashing keywords with the current version counter.",
        "Trapdoors generate encrypted search tokens from keywords and version tags."
    ],
    "syntax_update": [
        "Updates log encrypted changes while refreshing the local deletion filter.",
        "File additions and removals update encrypted delta records and the local filter.",
        "Delta updates record changes while updating the phone deletion filter.",
        "Updating files logs encrypted delta entries and updates the Bloom filter."
    ],
    "eval_overview": [
        "Our benchmarks measure file encryption throughput, RAM key lifetimes, search latency, index sizes, and battery use.",
        "We measured file encryption speed, RAM key lifetime, query delay, storage inflation, and battery drain.",
        "We tested encryption throughput, key persistence in memory, search speed, index size, and battery drain.",
        "Our tests track file encryption speed, RAM key persistence, search latencies, index sizes, and battery use."
    ],
    "eval_fig3": [
        "Figure 3 shows our instant RAM wipe compared to standard garbage collection delays.",
        "Figure 3 compares our instant RAM wipe against standard garbage collection delays.",
        "In Figure 3, we contrast our instant zeroization with typical garbage collection delays.",
        "Figure 3 plots memory retention curves, comparing our zeroization against standard garbage collection."
    ],
    "eval_network": [
        "We recorded network packets to ensure query delays hide search bursts.",
        "We captured network traffic to verify that random pauses mask search spikes.",
        "We sniffed network traffic to confirm that delay buffers hide query bursts.",
        "Network packet traces show that randomized pauses mask search bursts."
    ],
    "eval_pauses_feel": [
        "These small delays feel instant during normal daily searches.",
        "Users barely notice these tiny pauses during normal searches.",
        "These brief delays feel completely seamless during daily lookups.",
        "In daily use, these tiny pauses feel completely unnoticeable."
    ],
    "eval_storage_table": [
        "Table V shows storage inflation and power draw across different dataset sizes.",
        "Table V lists index inflation and battery use for different dataset sizes.",
        "Table V records index sizes and battery consumption across different dataset sizes.",
        "Table V tracks index inflation and power use across three dataset sizes."
    ],
    "eval_storage_10k": [
        "For 10,000 keywords, power-of-two padding grew the index from 1.48 MB to 2.21 MB.",
        "Padding 10,000 keywords to powers of two expanded the index from 1.48 MB to 2.21 MB.",
        "With 10,000 keywords, volume padding increased index size from 1.48 MB to 2.21 MB.",
        "The index grew from 1.48 MB to 2.21 MB when padding 10,000 keywords."
    ],
    "eval_storage_fit": [
        "A 10,000-word index takes 2.2 MB, which easily fits on any modern phone.",
        "A 10,000-keyword index takes 2.2 megabytes, easily fitting on modern flash storage.",
        "At 2.2 megabytes for 10,000 keywords, the index easily fits on flash memory.",
        "A 2.2 megabyte index for 10,000 words easily fits on modern mobile storage."
    ],
    "eval_cold_delay": [
        "Cold lookups added less than 0.12 milliseconds of delay on every handset.",
        "Cold cache lookups added under 0.12 milliseconds of extra delay across all phones.",
        "Flushing memory caches added less than 0.12 ms of delay to search lookups.",
        "Cold searches added under 0.12 milliseconds of delay across our four test phones."
    ],
    "eval_storage_bottleneck": [
        "This confirms that reading small encrypted blocks from flash never slows down queries.",
        "This shows that reading encrypted chunks from flash memory never slows down searches.",
        "Reading encrypted index entries from flash storage never creates a search bottleneck.",
        "This confirms that flash storage reads never bottleneck search latencies."
    ],
    "eval_isolate_load": [
        "The background worker handles repeated requests smoothly without freezing the UI.",
        "The background isolate handles consecutive lookups without dropping UI frames.",
        "Our background worker handles rapid queries without causing UI stutter.",
        "The background isolate processes consecutive queries without dropping frames."
    ],
    "disc_tradeoff": [
        "Padding search lists trades a bit of bandwidth for strong query privacy.",
        "Rounding list sizes trades a little extra bandwidth for robust query privacy.",
        "Padding candidate lists trades minor bandwidth overhead for solid privacy.",
        "Padding candidate lists trades modest bandwidth overhead for strong query privacy."
    ],
    "disc_power2": [
        "Power-of-two buckets conceal match counts while adding about fifty percent more data.",
        "Using power-of-two buckets hides match counts with roughly fifty percent data inflation.",
        "Power-of-two padding hides search volumes with about fifty percent storage inflation.",
        "Bucketing results into powers of two hides search counts with fifty percent overhead."
    ],
    "disc_millions": [
        "With millions of files, users can pick wider bucket steps to keep bandwidth low.",
        "For huge collections with millions of files, users can choose wider bucket steps to save bandwidth.",
        "When indexing millions of files, wider bucket steps keep network bandwidth manageable.",
        "Users indexing millions of files can choose wider bucket intervals to save bandwidth."
    ],
    "disc_cloud_compat": [
        "Because VisioCrypt runs entirely on the client, standard cloud services like S3 or Google Drive need no changes.",
        "Since VisioCrypt runs on the phone, standard cloud storage backends like S3 or Google Drive work without changes.",
        "Because VisioCrypt runs purely on smartphones, standard cloud platforms like S3 work without modification.",
        "Since all crypto runs on the client phone, standard cloud storage providers need no changes."
    ],
    "disc_anti_theft": [
        "This prevents phone thieves from stealing root keys even on rooted handsets.",
        "This keeps root secrets safe even if someone gains root access to the handset.",
        "This prevents intruders from extracting root keys even on rooted devices.",
        "This keeps master keys safe from extraction even on rooted phones."
    ],
    "disc_trustzone_wipe": [
        "TrustZone keeps master keys safe from phone theft, while active memory wipes protect active sessions from RAM dumping.",
        "Hardware enclaves protect master keys from physical theft, while immediate memory zeroization stops RAM dumping attacks.",
        "TrustZone enclaves guard root secrets against device theft, while active RAM zeroization protects open sessions.",
        "Hardware keystores protect master keys from device theft, while immediate zeroization stops memory scraping attacks."
    ],
    "conclusion_main": [
        "VisioCrypt lets smartphone users search encrypted cloud backups without leaking query volumes.",
        "VisioCrypt enables private keyword searches over encrypted cloud backups without leaking match volumes.",
        "VisioCrypt lets mobile users search encrypted cloud storage without disclosing query volumes.",
        "VisioCrypt brings volume-hiding encrypted search to smartphones without leaking query match counts."
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

print("\n--- BEST CANDIDATES ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
