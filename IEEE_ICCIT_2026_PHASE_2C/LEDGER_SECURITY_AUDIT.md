# Phase 2C Deliverable 1: Deletion Ledger Security & Cryptographic Audit

**Subject:** Independent Security & Cryptographic Implementation Audit of Two-Tier Authoritative Deletion Ledger  
**Status:** **APPROVED WITH EXPLICIT LIMITATIONS**  
**Location:** `IEEE_ICCIT_2026_PHASE_2C/LEDGER_SECURITY_AUDIT.md`  
**Target Codebase:**
- [`lib/crypto/deletion_ledger.dart`](file:///g:/_PROJECTS/visiocrypto/lib/crypto/deletion_ledger.dart) (Lines 1–324)
- [`lib/crypto/sse_engine.dart`](file:///g:/_PROJECTS/visiocrypto/lib/crypto/sse_engine.dart) (Lines 157–172, 338–410)

---

## 1. Executive Summary

This independent security audit evaluates the implementation of the Two-Tier Authoritative Deletion Ledger against low-level cryptographic vulnerabilities, side-channels, race conditions, crash consistency, and distributed synchronization properties.

We distinguish **Local Single-Handset Correctness** (which is fully verified and mathematically sound) from **Distributed Multi-Device Synchronization Guarantees** (which require explicit operational assumptions regarding cloud storage brokers and monotonic hardware counters).

---

## 2. Low-Level Cryptographic Security Evaluation

### 2.1. AES-GCM Nonce Uniqueness & Lifecycle
- **Implementation:** In `AuthoritativeDeletionLedger.saveToFile` (lines 218–223):
  ```dart
  final rand = Random.secure();
  final iv = Uint8List(12);
  for (int i = 0; i < 12; i++) {
    iv[i] = rand.nextInt(256);
  }
  ```
- **Auditor Evaluation:**
  - `Random.secure()` invokes the host platform's cryptographically secure pseudo-random number generator (`BCryptGenRandom` on Windows, `/dev/urandom` or `getrandom()` on Linux/Android).
  - The IV length is strictly 96 bits ($12$ bytes), matching the optimal NIST SP 800-38D recommendation for GCM mode without invoking the GHASH initialization path.
  - **Collision Probability:** Under the birthday paradox, the probability of an IV collision after $q$ ledger file encryptions under key $K_{\text{ledger\_enc}}$ is bounded by:
    $$P_{\text{collision}} \le \frac{q^2}{2^{97}}.$$
    For a heavy mobile user generating $q = 10^5$ deletions/saves over the handset lifetime, $P_{\text{collision}} \le \frac{10^{10}}{1.58 \times 10^{29}} \approx 6.3 \times 10^{-20}$ (negligible).
  - **Operational Limitation:** The current code uses randomized nonces rather than a deterministic linear counter. While compliant with NIST SP 800-38D Section 8.2.2 (which permits up to $2^{32}$ random invocations under a single key), a deterministic counter would eliminate the birthday bound entirely.
  - **Verdict:** **VERIFIED (COMPLIANT UNDER NIST SP 800-38D RANDOM NONCE BOUNDS)**.

---

### 2.2. Dual-Layer Authentication-Tag Verification
- **Implementation:**
  - *Layer 1 (Container Level):* AES-256-GCM AEAD 128-bit authentication tag verified by PointyCastle's `GCMBlockCipher.process` during `SseEngine.decryptGcm` in `loadFromFile` (lines 278–282).
  - *Layer 2 (Record Level):* Individual 256-bit HMAC-SHA256 tag $\tau = \text{HMAC}(K_{\text{ledger\_auth}}, d \parallel \text{timestamp} \parallel \text{epoch})$ verified for every tombstone in `loadFromFile` (lines 305–311) and `mergeRemote` (lines 178–182).
- **Auditor Evaluation:**
  - Any 1-bit tampering with the ciphertext container causes GCM AEAD failure and raises `LedgerCorruptedException`.
  - Even if an adversary could bypass container decryption, individual tombstones cannot be injected, forged, or modified without knowing $K_{\text{ledger\_auth}}$.
  - **Verdict:** **VERIFIED (EXCELLENT CRYPTOGRAPHIC DEFENSE-IN-DEPTH)**.

---

### 2.3. Key Derivation & Cryptographic Key Separation
- **Implementation:** In `SseEngine.deriveSseKeys` (lines 157–172):
  - Master key $K_{\text{master}}$ and salt $S$ are extracted via HKDF-Extract to produce pseudo-random key $PRK$.
  - PRK is expanded into five domain-separated 256-bit operational keys:
    - $K_{\text{search}} \gets \text{HKDF-Expand}(PRK, \text{"VisioCrypt-Search-Key"}, 32)$
    - $K_{\text{idx}} \gets \text{HKDF-Expand}(PRK, \text{"VisioCrypt-IndexVal-Key"}, 32)$
    - $K_{\text{upd}} \gets \text{HKDF-Expand}(PRK, \text{"VisioCrypt-Update-Key"}, 32)$
    - $K_{\text{ledger\_enc}} \gets \text{HKDF-Expand}(PRK, \text{"VisioCrypt-LedgerEnc-Key"}, 32)$
    - $K_{\text{ledger\_auth}} \gets \text{HKDF-Expand}(PRK, \text{"VisioCrypt-LedgerAuth-Key"}, 32)$
- **Auditor Evaluation:**
  - Under the PRF assumption of HKDF (RFC 5869), distinct domain-separation context strings guarantee computational independence across all five derived keys. Compromise of $K_{\text{search}}$ reveals zero information regarding $K_{\text{ledger\_enc}}$ or $K_{\text{ledger\_auth}}$.
  - **Verdict:** **VERIFIED (STRICT DOMAIN SEPARATION ESTABLISHED)**.

---

## 3. Systems, Concurrency & State Integrity Audit

### 3.1. Replay & Rollback Attacks (Local vs. Hardware-Enforced)
- **Vulnerability Analysis:**
  Suppose an attacker with temporary unprivileged physical access or malware possessing local filesystem read/write access replaces `ledgerFile` with an authentic, earlier version of the encrypted ledger (e.g., recorded prior to a document deletion).
  - Because the earlier ledger file was legitimately encrypted under $K_{\text{ledger\_enc}}$ with a valid GCM tag, `loadFromFile` will decrypt it successfully.
  - The client's state would roll back to the earlier epoch, resurrecting the deleted document in search results.
- **Architectural Boundary:**
  - The software ledger stores an internal monotonic counter `_currentEpoch`, but does **not** bind it to an external hardware-backed monotonic counter (e.g., Android Keystore RPMB or KeyMint rollback-resistant key storage).
  - **Explicit Limitation to State in Manuscript:** Software-level cryptographic authentication cannot prevent whole-file snapshot rollback on untrusted storage without a hardware monotonic counter or a trusted timestamp server.
  - **Verdict:** **PARTIALLY VERIFIED (SECURE AGAINST TAMPERING; VULNERABLE TO LOCAL DISK ROLLBACK WITHOUT HARDWARE RPMB)**.

---

### 3.2. Concurrency, Race Conditions & Event-Loop Thread Safety
- **Implementation:**
  - In Dart, user code executes within a single-threaded isolate event loop.
  - Mutations to `_tombstones` and `_filter` in `markDeleted` are synchronous.
  - Searches reading from `_tombstones` execute synchronously within isolate turns.
  - File saving in `saveToFile` uses unique temporary files (`${file.path}.tmp_${rand.nextInt(1000000)}`) with `flush: true` followed by atomic rename (`tempFile.rename(file.path)`).
- **Auditor Evaluation:**
  - Multiple asynchronous calls to `saveToFile` do not corrupt disk state because each operates on an isolated temporary file, and filesystem renames are atomic on NTFS, ext4, and APFS.
  - There is no race window where an unencrypted or half-written ledger file can be read by `loadFromFile`.
  - **Verdict:** **VERIFIED (CRASH-RESISTANT ATOMIC FILE REPLACEMENT)**.

---

### 3.3. Crash Consistency (Index Updates vs. Deletion Ledger)
- **Scenario:** The client application terminates abnormally (power loss, OS OOM kill) between an index update and a deletion ledger write:
  - *Case 1 (Tombstone persisted, cloud file lingers):* Safe. The local client suppresses the document from search results. The lingering cloud ciphertext creates storage bloat, not a privacy leak.
  - *Case 2 (Cloud deletion acknowledged, tombstone not yet persisted to disk):* If the local ledger is not saved, rebooting causes the local ledger to lack the tombstone. However, because the cloud file was deleted, cloud search returns $\bot$ or an empty payload for that document.
- **Verdict:** **VERIFIED (FAIL-SAFE DIRECTION)**.

---

### 3.4. Distributed Correctness & Device Migration
- **Multi-Device Synchronization:**
  - In `mergeRemote`, tombstones are merged via Last-Write-Wins (LWW) based on `timestamp` and `epoch`.
  - If Device A and Device B delete different files offline, merging their ledgers correctly unions the deletion sets without data loss.
  - If both devices delete the same file with different timestamps, the later deletion record is retained.
- **Distributed Limitation:**
  - The current codebase implements the client-side merge logic (`mergeRemote`), but does **not** include an active cloud sync protocol or network coordinator. If two devices attempt to write conflicting encrypted ledger blobs directly to a naive cloud bucket, the last write will overwrite the remote file container unless an append-only log or CRDT backend is deployed.
  - **Verdict:** **VERIFIED (CLIENT-SIDE MERGE CORRECT; DISTRIBUTED NETWORK SYNC PROTOCOL IS SCOPED AS ARCHITECTURAL ROADMAP)**.

---

## 4. Auditor Classification & Recommendations

| Security Dimension | Technical Property | Forensic Status |
| :--- | :--- | :---: |
| **Nonce Security** | 96-bit CSPRNG random nonces; birthday bound $< 10^{-19}$ | **VERIFIED** |
| **Authentication Integrity** | Dual-layer: 128-bit AES-GCM + 256-bit HMAC-SHA256 | **VERIFIED** |
| **Key Separation** | RFC 5869 HKDF domain-separated keys | **VERIFIED** |
| **Atomic Persistence** | Crash-safe atomic rename via temporary staging | **VERIFIED** |
| **Corrupted State Rejection** | Throws `LedgerCorruptedException`; active files protected | **VERIFIED** |
| **Rollback Resistance** | Lacks hardware RPMB counter binding | **LIMITATION IDENTIFIED** |
| **Distributed Multi-Device Sync** | Client merge verified; cloud transport not implemented | **LIMITATION IDENTIFIED** |

### Final Audit Verdict:
**APPROVED WITH EXPLICIT LIMITATIONS.** The Two-Tier Authoritative Deletion Ledger is cryptographically robust and solves the false-exclusion vulnerability on the mobile client. The manuscript must explicitly disclose that rollback resistance against local disk snapshot replacement requires hardware monotonic counters (RPMB/KeyMint).
