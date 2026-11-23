# Final Claim Disposition & Defensible Resubmission Roadmap

**Subject:** Definitive Disposition Matrix for Every Manuscript Claim and Pre-Resubmission Blockers  
**Manuscript:** Paper ID 2015 ("VisioCrypt")  
**Venue:** IEEE ICCIT 2026 (29th International Conference on Computer and Information Technology)  
**Target Directory:** `IEEE_ICCIT_2026_AUDIT_CORRECTIONS/FINAL_CLAIM_DISPOSITION.md`  
**Auditor:** Senior Applied Cryptographer, Systems Engineer & IEEE Publication Specialist  
**Date:** November 2026  

---

## 1. Executive Summary

This document synthesizes the findings of the forensic audit and the Phase 2A corrections package (`IEEE_ICCIT_2026_AUDIT_CORRECTIONS/`). It provides a definitive, unvarnished disposition for every major claim made in `2015_Revised_Manuscript.tex`, `2015_Validation_Report.md`, and `README.md`.

Every claim is categorized into one of three binding dispositions:
1. **RETAIN:** The claim is fully substantiated by reproducible code, verified mathematical proof, or verified raw experimental data.
2. **REFRAME:** The conceptual claim or mechanism is valid, but the experimental scope, nomenclature, or architecture was overstated and must be honestly reframed (e.g., from physical mobile hardware measurement to reference Dart VM runtime execution; from an empirical network adversary to an analytical information-theoretic decorrelation model).
3. **RETRACT:** The claim is contradicted by the codebase, mathematically invalid, or completely unsupported by empirical evidence (e.g., ARM TrustZone hardware-backed key storage, native C/C++ mobile throughput of 310.4 MB/s, dynamic update forward privacy, and zero false document exclusion without an authoritative ledger).

---

## 2. Comprehensive Claim Disposition Matrix

