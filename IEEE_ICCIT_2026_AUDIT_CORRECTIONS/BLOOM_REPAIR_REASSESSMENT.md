# Forensic Reassessment: Bloom Filter Deletion Mechanism & Authoritative State Architecture

**Subject:** Evaluation of Deletion State, False Exclusion Vulnerability, and Authoritative Ledger Design  
**Manuscript:** Paper ID 2015 ("VisioCrypt")  
**Target Directory:** `IEEE_ICCIT_2026_AUDIT_CORRECTIONS/BLOOM_REPAIR_REASSESSMENT.md`  
**Auditor:** Senior Applied Cryptographer & Systems Auditor  
**Date:** November 2026  

---

## 1. Formal Rejection of the `File.existsSync()` Proposal

In the preliminary forensic audit (`IEEE_ICCIT_2026_FORENSIC_AUDIT/CORRECTIONS_REQUIRED.md`, Section 4.2), it was proposed that Bloom filter false exclusions could be mitigated by adding a secondary local filesystem check:
```dart
// REJECTED PROPOSAL:
if (filter.mightContain(compositeKey)) {
  if (!File(docPath).existsSync()) {
    // Treat as deleted
  }
}
```

### 1.1. Why Local File Existence is Technically Insufficient
In a client-side searchable encryption scheme designed for mobile cloud storage, `File.existsSync()` fails completely as an authoritative source of deletion truth:

1. **Remote Cloud Storage Paradigm:**
   In VisioCrypt, the primary document corpus is stored in encrypted form on an untrusted cloud server. A client mobile device frequently operates with a partial local cache or zero local document retention (streaming/fetching files on demand upon search resolution). An active, valid document indexed on the server will frequently **not exist** as a local plaintext file on the device. Testing `File.existsSync()` on such a document would evaluate to `false`, causing an active remote file to be misclassified as deleted!

2. **Multi-Device Synchronization & Migration:**
   If a user enrolls a second mobile handset (or migrates to a new device), the new handset has not downloaded the document files. Under `File.existsSync()`, every single candidate returned by the cloud would appear non-existent locally, causing total search failure.

3. **Stale Local Caches & Delayed Eviction:**
   Conversely, when a user issues a deletion command, local file eviction may be deferred (e.g., pending background sync, held in an OS trash directory, or locked by an active view process). If the local file still lingers on disk when a search executes, `File.existsSync()` evaluates to `true`, resurrecting a deleted document and violating deletion correctness.

4. **Tombstone Semantics:**
   In distributed storage, deletion is an explicit cryptographic state transition (tombstone placement), not the incidental absence of a local file descriptor.

**Conclusion:** `File.existsSync()` is fundamentally flawed and is hereby formally rejected.

---

## 2. Theoretical Analysis of Bloom Filter Error Dynamics in VisioCrypt

In VisioCrypt, the client maintains a Bloom filter $\mathbf{BF}$ of capacity $m = 8192$ bits with $k = 4$ independent hash functions. When a document $d$ containing keyword $w$ is deleted, the composite token $\tau = w \parallel \text{id}(d)$ is inserted into $\mathbf{BF}$.

During search resolution for query $w$, the cloud returns a candidate list $\mathbf{R}^*(w) = \{ \text{id}(d_1), \dots, \text{id}(d_\ell) \}$. For each candidate $\text{id}(d_i)$, the client evaluates:
$$\text{IsDeleted} = \mathbf{BF}.\text{mightContain}(w \parallel \text{id}(d_i))$$

### 2.1. The Four Operational Quadrants

| Actual Status | $\mathbf{BF}$ Decision | Outcome | Impact on System |
| :--- | :---: | :--- | :--- |
| **Deleted Document** | Positive | True Positive ($TP$) | **Correct:** Deleted file is excluded from search results. |
| **Deleted Document** | Negative | False Negative ($FN$) | **Impossible ($FN = 0$):** Bloom filters possess deterministic zero false-negative guarantee. |
| **Active Document** | Negative | True Negative ($TN$) | **Correct:** Active file is preserved and presented to user. |
| **Active Document** | Positive | False Positive ($FP$) | **DATA LOSS / SILENT EXCLUSION:** Active document is falsely dropped from search results. |

### 2.2. Mathematical Quantification of the Vulnerability
For $n_{\text{del}}$ deleted items in a filter of $m$ bits with $k$ hash functions:
$$p_{\text{fp}} = \left( 1 - \left( 1 - \frac{1}{m} \right)^{k \cdot n_{\text{del}}} \right)^k \approx \left( 1 - e^{-k n_{\text{del}} / m} \right)^k$$

