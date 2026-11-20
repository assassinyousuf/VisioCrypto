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

test_batch4 = [
    "Index creation outputs an encrypted hash table and a deletion filter.",
    "Trapdoors turn keywords and version numbers into encrypted search tags.",
    "File updates log encrypted changes while refreshing the phone deletion filter.",
    "We monitored packet traffic to make sure query delays mask search bursts.",
    "Pausing 10 to 50 milliseconds between lookups smooths out bursty traffic.",
    "These brief pauses are barely noticeable during everyday searches.",
    "For 10,000 search terms, power-of-two padding enlarged the index from 1.48 MB to 2.21 MB.",
    "A 10,000-word index fits comfortably in 2.2 megabytes of phone storage.",
    "Running 1,000 searches on our budget phone used just 1.85 millijoules of battery energy.",
    "Repeated queries naturally pull from warm memory caches.",
    "We cleared memory caches before every benchmark run to measure cold lookup speeds.",
    "Cold searches added less than 0.12 milliseconds of delay on every device.",
    "Padding search lists trades a tiny amount of bandwidth for robust query privacy.",
    "Power-of-two buckets hide match counts while adding about fifty percent more data.",
    "With millions of files, users can choose wider bucket steps to keep bandwidth low.",
    "Because VisioCrypt works entirely on the phone, standard cloud providers like S3 or Google Drive require no changes.",
    "Sending occasional dummy requests stops observers from timing real searches.",
    "TrustZone locks protect master keys from device theft, while active memory wipes protect open sessions from cold-boot memory dumps."
]

test_sents(test_batch4)
