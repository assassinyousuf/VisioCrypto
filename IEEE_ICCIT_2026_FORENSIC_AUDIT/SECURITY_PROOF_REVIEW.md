# Independent Review of Formal Security Claims & Proofs

**Subject:** Review of Leakage Profiles, Security Games, Forward/Backward Privacy, and Theorem 1  
**Manuscript:** Paper ID 2015 ("VisioCrypt")  
**Location:** `IEEE_ICCIT_2026_FORENSIC_AUDIT/SECURITY_PROOF_REVIEW.md`  
**Reviewer Role:** Senior Theoretical Cryptographer & Searchable Symmetric Encryption (SSE) Specialist  

---

## 1. Executive Summary of Theoretical Review

The security claims in Section III-D, Section VI, and Theorem 1 of `2015_Revised_Manuscript.tex` were audited against foundational cryptographic SSE definitions (Curtmola et al. CCS 2006, Bost CCS 2016, Bost et al. CCS 2017, Patel et al. 2023).

**Major Findings:**
1. **Forward Privacy is Contradicted by Implementation:** The actual code in `addDocumentDynamic` inserts documents under the static search trapdoor $T_w$. It does not use versioned counters or PRF chains, immediately leaking the search pattern to the server during updates.
2. **Algorithm 1 Dynamic Update Protocol is Mathematically Dysfunctional:** The paper's Algorithm 1 claims updates insert under $T_{w,v} = \text{HMAC}(K, w \parallel v_w)$, but search queries under $T_w = \text{HMAC}(K, w)$. Because HMAC is a pseudo-random function without algebraic inversion, the cloud server cannot correlate $T_w$ to $T_{w,v}$. Searches will fail to return dynamically added documents.
3. **Backward Privacy Claim is Mischaracterized:** Storing deletions in a client-side in-memory Bloom filter does not constitute an outsourced Type-II backward-private SSE scheme. Furthermore, the Bloom filter false-positive rate corrupts deletion correctness.
4. **Theorem 1 Simulation Gap:** The ideal simulator $\mathcal{S}$ in Game 4 is parameterized by $\mathcal{L}_{\text{dyn-VH}}$, but the actual implementation leaks additional update-to-search correlations not included in $\mathcal{L}_{\text{dyn-VH}}$.

---

## 2. Detailed Verification of Security Claims

### 2.1. Search-Pattern and Access-Pattern Leakage
- **Formal Definition:**
  - $sp(w) = \{j \le t \mid w_j = w\}$ (reveals query equality).
  - $ap(w) = \{\text{id} \in \mathbf{R}^*(w)\}$ (reveals matching ciphertext identifiers).
- **Verification:** **VERIFIED**. The scheme uses deterministic trapdoors $T_w = \text{HMAC}(K_{\text{search}}, w)$. An adversary observing repeated searches immediately observes $sp(w)$. The decrypted posting list reveals the set of matching identifiers $ap(w)$. This leakage is standard for inverted-index SSE and is correctly formalized in $\mathcal{L}_{\text{search}}$.

---

### 2.2. Volume Leakage Function $\Phi(|R(w)|)$
- **Formal Definition:** $\Phi(|R(w)|) = 2^{\lceil \log_2 |R(w)| \rceil}$ for $|R| \le 4096$, and $\lceil |R| / 4096 \rceil \cdot 4096$ for $|R| > 4096$.
- **Verification:** **VERIFIED**. The padded candidate list size hides exact volume variances, leaking only the discrete bucket exponent $\lceil \log_2 |R(w)| \rceil$.
- **Limitation (Bucket Transition Leakage):** If document insertions push $|R(w)|$ across a power-of-two boundary ($2^k \to 2^{k+1}$), an observer sees the transition. This is accurately acknowledged in the manuscript's Discussion section.

---

### 2.3. Forward Privacy Audit
- **Formal Definition (Bost, CCS 2016):** An SSE scheme is forward private if an update query leaks no information about the keywords contained in the update, particularly whether the update matches a previously searched keyword:
  $$\mathcal{L}_{\text{update}}(\text{op}, d, \mathbf{W}_d) = (\text{op}, \text{id}(d), |\mathbf{W}_d|)$$
- **Code Audit (`lib/crypto/sse_engine.dart` lines 299–316):**
  ```dart
  for (final word in keywords) {
    final trapdoor = computeTrapdoor(word, kSearch);
    ...
    deltaUpdates.add({'trapdoor': trapdoor, ...});
  }
  ```