For $m = 8192$, $k = 4$, and $n_{\text{del}} = 500$:
$$p_{\text{fp}} \approx 0.0022 \quad (0.22\%)$$

While $0.22\%$ appears low for an individual lookup, consider a database query returning $\ell = 100$ candidate documents. The probability $P_{\text{loss}}$ that **at least one** active document is falsely and silently hidden from the user is:
$$P_{\text{loss}} = 1 - (1 - p_{\text{fp}})^\ell = 1 - (1 - 0.0022)^{100} \approx 1 - 0.8023 = 19.77\%$$

**Forensic Finding:** In nearly **1 out of every 5 searches** returning 100 results, VisioCrypt's current implementation silently drops a legitimate, active file. Claiming "Lemma 1: Zero False Document Exclusion" on the current code is mathematically and scientifically false.

---

## 3. The Authoritative Deletion-State Mechanism: Two-Tier Ledger Architecture

To achieve provable, absolute zero false exclusion ($FP_{\text{system}} = 0$) and zero false retrieval ($FN_{\text{system}} = 0$) while preserving sub-millisecond mobile search latency, VisioCrypt must implement a **Two-Tier Authoritative Deletion Ledger**.

```
                           Candidate doc_id from Cloud
                                       │
                                       ▼
                     ┌──────────────────────────────────┐
                     │   Tier 1: Bloom Filter (RAM)     │
                     │  Fast In-Memory Pre-Filter O(1)  │
                     └─────────────────┬────────────────┘
                                       │
                    Does BF contain w || doc_id?
                                  /         \
                             NO  /           \  YES (Candidate match or FP)
                                /             \
                               ▼               ▼
                       ┌──────────────┐   ┌────────────────────────────────┐
                       │ ACTIVE FILE  │   │ Tier 2: Authoritative Ledger   │
                       │ (Guaranteed) │   │  Local Encrypted Tombstone DB  │
                       │   PRESERVE   │   └───────────────┬────────────────┘
                       └──────────────┘                   │
                                            Is doc_id in Deletion Ledger?
                                                          /   \
                                                     NO  /     \  YES
                                                        /       \
                                                       ▼         ▼
                                            ┌──────────────┐ ┌──────────────┐
                                            │ Bloom Filter │ │ AUTHORITATIVE│
                                            │False Positive│ │ DELETION     │
                                            │   PRESERVE   │ │   EXCLUDE    │
                                            └──────────────┘ └──────────────┘
```

### 3.1. Algorithmic Specification

1. **Tier 1: Fast Probabilistic Pre-Filter (In-Memory Bloom Filter $\mathbf{BF}$)**
   - Resides entirely in memory.
   - Evaluates $k = 4$ double-hashes on $w \parallel \text{doc\_id}$.
   - Execution latency: $\approx 2.6$ microseconds ($379.3$ ops/ms).
   - If $\mathbf{BF}.\text{mightContain}(w \parallel \text{doc\_id}) = \text{false}$:
     - Because $FN = 0$, the document is **provably active**.
     - Execution terminates immediately: candidate is retained without querying disk storage.

2. **Tier 2: Authoritative Deletion Ledger ($\mathbf{D}_{\text{del}}$)**
   - An authenticated, encrypted local key-value store (e.g., encrypted SQLite / Hive / serialized encrypted map) anchored to client key $K_{\text{state}}$.
   - Stores the authoritative tombstone record:
     $$\mathbf{T}_{\text{del}}[\text{doc\_id}] = (\text{timestamp}, \text{auth\_tag})$$
   - **Invoked ONLY when Tier 1 returns Positive** (which occurs on true deletions or with probability $p_{\text{fp}} \approx 0.22\%$ on active documents).
   - If $\text{doc\_id} \in \mathbf{D}_{\text{del}}$: Document is an authentic deletion $\to$ **EXCLUDE**.
   - If $\text{doc\_id} \notin \mathbf{D}_{\text{del}}$: Document is an active file that triggered a Bloom filter collision $\to$ **PRESERVE**.

### 3.2. Formal Correctness Properties

- **Theorem (System-Wide Zero False Exclusion):**
  Let $\mathbf{D}_{\text{active}}$ be the set of active documents and $\mathbf{D}_{\text{del}}$ be the authoritative deletion set such that $\mathbf{D}_{\text{active}} \cap \mathbf{D}_{\text{del}} = \emptyset$.
  For any candidate $d \in \mathbf{D}_{\text{active}}$:
  - If $\mathbf{BF}.\text{mightContain}(w \parallel \text{id}(d)) = \text{false}$, $d$ is retained.
  - If $\mathbf{BF}.\text{mightContain}(w \parallel \text{id}(d)) = \text{true}$ (a Bloom collision), the system checks $\mathbf{D}_{\text{del}}$. Since $d \notin \mathbf{D}_{\text{del}}$, the collision is resolved and $d$ is retained.
  $$\Pr[d \in \mathbf{D}_{\text{active}} \text{ is excluded}] = 0.$$

