import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from transformers import pipeline

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

def score_sentences(sents, title=""):
    if not sents:
        return 0, []
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
    print(f"[{title}] Score = {score}% | Direct: {direct}, Polished: {polished}, Human: {human} (Total: {len(sents)})")
    return score, results

# Test Section by Section candidate humanized text
sections = {
    "Abstract": """
    Most of us back up personal photos and files onto Google Drive or Dropbox without thinking twice.
    Yet handing raw data over to cloud companies exposes everything if those servers get breached.
    Encrypting everything locally sounds great until someone needs to search for an old receipt.
    Downloading the entire database to the phone for every single search burns mobile data and drains the battery.
    Instead, the phone sends encrypted search tokens so the cloud finds files blindly.
    The catch is that normal search tells the server how many files matched.
    A nosy cloud admin can watch these numbers over time to figure out what someone is looking for.
    We stop this by padding result lists up to powers of two.
    Because every result size looks the same, the server cannot tell common words apart from rare ones.
    The server only ever sees bucket sizes of four, eight, sixteen, or thirty-two items.
    We enforce a lower floor of four items on smaller candidate lists.
    Deleted files get recorded in a local phone filter without alerting the cloud.
    Every new file gets a fresh version number so nobody can link it to older queries.
    We also buffer queries and send them with small random delays to break timing patterns.
    On Android, runtime garbage collection lets discarded keys sit in phone RAM for minutes.
    We write zeros over all key buffers in RAM right after every cipher call.
    Our root key stays locked inside ARM TrustZone behind fingerprint authentication.
    Our formal security proof confirms that no attacker can guess keywords from search traces.
    We wrote the app in Dart and ran tests on four Android phones.
    File encryption hit 310 megabytes per second on the Redmi K80.
    Looking up words took 0.23 milliseconds on the K80 and 1.48 milliseconds on the Galaxy A14.
    Our in-memory Bloom filter handled over twenty-two thousand membership checks per millisecond.
    While padding increases index size by about 50 percent, the extra megabytes easily fit on modern flash chips.
    """,
    
    "Intro": """
    Smartphones hold our most private personal photos, medical notes, and financial receipts.
    Most people back up these files to cloud servers like Google Drive or Dropbox for convenience.
    However, storing plain files on remote servers creates huge privacy risks if those servers suffer a breach.
    Encrypting files on the phone before uploading keeps data private from outside eyes.
    The trouble starts when you need to search your files for a specific keyword.
    Pulling down thousands of encrypted files just to search locally burns mobile data and drains the battery.
    Searchable encryption lets the remote server find matching files using encrypted tokens without seeing plain text.
    Yet standard searchable schemes still leak the exact number of matching files for every search term.
    A rogue cloud administrator can record these match counts to guess what users are searching for.
    Sending identical search tokens also lets observers track repeated searches and build user profile graphs.
    Furthermore, mobile app runtimes often leave temporary cryptographic keys sitting in memory until garbage collection kicks in.
    To fix these real-world problems, we built VisioCrypt for mobile cloud storage.
    Our system rounds candidate search lists to powers of two, hiding file counts behind uniform bucket sizes.
    We also buffer search queries on the phone and send them with random delays to break traffic timing.
    All root keys are stored inside ARM TrustZone hardware and protected by fingerprint biometric prompts.
    We explicitly overwrite temporary key buffers with zeros immediately after every cryptographic operation.
    We test VisioCrypt on four physical Android phones ranging from budget devices to flagship hardware.
    """,
    
    "RelatedWork": """
    Early searchable symmetric schemes allowed keyword lookups over static file collections.
    Later research introduced dynamic updates so users could add new files without leaking past queries.
    Researchers also scaled searchable encryption to handle multi-keyword and boolean searches efficiently.
    However, classical systems leak the number of matching documents returned by each query.
    Prior attacks showed that observing result counts lets an adversary reconstruct encrypted databases quickly.
    Volume-hiding techniques group candidate list sizes into preset bins to reduce this statistical leakage.
    Our scheme applies power-of-two padding on the mobile client to eliminate volume leakage with low overhead.
    Other projects have explored hardware enclaves like ARM TrustZone to protect search indices.
    Even so, little attention has been paid to key lifetime in mobile garbage-collected heaps.
    VisioCrypt bridges this gap by combining hardware key storage with active memory zeroization.
    """,
    
    "SystemModel": """
    Our system consists of a mobile client and an untrusted cloud storage server.
    The client owns a collection of encrypted files and wants to search them remotely.
    We assume the cloud server is honest-but-curious.
    The server follows all protocol rules correctly but tries to learn keyword plaintexts from stored records and query traffic.
    A local adversary might also attempt to dump device memory after the phone gets stolen.
    To protect data against both threats, our scheme uses six core operations.
    Key generation creates a master key inside the hardware enclave.
    Index building turns local files into an encrypted keyword map and initializes a deletion filter.
    Trapdoor computation creates a one-way token for a given search keyword and version number.
    Search evaluates the trapdoor against the remote index and filters out deleted items.
    Update appends encrypted delta records for newly added or deleted files.
    Decryption restores matching ciphertexts back to original plaintexts on the phone.
    We pad every matching list to powers of two with a minimum size of four entries.
    This guarantees that search results always fall into uniform bucket sizes.
    """,
    
    "Construction": """
    VisioCrypt derives four separate sub-keys from the master key using HKDF-SHA256 with domain separation strings.
    One key encrypts file contents, the second computes search tokens, the third protects index payloads, and the fourth secures update deltas.
    When building the index, the client tokenizes all files and maps each keyword to its matching file identifiers.
    Each file list is padded with dummy values up to the next power of two.
    The padded list is encrypted with AES-GCM-256 and stored under an HMAC-SHA256 search token.
    To search, the client generates a search trapdoor and sends it to the cloud.
    The server looks up the encrypted bucket and returns it to the phone for local decryption.
    The phone unpacks the list, removes dummy identifiers, and checks the local Bloom filter to drop deleted records.
    When adding a new file, the client increments the keyword version counter to produce a fresh update tag.
    When deleting a file, the client inserts the keyword and file identifier into the local Bloom filter.
    To prevent traffic analysis, our client queues search requests and sends them at randomized intervals.
    If the queue is empty, the client can emit dummy queries to keep network traffic indistinguishable.
    """,
    
    "SecurityProof": """
    We analyze the security of VisioCrypt against adaptive chosen-keyword attacks under our volume-hiding leakage profile.
    Our security model guarantees that the cloud server learns nothing beyond search equality and padded result lengths.
    We prove this theorem using a sequence of four indistinguishable hybrid games.
    In the first game, we replace search tokens and versioned update tags with random pseudo-random function outputs.
    In the second game, we substitute file ciphertexts with random byte strings of equal length.
    In the third game, we replace encrypted index payloads and update records with encryptions of zeros.
    Because candidate lists are padded to powers of two, index payloads in all buckets look identical.
    Forward privacy holds because each file addition uses an incremented version counter that cannot be linked to prior searches.
    Backward privacy holds because deletions are tracked in the local Bloom filter without alerting the cloud.
    The total advantage of any polynomial-time adversary is bounded by the security of HMAC-SHA256, AES-CTR, AES-GCM, and the filter false positive rate.
    """,
    
    "MobileImpl": """
    We implemented VisioCrypt as a cross-platform mobile library in Dart.
    To prevent the smartphone interface from freezing during heavy cryptographic work, we run indexing inside background Dart Isolates.
    The isolate derives sub-keys, tokenizes files, encrypts payloads with AES-GCM, and builds the search map.
    Managed mobile runtimes do not immediately clear variables when they go out of scope.
    Instead, discarded cryptographic keys can linger in memory until the garbage collector runs.
    To prevent memory dump attacks, our implementation manages all secret keys as contiguous byte arrays.
    Immediately after each cryptographic operation completes, our code calls fillRange to overwrite the key buffer with zeros.
    This wipes the key material from physical phone RAM before the memory gets recycled.
    The master key remains permanently locked in ARM TrustZone storage behind biometric authentication.
    """,
    
    "Evaluation": """
    We benchmarked VisioCrypt across four physical Android smartphones spanning different performance tiers.
    Our testbed includes a flagship Redmi K80, a high-performance Redmi Turbo 4 Pro, a mid-range Google Pixel 7a, and a budget Samsung Galaxy A14.
    On the Redmi K80, VisioCrypt reached a file encryption throughput of 310 megabytes per second using AES-CTR-256 with HMAC verification.
    Across an index of ten thousand keywords, searching took 0.23 milliseconds on the Redmi K80 and 1.48 milliseconds on the budget Galaxy A14.
    In contrast, scanning unindexed files linearly took over 18 seconds on the budget phone.
    Our in-memory Bloom filter performed over 22,000 membership checks per millisecond.
    Logging an incremental update took only 0.08 milliseconds per keyword.
    Padding result lists to powers of two added approximately 50 percent storage overhead.
    For an index of ten thousand keywords, the total padded index was 2.2 megabytes, which easily fits in phone memory.
    """
}

for name, text in sections.items():
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if len(s.strip().split()) >= 4]
    score, _ = score_sentences(sents, name)
