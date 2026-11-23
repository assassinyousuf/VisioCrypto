# Phase 2B Deliverable B1: Regression Test Suite Execution Report

**Subject:** Empirical Verification of Two-Tier Authoritative Deletion Ledger & SSE Correctness  
**Status:** **VERIFIED** (21 / 21 Tests Passing, 0 Failures, 0 Regressions)  
**Location:** `IEEE_ICCIT_2026_PHASE_2B/B1_REGRESSION_TEST_RESULTS.md`  
**Test Manifest:**
- `test/authoritative_deletion_ledger_test.dart` (11 new regression tests)
- `test/sse_test.dart` (10 core baseline tests)

---

## 1. Clean Environment Test Execution Record

- **Test Runner:** Flutter Test Framework (`flutter test`)
- **Command:** `G:\_PROJECTS\flutter\bin\flutter.bat test test/authoritative_deletion_ledger_test.dart test/sse_test.dart`
- **Execution Timestamp:** `2026-11-21T02:37:55+06:00`
- **Working Directory:** `G:\_PROJECTS\visiocrypto`
- **Platform:** Windows 11 Pro 64-bit (Build 26300), AMD/Intel x86_64 Host
- **Dart Runtime:** Dart SDK 3.9.2 (stable, x64)
- **Exit Code:** `0` (Success)
- **Execution Duration:** $1.4$ seconds (compilation + runtime execution)
- **Total Test Cases Executed:** **21**
- **Passing Cases:** **21**
- **Failing Cases:** **0**

---

## 2. Detailed Test-by-Test Verification Matrix

| # | Group | Test Case Name | Mechanism Evaluated | Observed Output | Status |
| :-: | :--- | :--- | :--- | :---: | :---: |
| **1** | Core & Crypto | `Tombstone cryptographic HMAC creation and verification` | HMAC-SHA256 authentication of tombstone fields; rejection of wrong keys and tampered IDs | PASSED | **VERIFIED** |
| **2** | Core & Crypto | `Active documents vs Deleted documents: accurate classification` | Correct boolean categorization of active vs deleted files across multiple keywords | PASSED | **VERIFIED** |
| **3** | Core & Crypto | `Zero False Exclusions: Bloom Filter collisions resolved` | Saturated 64-bit filter producing false-positive collisions against active files; Tier 2 resolves and preserves active files | PASSED | **VERIFIED** |
| **4** | Core & Crypto | `Zero False Negatives: deleted documents are never missed` | 50 deleted documents queried across multiple keywords; 100% detection rate ($FN = 0$) | PASSED | **VERIFIED** |
| **5** | Core & Crypto | `Duplicate deletion idempotency` | Re-deleting an already-deleted document updates timestamp and increments epoch without duplicating entries | PASSED | **VERIFIED** |
| **6** | Persistence | `Restart Recovery: Encrypted ledger roundtrip & filter rehydration` | Serializing ledger with AES-256-GCM, writing to disk, restarting into fresh instance, rehydrating Bloom filter | PASSED | **VERIFIED** |
| **7** | Persistence | `Corrupted or Tampered Ledger: Triggers LedgerCorruptedException` | Flipping ciphertext bits on disk triggers GCM authentication failure; system throws `LedgerCorruptedException` | PASSED | **VERIFIED** |
| **8** | Persistence | `Missing Ledger file returns fresh empty state` | Querying non-existent ledger file returns clean 0-count ledger; active documents are never assumed deleted | PASSED | **VERIFIED** |
| **9** | Persistence | `Synchronization & Conflict Resolution: Merge remote state via LWW` | Merging two ledgers with concurrent updates; resolves conflicts via Last-Write-Wins and re-authenticates HMACs | PASSED | **VERIFIED** |
| **10** | End-to-End | `End-to-End: Indexing multiple docs, authoritatively deleting, searching` | 3 documents indexed; 1 deleted via `deleteDocument`; `searchIndex` returns exactly the 2 active documents | PASSED | **VERIFIED** |
| **11** | End-to-End | `Stale local cache / file presence independence` | Document exists on disk (`File.existsSync() == true`) but is authoritatively deleted; search correctly excludes it | PASSED | **VERIFIED** |
| **12** | Core Baseline | `HKDF-Extract and Expand produces deterministic split keys` | RFC 5869 key derivation produces identical 32-byte split keys | PASSED | **VERIFIED** |
| **13** | Core Baseline | `AES-CTR engine initialization and keystream sequence` | PointyCastle AES-CTR stream engine generates pseudorandom bytes | PASSED | **VERIFIED** |
| **14** | Core Baseline | `Different keys produce different keystreams` | Key sensitivity: 1-bit key difference diverges stream output | PASSED | **VERIFIED** |
| **15** | Core Baseline | `Tokenization removes stopwords and filters valid keywords` | Text normalization, punctuation removal, stopword filtering | PASSED | **VERIFIED** |
| **16** | Core Baseline | `Trapdoor generation is deterministic` | HMAC-SHA256 search token generation produces consistent 64-char hex strings | PASSED | **VERIFIED** |
| **17** | Core Baseline | `Encrypt and decrypt roundtrip matches original data` | Chunked AES-CTR + HMAC-SHA256 file roundtrip | PASSED | **VERIFIED** |
| **18** | Core Baseline | `Decryption fails if ciphertext is altered (AEAD integrity check)` | 1-bit alteration in middle of ciphertext triggers `SecurityException` | PASSED | **VERIFIED** |
| **19** | Core Baseline | `Indexing and searching a document retrieves matching files` | SSE index database inverted index generation and keyword search | PASSED | **VERIFIED** |
| **20** | Core Baseline | `Volume-Hiding padding pads index lists and search filters dummy` | Multi-tier power-of-two padding $\Phi(|R|)$ filters dummy matches on search | PASSED | **VERIFIED** |
| **21** | Core Baseline | `Volume-Hiding padding correctly handles result sets exceeding 32` | Padded capacity evaluation across $1, 3, 5, 33, 65, 300, 2500, 5000$ entries | PASSED | **VERIFIED** |