- **Theorem (System-Wide Zero False Retrieval):**
  For any deleted candidate $d \in \mathbf{D}_{\text{del}}$:
  - By the deterministic zero false-negative property of Bloom filters:
    $$\Pr[\mathbf{BF}.\text{mightContain}(w \parallel \text{id}(d)) = \text{false}] = 0.$$
  - Thus, Tier 1 always forwards $d$ to Tier 2.
  - In Tier 2, $\text{id}(d) \in \mathbf{D}_{\text{del}}$ evaluates to true with probability 1.
  $$\Pr[d \in \mathbf{D}_{\text{del}} \text{ is retained}] = 0.$$

- **Average Search Complexity:**
  Let $C_{\text{BF}}$ be the cost of a Bloom filter lookup ($O(1) \approx 2.6\ \mu\text{s}$) and $C_{\text{ledger}}$ be the cost of a local ledger lookup ($O(1) \approx 50\ \mu\text{s}$).
  For $\ell$ returned candidates with deletion fraction $\alpha = |\mathbf{R}_{\text{del}}| / \ell$:
  $$\mathbb{E}[C_{\text{search}}] = \ell \cdot \left( C_{\text{BF}} + (\alpha + (1 - \alpha) p_{\text{fp}}) \cdot C_{\text{ledger}} \right)$$
  For typical search where most candidates are active ($\alpha \approx 0$):
  $$\mathbb{E}[C_{\text{search}}] \approx \ell \cdot \left( C_{\text{BF}} + 0.0022 \cdot C_{\text{ledger}} \right) \approx \ell \cdot C_{\text{BF}} + 0.00011 \cdot \ell \cdot C_{\text{ledger}}.$$
  The ledger overhead is amortized to near-zero, preserving mobile battery and CPU cycles.

---

## 4. Lifecycle & Persistence Operations

### 4.1. Persistence Across Application Restarts
1. **Cold Boot Initialization:**
   - The in-memory Bloom filter bitset $\mathbf{BF}$ is transient.
   - Upon application launch, the client decrypts $\mathbf{D}_{\text{del}}$ using $K_{\text{state}}$.
   - The client iterates over the tombstone identifiers in $\mathbf{D}_{\text{del}}$ and reconstructs the bitset $\mathbf{BF}$ via `filter.add(w || id)` in $O(n_{\text{del}})$ time.
   - For $n_{\text{del}} = 1000$, reconstruction consumes $< 3$ ms on mobile ARM cores.
   - Alternatively, the 1024-byte bitset itself can be serialized and decrypted on boot in $< 0.1$ ms.

### 4.2. Recovery After Device Migration / Secondary Device Enrollment
1. **The Handset Migration Challenge:**
   When a user authenticates on a new smartphone, the local deletion ledger is absent.
2. **Encrypted Cloud Tombstone Synchronization:**
   - The client encrypts the tombstone ledger as an authenticated blob $C_{\text{ledger}} = \text{AES-GCM-Enc}(K_{\text{state}}, \mathbf{D}_{\text{del}})$ and syncs it to cloud metadata storage.
   - The cloud server observes only ciphertext size $|C_{\text{ledger}}|$, learning only an upper bound on total deletions (which can be padded to fixed volume tiers).
   - Upon enrolling a new handset, the user performs key recovery, downloads $C_{\text{ledger}}$, decrypts it into local storage, and initializes $\mathbf{BF}$.
   - Full document redownload is completely avoided.

---

## 5. Mandatory Implementation & Testing Mandate

> [!CRITICAL]
> **Defensibility Rule:** Zero false exclusion MUST NOT be claimed as a verified contribution in the IEEE ICCIT 2026 manuscript until:
> 1. The Two-Tier Authoritative Ledger is physically implemented in `lib/crypto/sse_engine.dart`.
> 2. A comprehensive regression test suite (verifying $0, 100, 500, 1000$ deletions and forced Bloom filter collisions) executes with $0$ active document exclusions.
> If the paper is submitted prior to implementing this architecture, Lemma 1 must be retracted and replaced with a frank discussion of Bloom filter collision probability and the planned two-tier ledger architecture.