| # | Manuscript / Rebuttal Claim | Original Location | Forensic Reality in Repository | Binding Disposition | Required Resubmission Action & Defensible Framing |
| :-: | :--- | :--- | :--- | :---: | :--- |
| **1** | **AES-CTR-256 + HMAC-SHA256 Chunked Streaming** | Sec. III-B, IV-A | Implemented in `CryptEngine` (`crypt_engine.dart`). 64 KB chunking, Encrypt-then-MAC, unique nonces, SHA-256 tag. | **RETAIN** | Keep existing architecture. Highlight chunked streaming as an effective defense against memory spikes on mobile devices. |
| **2** | **PointyCastle AES-256-GCM for Encrypted Posting Lists** | Sec. III-B, IV-B | Implemented in `SseEngine.encryptGcm` / `decryptGcm` (`sse_engine.dart`). Operational for candidate arrays. | **RETAIN** | Keep implementation. Accurately explain why GCM is restricted to small index payloads ($< 4$ KB). |
| **3** | **RFC 5869 HKDF Key Derivation Architecture** | Sec. III-B | Implemented in `Hkdf` (`hkdf.dart`). Derives domain-separated keys ($K_{\text{search}}, K_{\text{idx}}, K_{\text{file}}$). | **RETAIN** | Keep formal specification. Cryptographically sound and passes all test assertions. |
| **4** | **Dynamic Power-of-Two Volume-Hiding Padding ($\Phi$)** | Sec. III-C, IV-C | Implemented in `SseEngine.padFileList` and verified across sizes $1$ to $5000$ in `sse_test.dart`. | **RETAIN** | Retain mathematical definition $\Phi(R) = 2^{\lceil \log_2 |R| \rceil}$. Accurately document bucket transition leakage. |
| **5** | **Memory Zeroization in Dart** | Sec. IV-D | `_zeroize` and `Isolate.run` implemented. Clears mutable `Uint8List` byte buffers; isolates force OS memory release. | **RETAIN** | Retain with honest acknowledgment of Dart's garbage collector: mutable buffers are zeroized; immutable strings rely on isolate termination. |
| **6** | **Genuine Host Benchmark Data (Dart x64)** | Table II, Sec. VII | `raw_benchmark_results.json` contains 100 verified trials on Windows 11 Dart 3.9.2 VM. | **RETAIN** | Retain verified host metrics: AES-CTR ($54.3$ MB/s), AES-GCM ($0.71$ MB/s), Trapdoors ($230.2$ ev/ms), Bloom ($379.3$ ops/ms). |
| **7** | **Physical Multi-Tier Smartphone Evaluation (Table II)** | Table II, Sec. VII | No physical smartphones (Redmi K80, Turbo 4 Pro, Pixel 7a/Pro, S21, A14) were connected via ADB or benchmarked. | **REFRAME / REMOVE** | Retract physical hardware claims. Reframe Table II as an *Analytical Mobile Performance Projection* or replace with the verified Host Benchmark Table. |
| **8** | **Search Latency Scaling ($0.11$ ms)** | Sec. VII-A | $0.11$ ms measures only local in-memory candidate unpadding & GCM decryption of a 4-entry list, not network search. | **REFRAME** | Explicitly reframe $0.11$ ms as *client-side candidate resolution time*; acknowledge that complete cloud search latency is dominated by network RTT ($20$--$50$ ms). |
| **9** | **Timing Correlation Defense ($50.6\%$ Accuracy)** | Sec. VII-B, Fig. 2b | `timing_and_padding_experiments.py` line 87 used `np.random.choice([0, 1])` (synthetic coin flip). | **REFRAME** | Reframe from an "empirical adversarial evaluation" to an *Information-Theoretic Modeling of Epoch Batching*, proving that under ideal Poisson/Bernoulli dummy injection, Bayes error rate is bounded by $0.5$. |
| **10** | **Adaptive Security Theorem (Theorem 1)** | Sec. VI | Dynamic update proof failed because updates leak static trapdoors. However, static protocol proof is mathematically sound. | **REFRAME TO STATIC** | Restate Theorem 1 as *Adaptive Static Volume-Hiding IND-CKA2 Security*. Prove simulator $\mathcal{S}(\mathcal{L}_{\text{VH}})$ under HKDF, HMAC, and AES-GCM assumptions. |
| **11** | **ARM TrustZone / Android KeyMint Root Key Anchoring** | Sec. III-A, IV-A | Key is written as unencrypted raw plaintext bytes to `${docsDir.path}/.visiocrypt_secure_key`. KeyMint is not invoked. | **RETRACT** | Retract claim that prototype integrates with hardware KeyMint/StrongBox. State honestly: root key is managed by client runtime; hardware Keystore binding is an architectural deployment roadmap. |
| **12** | **BiometricPrompt Cryptographic Hardware Binding** | Sec. III-A | `local_auth` performs a boolean UI authentication check; it is not bound to a `CryptoObject` hardware unwrap. | **RETRACT** | Retract claim of `CryptoObject` cryptographic binding. Describe `local_auth` as a client-side user verification gate. |
| **13** | **Hardware-Accelerated Native Mobile Crypto ($310.4$ MB/s)** | Abstract, Sec. VII | No C/C++/NDK native crypto exists in `android/`. `AesCtrEngine` uses pure-Dart PointyCastle. | **RETRACT** | Retract the 310.4 MB/s native mobile throughput claim. Report the genuine pure-Dart throughput ($54.3$ MB/s) and discuss theoretical native ARM NEON acceleration ceilings. |
| **14** | **Forward Privacy in Dynamic Document Updates** | Sec. III-D, VI | `addDocumentDynamic` inserts documents under the static search trapdoor $T_w$, leaking search equality on updates. | **RETRACT** | Retract forward privacy claim. Clearly state: dynamic updates disclose keyword search-pattern equality to the server. Frame true forward-private updates (e.g., Sophos/Diana) as future work. |
| **15** | **Type-II Backward Privacy** | Sec. III-D | Client stores deletions locally in an in-memory Bloom filter; server state is unchanged. Not an outsourced backward-private scheme. | **RETRACT** | Retract Type-II backward privacy claim. Frame client-side Bloom filtering as a *Client-Side Deletion Pre-Filter*. |
| **16** | **Zero False Document Exclusion (Lemma 1)** | Sec. V, Lemma 1 | Bloom filter collisions silently drop active documents (line 350 drops matches without checking an authoritative ledger). | **RETRACT (Until Repaired)** | Retract Lemma 1 in its current form. Either implement the Two-Tier Authoritative Ledger or state that active document exclusion is bounded by Bloom filter collision probability $p_{\text{fp}}$. |
| **17** | **Physical Mobile Battery Energy Measurements ($1.12$ mJ)** | Table II, Sec. VII | No Monsoon power monitor, hardware profiler, or `dumpsys batterystats` logs exist in repository. | **RETRACT** | Retract empirical millijoule measurements. Replace with theoretical CPU cycle / energy modeling based on standard mobile power coefficients. |

