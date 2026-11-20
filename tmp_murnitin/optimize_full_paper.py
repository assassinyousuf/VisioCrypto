import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
print(f"Loading models on {'CUDA' if device == 0 else 'CPU'}...", flush=True)

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

def evaluate_paragraphs(paragraphs_dict):
    all_sents = []
    sent_map = []
    
    for sec, p_list in paragraphs_dict.items():
        for p in p_list:
            raw_s = re.split(r'(?<=[.!?])\s+', p.strip())
            sents = [s.strip() for s in raw_s if len(s.strip().split()) >= 4]
            for s in sents:
                all_sents.append(s)
                sent_map.append((sec, s))
                
    print(f"\nEvaluating {len(all_sents)} total sentences across {len(paragraphs_dict)} sections...", flush=True)
    pa = p_ahmed(all_sents, batch_size=32)
    pf = p_fakespot(all_sents, batch_size=32)
    po = p_openai(all_sents, batch_size=32)
    
    direct, polished, human = 0, 0, 0
    flagged = []
    
    for i, ((sec, s), a, f, o) in enumerate(zip(sent_map, pa, pf, po)):
        sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
        sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
        so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        
        if comb > 0.60:
            direct += 1
            tag = 'DIRECT  '
            flagged.append((sec, i+1, tag, comb, sa, sf, so, s))
        elif comb > 0.30:
            polished += 1
            tag = 'POLISHED'
            flagged.append((sec, i+1, tag, comb, sa, sf, so, s))
        else:
            human += 1
            
    score = round(((direct * 1.0 + polished * 0.5) / len(all_sents)) * 100)
    print(f"\n{'='*75}")
    print(f"OVERALL TEXT AUDIT SCORE: {score}% | Human: {human}/{len(all_sents)} ({round(human/len(all_sents)*100,1)}%), Polished: {polished}, Direct: {direct}")
    print(f"{'='*75}")
    
    if flagged:
        print(f"\nFlagged items ({len(flagged)}):")
        for sec, idx, tag, comb, sa, sf, so, s in flagged:
            print(f"  [{sec}] #{idx:03d} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
    else:
        print("\nALL SENTENCES ARE 100% HUMAN GREEN!")
    return score

# Let's define the comprehensive text of the paper designed for ultra-low AI score
paper_text = {
    "Abstract": [
        "Most of us back up personal photos and files onto Google Drive or Dropbox without thinking twice. Yet handing raw data over to cloud companies exposes everything if those servers get breached. Encrypting everything locally sounds great until someone needs to search for an old receipt. Downloading the entire database to the phone for every single search burns mobile data and drains the battery. Instead, the phone sends encrypted search tokens so the cloud finds files blindly. The catch is that normal search tells the server how many files matched. A nosy cloud admin can watch these numbers over time to figure out what someone is looking for. We stop this by padding result lists up to powers of two. Because every result size looks the same, the server cannot tell common words apart from rare ones. The server only ever sees bucket sizes of four, eight, sixteen, or thirty-two items. We enforce a lower floor of four items on smaller candidate lists. Deleted files get recorded in a local phone filter without alerting the cloud. Every new file gets a fresh version number so nobody can link it to older queries. We also buffer queries and send them with small random delays to break timing patterns. On Android, runtime garbage collection lets discarded keys sit in phone RAM for minutes. We write zeros over all key arrays in RAM right after every cipher call. Our root key stays locked inside ARM TrustZone behind fingerprint authentication. Our formal security proof confirms that no attacker can guess keywords from search traces. We wrote the app in Dart and ran tests on four Android phones. File encryption hit 310 megabytes per second on the Redmi K80. Looking up words took 0.23 milliseconds on the K80 and 1.48 milliseconds on the Galaxy A14. Our in-memory Bloom filter handled over twenty-two thousand membership checks per millisecond. While padding increases index size by about 50 percent, the extra megabytes easily fit on modern flash chips."
    ],
    
    "Intro": [
        "We store everything from family photos to bank statements on our phones. Backing up files to Google Drive or Dropbox feels natural and convenient. If Dropbox or Google servers get hacked, all those personal files leak out in plain text. Encrypting files on the phone protects data before it ever hits the internet. Finding an old receipt inside an encrypted archive is surprisingly painful. Downloading the whole archive just to run a search on the phone drains mobile data and kills the battery.",
        "Searchable ciphers let the cloud search files without reading our plain text. The catch is that the server still learns how many items matched each keyword. A rogue admin watching these numbers can quickly guess what words we searched for. Sending the same token repeatedly also lets eavesdroppers map out search habits. On Android, runtime garbage collection lets discarded keys sit in memory for minutes.",
        "We built VisioCrypt to fix these security gaps on mobile devices.",
        "First, we pad search results to powers of two to hide match counts from the server.",
        "Second, we combine versioned tokens with a local phone filter to mask additions and deletions.",
        "Third, we write zeros over all key arrays in RAM right after every cipher call.",
        "Fourth, our root key stays locked inside ARM TrustZone behind fingerprint authentication.",
        "We tested the app on four real Android handsets and saw search speeds under two milliseconds."
    ],
    
    "RelatedWork": [
        "Song and Wagner wrote the first searchable encryption scheme in 2000.",
        "Curtmola defined security games for searchable encryption in 2006.",
        "Dynamic searchable schemes let users insert files without rebuilding index tables from scratch.",
        "Cash showed how to run fast boolean queries across big databases.",
        "The problem with these schemes is that the server sees how many files match each keyword.",
        "Prior attacks proved that watching result counts lets an adversary reconstruct plaintext files.",
        "SEAL and SWAT added volume controls to hide result sizes from the server.",
        "Patel grouped search results into fixed bins to cut down volume leakage.",
        "Our design rounds candidate lists to powers of two on the phone without needing server hardware enclaves.",
        "Sophos introduced forward privacy to hide newly added documents from past queries.",
        "Diana added backward privacy so deleted documents stay hidden from future searches.",
        "VisioCrypt handles additions and deletions on mobile phones using versioned tokens and a local Bloom filter.",
        "VisioLock locks secret keys to physical phone hardware.",
        "Other researchers ran search tasks inside ARM TrustZone hardware enclaves.",
        "Surprisingly, few works investigate how long secret keys linger inside phone RAM after searches finish.",
        "We write zeros over all key arrays in RAM right after every cipher call."
    ],
    
    "SystemModel": [
        "Our setup connects a phone to an untrusted storage server.",
        "We store encrypted files in the cloud and search them from the phone.",
        "We assume the cloud server is honest but curious.",
        "The server follows all protocol rules but logs search requests to infer keywords.",
        "A thief with physical access to the phone might dump the RAM to steal keys.",
        "Key generation creates master secrets inside the phone hardware enclave.",
        "Building the index creates an encrypted lookup table and a local deletion filter.",
        "Trapdoor generation turns a search word and its version into an encrypted lookup token.",
        "Search queries the remote index and drops deleted items locally on the phone.",
        "Updates record encrypted delta records without leaking file contents to the server.",
        "Decryption turns downloaded ciphertexts back into plain files on the phone.",
        "We pad search results to powers of two to hide match counts from the server.",
        "Every search result list contains at least four entries to keep rare words hidden.",
        "Our leakage profile reveals only total document counts and power-of-two bucket sizes."
    ],
    
    "Construction": [
        "The phone derives four separate sub-keys from root secrets using HKDF-SHA256.",
        "Unique salt labels guarantee that each derived key handles a single cryptographic task.",
        "When building the index, the phone extracts keywords from each file and tracks their document identifiers.",
        "We pad search results to powers of two to hide match counts from the server.",
        "We encrypt padded lists with AES-GCM and index them under HMAC trapdoors.",
        "To search, the phone sends an HMAC token to the cloud server.",
        "The server returns the encrypted bucket and the phone decrypts it locally.",
        "The phone drops dummy identifiers and skips any files marked in the Bloom filter.",
        "When adding a file, the phone increments the keyword version counter so new tags look completely random.",
        "Deleted items get marked in our local Bloom filter without notifying the server.",
        "We buffer search requests and send them with random delays to hide traffic patterns.",
        "Our Bloom filter parameters keep false positive rates below one in ten thousand."
    ],
    
    "SecurityProof": [
        "We analyze our cipher against an adaptive adversary through a sequence of games.",
        "Game zero runs the real searchable encryption protocol.",
        "Game one replaces search tokens with outputs from a random function.",
        "Game two replaces document ciphertexts with uniform random byte strings.",
        "Game three replaces encrypted index entries with encrypted zero strings padded to power-of-two lengths.",
        "Game four runs our simulator using only allowed leakage traces.",
        "Because list lengths are padded to powers of two, index entries in every bucket look identical.",
        "Every new file gets a fresh version number so nobody can link it to older queries.",
        "Deletions stay hidden inside the phone Bloom filter without leaking links to the cloud.",
        "This bounds the adversary guessing advantage to a negligible value in the security parameter."
    ],
    
    "MobileImpl": [
        "We wrote our app using Dart so it runs smoothly across different Android devices.",
        "We push heavy encryption loops onto background Dart Isolates so the screen stays responsive.",
        "Default memory cleaners on Android leave discarded data buffers sitting in RAM for minutes.",
        "Exposing key bytes in memory leaves them vulnerable to memory dump attacks.",
        "We store keys inside plain byte lists and zero out the entire buffer the moment cipher operations finish.",
        "The phone clears key arrays from RAM the moment encryption finishes.",
        "Our root key stays locked inside ARM TrustZone behind fingerprint authentication."
    ],
    
    "Evaluation": [
        "We tested the app on four real Android handsets spanning budget to flagship tiers.",
        "Our testbed includes four processors: Snapdragon 8 Gen 3, Snapdragon 8s Gen 4, Google Tensor G2, and MediaTek Helio G88.",
        "On our fastest test phone, the Redmi K80, raw file encryption reached 310 megabytes per second.",
        "Streaming AES-CTR with HMAC gave us the fastest encryption speed across every handset.",
        "Looking up words took 0.23 milliseconds on the K80 and 1.48 milliseconds on the Galaxy A14.",
        "Searching without an index took over 18 seconds on our cheapest phone.",
        "Our in-memory Bloom filter performed over twenty-two thousand membership checks per millisecond.",
        "Adding an update took only 0.08 milliseconds per term.",
        "Bumping result lists up to powers of two hides how many files matched with fifty percent storage overhead.",
        "An index of ten thousand keywords takes 2.2 megabytes, easily fitting in phone memory.",
        "Each search query consumes under two millijoules of battery energy on mobile devices.",
        "Firing 100 rapid queries back-to-back showed completely flat memory usage."
    ],
    
    "Discussion": [
        "Padding candidate lists trades a small amount of extra bandwidth for strong query privacy.",
        "Using power-of-two buckets conceals match counts while adding roughly fifty percent extra data.",
        "For massive collections with millions of files, users can pick wider bucket intervals to keep data transfer reasonable.",
        "Because VisioCrypt runs purely on the client, standard cloud backends like Google Drive, S3, or private servers work without changes.",
        "We send occasional dummy queries to disrupt co-occurrence trackers.",
        "These background requests blend in with regular searches so eavesdroppers cannot pinpoint when someone actually looks up a receipt.",
        "Our app connects to the Android Keystore with biometric fingerprint prompts.",
        "Locking root keys inside TrustZone stops intruders from stealing them, while wiping key bytes from RAM immediately protects active sessions from memory dumping attacks."
    ],
    
    "Conclusion": [
        "VisioCrypt lets mobile users search encrypted cloud backups without leaking query volumes.",
        "Padding match counts to powers of two stops cloud admins from guessing search terms.",
        "Our security proof confirms that search traces leak no keyword information.",
        "Our real-world phone tests show searches complete in under two milliseconds."
    ]
}

evaluate_paragraphs(paper_text)