- **Forensic Truth:**
  - The update routine evaluates `computeTrapdoor(word, kSearch)` — the exact same static trapdoor used for searching.
  - The cloud server simply checks whether `trapdoor == previous_search_token`. If equal, the server immediately learns that the new document contains the searched keyword.
  - **Verdict:** **FORWARD PRIVACY IS COMPLETELY ABSENT IN THE IMPLEMENTATION.**

- **Algorithm 1 Protocol Audit (Paper lines 225 & 242):**
  - In Algorithm 1:
    - Search: $T_w \gets \text{HMAC}(K_{\text{search}}, w)$
    - Update: $T_{w,v} \gets \text{HMAC}(K_{\text{search}}, w \parallel v_w)$
  - **Fatal Protocol Flaw:** In Sophos (Bost 2016), forward privacy is achieved because the server evaluates a trapdoor permutation: $T^{(v)} = \pi^{-1}(T^{(v+1)})$. VisioCrypt uses standard HMAC-SHA256, which has no inversion homomorphism.
  - When the client queries $T_w$, the server searches the map $\mathbf{I}$. But the update was written under $T_{w, v_w}$!
  - $T_w \ne T_{w, v_w}$.
  - The server will find zero matching update entries. The protocol is broken.

---

### 2.4. Type-II Backward Privacy Audit
- **Formal Definition (Bost et al., CCS 2017):** Search reveals the current matching documents, the timestamps/operations of all updates on $w$, but does NOT reveal the document identifiers of deleted files.
- **VisioCrypt Mechanism:**
  - Deletions are not sent to the cloud. Instead, the client locally inserts $w \parallel \text{id}(d)$ into an in-memory Bloom filter $\mathbf{BF}$.
  - At search time, the server returns all documents ever indexed under $w$. The client filters out deletions locally.
- **Critique:**
  - This is not an outsourced backward-private SSE scheme. It is an unpadded local client-side filter.
  - If a user changes phones or logs in on a new device, the in-memory Bloom filter is lost. The new handset cannot filter deletions without downloading and rebuilding the entire state.
  - Moreover, as established in `test_bloom_exclusion.dart`, false positives in $\mathbf{BF}$ silently drop active documents.

---

### 2.5. Theorem 1 5-Game Hopping Proof Audit
- **Theorem Statement:** VisioCrypt achieves adaptive $\mathcal{L}_{\text{dyn-VH}}\text{-IND-CKA2}$ security.
- **Proof Structure Review:**
  - Game 0 to Game 1: HKDF PRF extraction assumption — sound.
  - Game 1 to Game 2: HMAC PRF security for search tokens — sound for static queries.
  - Game 2 to Game 3: AES-256-GCM IND-CPA security for index posting lists — sound for static queries.
  - Game 3 to Game 4: Simulation from $\mathcal{L}_{\text{dyn-VH}}$:
    - Simulator $\mathcal{S}$ generates random strings for $sp(w)$ and simulated payloads of size $\Phi(|R|)$.
- **Gap in Proof:** The simulation proof is valid **ONLY for static collections**. For dynamic updates, because the real scheme leaks static trapdoors during updates (or because the paper's versioned counter protocol cannot be resolved by the server), the transition fails:
  $$|\Pr[\text{Game}_3] - \Pr[\text{Game}_4]| \not\le \text{negl}(\lambda)$$
  An adversary submitting an update query on a searched keyword easily distinguishes the real game from the simulated game.

---

## 3. Required Theoretical Revisions for Resubmission

1. **Retract Universal Dynamic Forward/Backward Privacy Claims:**
   - Clearly define VisioCrypt as a **Static Volume-Hiding Searchable Symmetric Encryption Scheme** with a **Client-Side Bloom-Filter Deletion Filter**.
2. **Repair Theorem 1 Scope:**
   - Restate Theorem 1 as achieving adaptive $\mathcal{L}_{\text{VH}}\text{-IND-CKA2}$ security for static queries and client-side deletion acceleration.
3. **Fix Algorithm 1:**
   - Remove the unworkable version counter $w \parallel v_w$ from Algorithm 1, or implement a genuine trapdoor permutation/hash-chain if forward privacy is retained as a future direction.
