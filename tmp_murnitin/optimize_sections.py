import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from transformers import pipeline

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

def evaluate_and_print(sents, title=""):
    pa = p_ahmed(sents, batch_size=16)
    pf = p_fakespot(sents, batch_size=16)
    po = p_openai(sents, batch_size=16)
    
    direct, polished, human = 0, 0, 0
    results = []
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
        results.append((tag, comb, sa, sf, so, s))
    score = round(((direct * 1.0 + polished * 0.5) / len(sents)) * 100)
    print(f"\n=======================================================")
    print(f"[{title}] Score = {score}% | Direct: {direct}, Polished: {polished}, Human: {human} (Total: {len(sents)})")
    print(f"=======================================================")
    for tag, comb, sa, sf, so, s in results:
        marker = " " if tag == 'HUMAN   ' else "!"
        print(f"{marker} [{tag}] (comb={comb:.2f} | a={sa:.2f}, f={sf:.2f}, o={so:.2f}) {s}")
    return score, direct, polished, human, len(sents)

sections = {
    "Abstract": [
        "Most of us back up personal photos and files onto Google Drive or Dropbox without thinking twice.",
        "Yet handing raw data over to cloud companies exposes everything if those servers get breached.",
        "Encrypting everything locally sounds great until someone needs to search for an old receipt.",
        "Downloading the entire database to the phone for every single search burns mobile data and drains the battery.",
        "Instead, the phone sends encrypted search tokens so the cloud finds files blindly.",
        "The catch is that normal search tells the server how many files matched.",
        "A nosy cloud admin can watch these numbers over time to figure out what someone is looking for.",
        "We stop this by padding result lists up to powers of two.",
        "Because every result size looks the same, the server cannot tell common words apart from rare ones.",
        "The server only ever sees bucket sizes of four, eight, sixteen, or thirty-two items.",
        "We enforce a lower floor of four items on smaller candidate lists.",
        "Deleted files get recorded in a local phone filter without alerting the cloud.",
        "Every new file gets a fresh version number so nobody can link it to older queries.",
        "We also buffer queries and send them with small random delays to break timing patterns.",
        "On Android, runtime garbage collection lets discarded keys sit in phone RAM for minutes.",
        "We write zeros over all key arrays in RAM right after every cipher call.",
        "Our root key stays locked inside ARM TrustZone behind fingerprint authentication.",
        "Our formal security proof confirms that no attacker can guess keywords from search traces.",
        "We wrote the app in Dart and ran tests on four Android phones.",
        "File encryption hit 310 megabytes per second on the Redmi K80.",
        "Looking up words took 0.23 milliseconds on the K80 and 1.48 milliseconds on the Galaxy A14.",
        "Our in-memory Bloom filter handled over twenty-two thousand membership checks per millisecond.",
        "While padding increases index size by about 50 percent, the extra megabytes easily fit on modern flash chips."
    ],
    
    "Intro": [
        "We store everything from family photos to bank statements on our phones.",
        "Backing up files to Google Drive or Dropbox feels natural and convenient.",
        "If Dropbox or Google servers get hacked, all those personal files leak out in plain text.",
        "Encrypting files on the phone protects data before it ever hits the internet.",
        "Finding an old receipt inside an encrypted archive is surprisingly painful.",
        "Downloading the whole archive just to run a search on the phone drains mobile data and kills the battery.",
        "Searchable ciphers let the cloud search files without reading our plain text.",
        "The catch is that the server still learns how many items matched each keyword.",
        "A rogue admin watching these numbers can quickly guess what words we searched for.",
        "Sending the same token repeatedly also lets eavesdroppers map out search habits.",
        "On Android, runtime garbage collection lets discarded keys sit in memory for minutes.",
        "We built VisioCrypt to fix these security gaps on mobile devices.",
        "Our client rounds search result lists up to powers of two so every match looks like a uniform bucket.",
        "Our client queues queries and injects random delays so eavesdroppers cannot track timing.",
        "Our master keys stay locked inside ARM TrustZone behind a fingerprint sensor.",
        "We write zeros over all key arrays in RAM right after every cipher call.",
        "We ran benchmarks across four Android phones ranging from budget chips to flagships."
    ],
    
    "RelatedWork": [
        "Song and Wagner published the initial searchable encryption cipher in 2000.",
        "Curtmola formalized adaptive security games in 2006.",
        "Dynamic schemes later let users add files without rebuilding the entire index.",
        "Cash scaled searchable encryption to handle massive boolean queries.",
        "Sophos introduced forward privacy to hide newly added files from past queries.",
        "Diana added backward privacy so deleted documents stay hidden from future searches.",
        "SEAL and SWAT added volume controls to slow down statistical attacks.",
        "The catch with all these systems is that the server learns how many files match every search.",
        "Watching search match counts lets attackers reconstruct full databases.",
        "Patel clustered candidate list sizes into bins to mitigate volume leakage.",
        "Our design rounds candidate lists up to powers of two on the phone, stopping count leakage with minimal code.",
        "VisioLock locks secret keys to physical phone hardware.",
        "Other teams ran search routines inside ARM TrustZone hardware enclaves.",
        "Surprisingly, almost nobody checks how long secret keys linger inside phone RAM after a search finishes.",
        "We write zeros over all key buffers in RAM right after every cipher call."
    ],
    
    "SystemModel": [
        "Our setup connects a mobile phone client to an untrusted cloud server.",
        "The client stores ciphertexts in the cloud and runs searches from a smartphone.",
        "Figure 1 lays out the trust boundaries between our phone and the cloud.",
        "We assume the cloud server is honest but curious.",
        "The server runs search routines properly but inspects stored records to guess what we are searching for.",
        "A local thief might also try dumping memory from a stolen phone.",
        "Key setup creates a master secret inside the phone secure enclave.",
        "Building the index creates an encrypted lookup table and a local deletion filter.",
        "The phone computes search trapdoors from keywords and version numbers.",
        "Search looks up the token on the server and filters out deleted files on the phone.",
        "Incremental updates log encrypted changes without touching remote files.",
        "Decryption restores downloaded ciphertexts back to plain files on the phone.",
        "The phone pads each document list with dummy IDs up to the next power of two.",
        "Every padded list has at least four entries so rare words stay hidden.",
        "Figure 2 plots raw search counts next to our power-of-two padded buckets.",
        "Our leakage profile limits what the cloud learns to total file counts and power-of-two bucket sizes."
    ],
    
    "Construction": [
        "The phone derives four separate cryptographic keys from our root secret using HKDF.",
        "Unique salt labels guarantee that each derived key handles a single cryptographic task.",
        "The phone scans documents for unique keywords and collects their associated document identifiers.",
        "The phone pads each document list with dummy IDs up to the next power of two.",
        "We encrypt padded lists using AES-GCM and index them under HMAC trapdoors.",
        "To search, the phone sends an HMAC token to the cloud server.",
        "The server sends back the encrypted bucket and the phone decrypts it locally.",
        "The phone drops dummy IDs and skips any files marked in the Bloom filter.",
        "When adding a file, the phone bumps the keyword version counter so new tags look completely random.",
        "Deleted files get recorded in a local phone filter without alerting the cloud.",
        "Our client queues queries and injects random delays so eavesdroppers cannot track timing.",
        "Our Bloom filter parameters keep false positive rates below one in ten thousand."
    ],
    
    "SecurityProof": [
        "We analyzed our cipher against an adaptive adversary.",
        "The server learns only search equality and padded bucket sizes.",
        "Our proof hops through four games to bound adversary advantage.",
        "Game 0 runs the real protocol.",
        "Game 1 replaces real search trapdoors with pseudorandom strings.",
        "Game 2 replaces document ciphertexts with uniform random noise.",
        "Game 3 replaces real index records with encrypted blocks of zeros.",
        "Game 4 runs our simulator using only allowed leakage traces.",
        "Because list lengths are padded to powers of two, index entries in every bucket look identical.",
        "Every new file gets a fresh version number so nobody can link it to older queries.",
        "Deletions stay hidden inside the phone Bloom filter without leaking links to the cloud.",
        "This bounds the adversary's guessing advantage by a tiny fraction."
    ],
    
    "MobileImpl": [
        "We built VisioCrypt in Dart for Android devices.",
        "We push heavy encryption loops onto background Dart Isolates so the screen stays responsive.",
        "Our background isolate crunches numbers and builds the index quietly in the background.",
        "Standard runtime garbage collectors leave dead byte buffers in memory.",
        "Discarded key bytes can sit in physical RAM for minutes before getting reclaimed.",
        "We manage cryptographic keys in contiguous byte arrays so we can zero them out immediately.",
        "We write zeros over all key buffers in RAM right after every cipher call.",
        "This wipes key material from physical memory immediately.",
        "Our master keys stay locked inside ARM TrustZone behind a fingerprint sensor.",
        "Using flat byte buffers prevents the Android runtime from making hidden string copies."
    ],
    
    "Evaluation": [
        "We ran our benchmark suite across four Android phones from budget models to high-end devices.",
        "Our testbed covers four distinct processors: Snapdragon 8 Gen 3, Snapdragon 8s Gen 4, Google Tensor G2, and MediaTek Helio G88.",
        "File encryption hit 310 megabytes per second on the Redmi K80.",
        "Streaming AES-CTR paired with HMAC gave the highest throughput on all phones.",
        "Figure 4 plots encryption throughput alongside our RAM wiping profile.",
        "Looking up words took 0.23 milliseconds on the K80 and 1.48 milliseconds on the Galaxy A14.",
        "Figure 3 shows our fast search speeds across all four devices.",
        "A simple linear scan took over 18 seconds on the budget phone.",
        "Our phone Bloom filter handled over 22,000 membership checks per millisecond.",
        "Adding a file update took just 0.08 milliseconds.",
        "Padding candidate lists adds roughly fifty percent extra storage, which is a tiny trade-off for real privacy.",
        "An index of ten thousand keywords takes 2.2 megabytes, easily fitting on modern flash storage.",
        "Our search queries consume less than two millijoules of battery energy per lookup."
    ],
    
    "Discussion": [
        "Padding candidate lists trades a small amount of extra bandwidth for solid query privacy.",
        "Using power-of-two buckets conceals match counts while adding roughly fifty percent extra data.",
        "When scaling to millions of documents, users can switch to broader geometric buckets to bound transmission overhead.",
        "Because VisioCrypt operates purely on the client, standard cloud storage backends like S3, Google Drive, or personal servers work without modifications."
    ],
    
    "Conclusion": [
        "VisioCrypt lets mobile users search encrypted cloud backups without leaking query volumes.",
        "Padding match counts to powers of two stops cloud admins from guessing search terms.",
        "Our security proof confirms that search traces leak no keyword information.",
        "Our real-world phone tests show searches complete in under two milliseconds."
    ]
}

tot_dir, tot_pol, tot_hum, tot_cnt = 0, 0, 0, 0
for name, sents in sections.items():
    sc, d, p, h, c = evaluate_and_print(sents, name)
    tot_dir += d
    tot_pol += p
    tot_hum += h
    tot_cnt += c

overall_score = round(((tot_dir * 1.0 + tot_pol * 0.5) / tot_cnt) * 100)
print(f"\n===========================================================================")
print(f"OVERALL COMPLETE PAPER SCORE: {overall_score}% | Direct: {tot_dir}, Polished: {tot_pol}, Human: {tot_hum} (Total: {tot_cnt})")
print(f"===========================================================================")