---

## 3. Distinction: Tested Behavior vs. Formal Guarantees

In compliance with IEEE rigorous scientific reporting standards, we explicitly demarcate between what has been **empirically validated** in the test harness and what is **formally guaranteed** under mathematical proof:

### 3.1. Tested Behavior (Empirical Testbed Bounds)
- **Zero False Exclusions:** Validated across test suites with artificially saturated Bloom filters ($m=64, k=3, n=30$), proving that collision events against active documents do not cause exclusion.
- **Zero False Negatives:** Validated across $n=50$ deletions with $100\%$ detection.
- **AEAD Integrity:** Validated across 1-bit tampering tests on encrypted ledger files and encrypted ciphertext payloads.
- **Memory Recovery:** Validated across file restart cycles and in-memory filter rehydration.

### 3.2. Formal Cryptographic Guarantees (Theoretic Bounds)
- **Zero False Exclusion Guarantee:** Formally holds for all active documents $d \in \mathbf{D}_{\text{active}}$ because the Two-Tier verification checks `_tombstones.containsKey(d)` whenever Tier 1 returns positive. Since an active document was never inserted into `_tombstones`, $\Pr[d \text{ is excluded}] = 0$.
- **Zero False Negative Guarantee:** Formally holds by the deterministic property of Bloom filters (hash functions never map an inserted element's bits to zero).
- **Tombstone Unforgeability:** Bounded by the PRF security of HMAC-SHA256: an adversary cannot forge a valid tombstone tag $\tau = \text{HMAC}(K_{\text{ledger\_auth}}, \text{doc} \parallel \text{ts} \parallel \text{epoch})$ with advantage greater than $\mathbf{Adv}_{\text{HMAC}}^{\text{prf}}(\lambda)$.
- **Ledger Confidentiality & Authenticity:** Bounded by the IND-CPA and INT-CTXT security of AES-256-GCM.
