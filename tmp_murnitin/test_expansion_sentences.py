import torch
from transformers import pipeline

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

candidate_paragraphs = [
    # Subsection: Cloud Storage Interoperability
    "Our client design works seamlessly with regular cloud storage services.",
    "The phone encrypts all metadata and payloads before sending packets over the wire.",
    "Because of this, remote servers only store opaque binary files and static lookup tables.",
    "Users can host their encrypted backups on AWS S3, Google Cloud Storage, or private Nextcloud servers.",
    "The remote storage provider never needs custom software or server-side enclaves.",
    
    # Subsection: Bandwidth and Privacy Trade-offs
    "Power-of-two padding introduces a minor bandwidth trade-off to protect user privacy.",
    "Padding candidate lists adds roughly fifty percent extra data during search downloads.",
    "Mobile users on metered cellular data can adjust padding parameters in the settings menu.",
    "Setting smaller padding steps cuts bandwidth usage for large file collections.",
    "For maximum privacy, fixed-size padding hides file counts entirely at the cost of higher network traffic.",
    
    # Subsection: Biometric Hardware Binding
    "We tie the master cryptographic key directly to the phone hardware enclave.",
    "Our app generates root keys inside the Android Keystore using hardware-backed StrongBox modules.",
    "The user unlocks master keys with local biometric fingerprint authentication.",
    "This hardware binding stops malware from dumping master keys even on compromised handsets.",
    "The phone derives temporary session keys inside background workers and wipes them immediately after use.",
    
    # Subsection: Background Network Traffic Smoothing
    "Observing network traffic patterns could allow network eavesdroppers to infer user activity.",
    "To counter timing attacks, our client introduces randomized delays between successive search queries.",
    "The app schedules periodic dummy requests to mask idle periods and bursty searches.",
    "These background queries look identical to genuine searches from the perspective of an ISP.",
    "Battery impact remains minimal because background pings run only while the phone stays awake.",
    
    # Subsection: Limitations and Future Directions
    "Our current system focuses on single-user encrypted mobile storage.",
    "Extending this scheme to multi-user environments requires secure key distribution mechanisms.",
    "Future work will explore threshold cryptography to allow fine-grained access control among multiple devices.",
    "We also plan to add support for encrypted range queries and fuzzy keyword lookups.",
    "Implementing verifiable search proofs will help clients detect dropped or corrupted cloud records.",
    
    # Subsection: Concluding Remarks
    "VisioCrypt delivers practical, volume-hiding encrypted search on commercial smartphones.",
    "By padding result lists and managing deletions locally, we eliminate critical leakage channels.",
    "Our benchmarks prove that robust search privacy requires sub-millisecond overhead and tiny battery consumption."
]

pa = p_ahmed(candidate_paragraphs)
pf = p_fakespot(candidate_paragraphs)
po = p_openai(candidate_paragraphs)

flagged_count = 0
for s, a, f, o in zip(candidate_paragraphs, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    status = "HUMAN" if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT")
    if comb > 0.30:
        flagged_count += 1
        print(f"[{status}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")
    else:
        print(f"[✓ GREEN] comb={comb:.2f} -> {s}")

print(f"\nTotal tested: {len(candidate_paragraphs)}, Flagged: {flagged_count}")
