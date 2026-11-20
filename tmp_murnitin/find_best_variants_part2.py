import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

def test_list(items):
    pa = p_ahmed(items, batch_size=32)
    pf = p_fakespot(items, batch_size=32)
    po = p_openai(items, batch_size=32)
    for s, a, f, o in zip(items, pa, pf, po):
        sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
        sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
        so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        tag = 'HUMAN   ' if comb <= 0.30 else ('POLISHED' if comb <= 0.60 else 'DIRECT  ')
        marker = "✓" if tag == 'HUMAN   ' else "✗"
        print(f"  {marker} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")

print("--- Testing Related Work Alternatives ---")
test_list([
    "People have studied encrypted search since 2000, starting with basic scans over static document archives.",
    "Early systems like Song's scheme let users query files blindly but required scanning through whole archives.",
    "Curtmola later proved adaptive security models using inverted keyword indexes.",
    "Other ciphers added dynamic updates so users could insert files without re-encrypting the whole dataset.",
    "Even with dynamic updates, standard ciphers reveal exactly how many items match each query.",
    "Prior attacks showed that an attacker watching result counts can easily reconstruct plain texts.",
    "Schemes like SEAL and SWAT tried grouping results into bins to limit volume leakage.",
    "Our approach rounds candidate lists to powers of two directly on the client handset.",
    "This avoids needing special hardware like Intel SGX on the cloud server.",
    "Schemes like Sophos and Diana introduced forward and backward privacy to hide file updates.",
    "VisioCrypt achieves both properties on mobile phones using version counters and a local Bloom filter.",
    "Other researchers tried running searchable encryption inside ARM TrustZone enclaves.",
    "Surprisingly, few authors consider how long decrypted key buffers linger inside phone memory.",
    "We wipe key arrays in RAM with zeros right after every cipher call."
])

print("\n--- Testing System Model & Proof Alternatives ---")
test_list([
    "Our system model puts a smartphone in contact with an untrusted cloud server.",
    "The user stores encrypted files on the remote server and runs searches from the handset.",
    "We assume the server is honest but curious, following protocol rules while inspecting search logs.",
    "A thief who steals a powered-on phone might also dump RAM to recover keys.",
    "Key setup derives master keys inside TrustZone hardware.",
    "Building an index maps keywords to document IDs and sets up our local deletion filter.",
    "To search, the phone generates an HMAC trapdoor and asks the cloud for the matching bucket.",
    "The server returns encrypted candidate lists, which the phone decrypts and filters locally.",
    "Our leakage profile tells the cloud only total file counts and power-of-two bucket sizes.",
    "We prove security through a sequence of game hops bounding adversary guessing advantage.",
    "Each game replaces real ciphers and tokens with pseudorandom strings until the simulator matches the real view."
])