---

## 3. Explicit Inventory of Remaining Technical Blockers

Before any final edits are applied to `IEEE_ICCIT_2026_REVISION/` or resubmission files are compiled, the research team must address the following technical blockers:

### Blocker 1: Implementation of the Two-Tier Authoritative Deletion Ledger
- **Status:** **CRITICAL FUNCTIONAL BLOCKER**.
- **Issue:** Currently, line 350 of `lib/crypto/sse_engine.dart` directly excludes candidates that match the Bloom filter. In `test_bloom_exclusion.dart`, active documents were dropped.
- **Required Resolution:** Implement an in-memory authoritative deletion `Set<String>` (or local encrypted ledger) in `sse_engine.dart`. When `filter.mightContain` evaluates to true, verify whether the document ID actually exists in the deletion set. If absent, preserve the candidate.
- **Verification:** Run a regression test verifying that forced Bloom collisions do not drop active documents.

### Blocker 2: Alignment of Algorithm 1 with Implementation
- **Status:** **THEORETICAL BLOCKER**.
- **Issue:** Algorithm 1 in `2015_Revised_Manuscript.tex` includes a version counter $w \parallel v_w$ in updates, while search uses $w$. Because HMAC has no inversion, the cloud server cannot correlate them.
- **Required Resolution:** Update Algorithm 1 to match the authentic static index build protocol and practical client-side update protocol, eliminating the broken version counter.

### Blocker 3: Table II and Text Rewriting
- **Status:** **MANUSCRIPT DRAFTING BLOCKER**.
- **Issue:** Table II currently claims multi-device physical benchmarks across Redmi K80, Pixel 7 Pro, Galaxy S21, and Galaxy A14, which were not physically measured.
- **Required Resolution:** Reconstruct Table II to present the genuine Host Reference Platform empirical benchmarks (with sample sizes, standard deviations, and 95% confidence intervals), supplemented by an analytical projection model for mobile execution.

### Blocker 4: Threat Model & Security Framing Rewrite
- **Status:** **SCIENTIFIC INTEGRITY BLOCKER**.
- **Issue:** The manuscript must completely eliminate claims of hardware TrustZone root-key storage, native 310 MB/s mobile throughput, and forward privacy.
- **Required Resolution:** State the exact, unvarnished security guarantees:
  - Static Volume-Hiding SSE with power-of-two padding.
  - Provable IND-CKA2 security under Theorem 1.
  - Transparent disclosure of update leakage and Bloom filter collision mitigation.

---

## 4. Final Auditor Declaration

This completes Phase 2A (Forensic Audit Corrections and Evidence Reconciliation). 
The six required audit correction documents:
1. `FACTUAL_CORRECTIONS.md`
2. `BLOOM_REPAIR_REASSESSMENT.md`
3. `TIMING_MODEL_REASSESSMENT.md`
4. `BENCHMARK_SCOPE_REASSESSMENT.md`
5. `STATIC_SECURITY_PROOF_REASSESSMENT.md`
6. `FINAL_CLAIM_DISPOSITION.md`

have been authored and saved in `IEEE_ICCIT_2026_AUDIT_CORRECTIONS/`. 

As mandated:
- The frozen revision directory (`IEEE_ICCIT_2026_REVISION/`) remains completely untouched.
- No final PDFs have been compiled.
- No changes have been pushed to GitHub.
- Execution is now paused to present the findings and await user direction on addressing the identified blockers.
