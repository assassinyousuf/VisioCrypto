# VisioCrypt — Comprehensive Project Audit & Reviewer Response Mapping
**Paper ID:** 2015  
**Manuscript Title:** *VisioCrypt: A TEE-Anchored Client-Side Searchable Encryption Scheme with Dynamic Volume-Hiding Padding for Mobile Cloud Storage*  
**Venue:** 29th International Conference on Computer and Information Technology (IEEE ICCIT 2026)  
**Decision:** CONDITIONALLY ACCEPTED (Major Revision)  
**Audit Date:** November 2026  

---

## 1. Executive Summary & Workspace Inventory

A complete technical audit of the VisioCrypt project workspace (`g:\_PROJECTS\visiocrypto`) was performed. The repository contains a complete, working client-side searchable symmetric encryption (SSE) mobile framework built in Dart and Flutter, alongside academic LaTeX manuscripts, benchmarking harnesses, and evaluation artifacts.

### Workspace Asset Breakdown

| Directory / File | Type & Language | Status / Content Description |
| :--- | :--- | :--- |
| `lib/crypto/sse_engine.dart` | Dart (Pure Cryptographic Core) | **Implemented**: Inverted index creation, HKDF-SHA256 key derivation, HMAC-SHA256 trapdoor generation, AES-256-GCM encrypted index payloads, Bloom filter membership verification, dynamic versioned update logging, and volume-hiding padding. |
| `lib/crypto/crypt_engine.dart` | Dart (AEAD File Engine) | **Implemented**: Encrypt-then-MAC (EtM) streaming file encryption combining AES-CTR-256 with HMAC-SHA256, chunked processing, constant-time verification, and `zeroize()` buffer overwriting. |
| `lib/crypto/hkdf.dart` | Dart (KDF Core) | **Implemented**: RFC 5869 compliant HKDF-Extract and HKDF-Expand primitives using SHA-256. |
| `lib/crypto/benchmark.dart` | Dart (Benchmark Suite) | **Implemented**: Synthetic harness measuring throughput of AES-CTR, AES-GCM, trapdoor generation rate, Bloom filter verification, and index construction. |
| `lib/screens/` & `widgets/` | Dart / Flutter UI | **Implemented**: Mobile user interface for file selection, indexing, encrypted document search, biometric authentication gating (`local_auth`), and keystream visualization. |
| `test/sse_test.dart` | Dart / Flutter Test | **Verified**: 10 unit and integration tests validating HKDF key separation, AES-CTR keystream uniqueness, tokenization, deterministic trapdoors, AEAD integrity verification, index search, and volume-hiding padding. |
| `writing_paper/paper_ieee.tex` | LaTeX (`IEEEtran.cls`) | **Original Draft**: 6-page double-blind conference paper. Suffered from colloquial phrasing (introduced to lower AI-detector scores), pre-rendered PNG graphics instead of native LaTeX tables/equations, and several imprecise security claims. |
| `writing_paper/references.bib` | BibTeX | **Literature Base**: 23 citations covering SSE, leakage attacks, and hardware security. Requires corrections regarding Song et al. citations, formal SSE definitions, and expanded comparative literature. |
| `android/` | Android Gradle / Kotlin | **System Infrastructure**: Standard Flutter embedding (`MainActivity.kt: FlutterFragmentActivity`). Biometric gating via `local_auth`. Hardware-backed KeyMint/StrongBox root key storage occurs via Android Keystore APIs; does NOT contain a custom C/C++ TrustZone driver. |

---

## 2. Implemented vs. Simulated vs. Proposed Architectural Elements

To ensure scientific defensibility, we rigorously distinguish what is genuinely implemented in code from what is simulated or proposed as architectural design:

| Architectural Component | Implementation Status | Technical Reality in Codebase | Scientific Alignment in Revised Paper |
| :--- | :---: | :--- | :--- |
| **AES-256-GCM Index Payloads** | **Fully Implemented** | Uses PointyCastle `GCMBlockCipher(AESEngine())` with 96-bit random IVs for small encrypted posting lists in `sse_engine.dart`. | Formally specified as the primary AEAD scheme for index storage. |
| **AES-CTR-256 + HMAC-SHA256 File Cipher** | **Fully Implemented** | Implemented in `crypt_engine.dart` as chunked Encrypt-then-MAC (EtM) with HKDF domain separation. | Explicitly defended as the mobile streaming storage format to prevent OOM when handling multi-hundred-megabyte files in limited mobile RAM. |
| **HKDF Key Separation** | **Fully Implemented** | RFC 5869 extract-and-expand with unique domain labels (`VisioCrypt-Search-Key`, `VisioCrypt-IndexVal-Key`, `VisioCrypt-Update-Key`, etc.). | Full mathematical specification in Section IV; assumption in Game Hopping security proof. |
| **Volume-Hiding Padding** | **Fully Implemented** | Geometric power-of-two padding with floor of 4. Previously capped at 128; now updated to support arbitrary result sets up to $N_{\max} = 4096$ and multi-bucket chunking. | Formally defined padding policy $\Phi(R)$ in Section IV with leakage profile $\mathcal{L}_{\text{dyn-VH}}$. |
| **Bloom Filter Deletion Accelerator** | **Fully Implemented** | 4-hash SHA-256 double hashing filter (`SseBloomFilter`). | Formally proven as a *negative candidate accelerator* rather than an authoritative exclusion filter, preventing false document exclusions. |
| **Transient Memory Zeroization** | **Implemented (Best-Effort)** | `_zeroize(Uint8List)` calls `fillRange(0, len, 0)` on byte buffers immediately after cryptographic execution. | Explicitly documented as *best-effort userland zeroization*; acknowledges Dart VM garbage collection and immutable String/ByteData limitations. |
| **ARM TrustZone / Android Keystore** | **Architectural / API-Level** | Android `local_auth` biometric prompt gates user access; standard Android Keystore API provides hardware-backed key anchoring where KeyMint/StrongBox is present. | Accurately scoped: root key lifecycle is rooted in Android Keystore (KeyMint/StrongBox), while operational cryptographic evaluation runs in userland Dart VM. |
| **Query Decorrelation & Timing Delays** | **Implemented** | `QueryDecorrelationPool` in `sse_engine.dart` queues queries and injects dummy trapdoors. | Rigorously analyzed: random delays alone are proven vulnerable to timing correlation; batching into discrete epochs and dummy trapdoors provide genuine decorrelation. |

---

## 3. Comprehensive Mapping of Reviewer Comments & Required Actions

### Reviewer #1 Comments (10 Items)

| ID | Reviewer #1 Concern | Root Cause in Original Submission | Required Technical / Editorial Action | Section / Deliverable Impact |
| :---: | :--- | :--- | :--- | :--- |
| **R1.1** | **Search-token leakage profile** | Abstract and Section V claimed absolute zero leakage ("search tokens leak nothing to attackers"). | 1. Formally define search pattern $sp(w)$, access pattern $ap(w)$, and volume leakage $\lceil \log_2 \|R(w)\| \rceil$.<br>2. Provide formal leakage function $\mathcal{L}_{\text{dyn-VH}} = (\mathcal{L}_{\text{setup}}, \mathcal{L}_{\text{search}}, \mathcal{L}_{\text{update}})$.<br>3. Provide simulation-based security definition ($\mathcal{L}_{\text{dyn-VH}}$-IND-CKA2) with simulator $\mathcal{S}$ and game transitions. | Section III.D, Section V, Theorem 1, Response Doc R1.1 |
| **R1.2** | **Result sets exceeding 32 entries** | Manuscript claimed server only ever sees bucket sizes of $\{4, 8, 16, 32\}$ without addressing large result sets. | 1. Implement multi-tiered power-of-two policy up to $N_{\max} = 4096$ with multi-bucket chunking for $n > 4096$.<br>2. Formally analyze bucket transition leakage when updates trigger $2^k \to 2^{k+1}$.<br>3. Benchmark and plot padding expansion and storage inflation. | `sse_engine.dart`, Section IV.B, Fig. 2, Table V, Response Doc R1.2 |
| **R1.3** | **Cryptographic architecture consistency** | Manuscript mixed AES-CTR+HMAC and AES-GCM without explaining key separation or architectural rationale. | 1. Clarify dual-layer design: AES-256-GCM for encrypted index posting lists; chunked AES-CTR-256 + HMAC-SHA256 (EtM) for large streaming file storage to avoid mobile RAM OOM.<br>2. Formally document HKDF domain separation strings, nonce uniqueness (96-bit random IV for GCM, 128-bit counter for CTR), and constant-time tag validation. | Section IV.A, Section IV.D, Response Doc R1.3 |
| **R1.4** | **RAM zeroization in Dart/Flutter** | Unqualified claim of complete memory erasure via byte wiping. | 1. Analyze Dart memory model: mutable `Uint8List` vs immutable `String` and `utf8.encode()` buffers.<br>2. Note that garbage-collected runtimes (ART/Dart VM) can retain orphan copies.<br>3. Frame `_zeroize()` as best-effort defense-in-depth, emphasizing why master keys must remain anchored in hardware Keystore. | Section V.B, Listing 1, Response Doc R1.4 |
| **R1.5** | **ARM TrustZone / Android Keystore scoping** | Conflated standard Android Keystore / Biometrics with verified custom TrustZone code. | 1. Formally define root key lifecycle: KeyMint/StrongBox hardware key generation (`PURPOSE_DERIVE_KEY`), biometric authorization gating via `BiometricPrompt` (`CryptoObject`), and transient session key wrapping.<br>2. Clarify hardware/software boundary: hardware stores master root; Dart VM in Normal World executes SSE indexing. | Section III.A, Section V.A, Response Doc R1.5 |
| **R1.6** | **Bloom filter false-positive correctness** | Unclear whether false positives cause legitimate files to be permanently excluded from search results. | 1. Provide exact mathematical false-positive derivation: $p \approx (1 - e^{-k n / m})^k$.<br>2. Formally prove correctness: Bloom filter serves solely as a negative lookup accelerator. A positive match triggers local inverted index / version verification, ensuring zero false document exclusions. | Section IV.C, Section V.C, Response Doc R1.6 |
| **R1.7** | **Random query delays vs. timing attacks** | 10–50 ms random delays claimed to prevent timing attacks. | 1. Prove mathematically that i.i.d. random delays $U(a, b)$ can be averaged out by an adversary observing $M$ repeated queries ($\text{Var}(\bar{X}) = \sigma^2 / M$).<br>2. Detail `QueryDecorrelationPool` with fixed epoch batching and dummy query injection (`__DUMMY_QUERY__`).<br>3. Conduct timing correlation experiment and report measured adversary success. | Section IV.E, Section VI.D, Response Doc R1.7 |
| **R1.8** | **Device portability & testbed details** | Four test devices lacked complete technical hardware specifications. | 1. Formally document testbed: Redmi K80 (Snapdragon 8 Gen 3, 16GB, Android 15), Pixel 7 Pro (Google Tensor G2 + Titan M2, 12GB, Android 14), Galaxy S21 (Exynos 2100, 8GB, Android 13), Galaxy A14 (MediaTek Helio G80, 4GB, Android 13).<br>2. Document cryptographic hardware accelerators (ARMv8-A Crypto Extensions, KeyMint vs Keymaster).<br>3. Explicitly acknowledge sample limitations. | Section VI.A, Table II, Response Doc R1.8 |
| **R1.9** | **Benchmarking methodology rigor** | Raw numbers reported without statistical distributions, warm-ups, or confidence intervals. | 1. Establish rigorous benchmarking protocol: $N = 100$ independent trials, 10-run warm-up procedure, reporting mean, standard deviation, median, 95% confidence intervals, and interquartile ranges.<br>2. Document mobile energy measurement methodology (per-operation battery drain via Monsoon / Battery Historian API).<br>3. Generate plots directly from measured data. | Section VI, Table III, Table IV, Figures 3-4, Response Doc R1.9 |
| **R1.10** | **Forward and backward privacy formalization** | Claims of forward/backward privacy lacked formal definitions and update protocol specifications. | 1. Formally define update protocol ($\text{Update}$ algorithm with state-versioned trapdoors and incremental delta-logging).<br>2. Evaluate against Bost CCS 2016 (Forward Privacy) and Bost et al. CCS 2017 (Backward Privacy Type-II/III).<br>3. State exact guarantees: forward privacy is achieved via monotonic version counters; backward privacy is achieved at Type-II via client-side deletion filtering. | Section III.C, Section IV.D, Section V.D, Response Doc R1.10 |

---

### Reviewer #2 Concerns (5 Items)

| ID | Reviewer #2 Concern | Root Cause in Original Submission | Required Technical / Editorial Action | Section / Deliverable Impact |
| :---: | :--- | :--- | :--- | :--- |
| **R2.1** | **Academic presentation & writing style** | Colloquial language ("nosy admin", "old receipt") was introduced to evade AI detectors; PNG images used instead of native LaTeX tables/equations. | 1. Completely rewrite manuscript using rigorous, professional IEEE academic prose.<br>2. Replace all pre-rendered PNG graphics with native, beautifully formatted LaTeX code (`booktabs` tables, `algorithmicx` pseudocode, numbered equations).<br>3. Maintain strict 6.0 page IEEE conference formatting. | Entire manuscript (`2015_Revised_Manuscript.tex`), Response Doc R2.1 |
| **R2.2** | **Systematic literature review & comparison table** | Table I was an image, lacked critical state-of-the-art schemes (Patel et al., Demertzis et al.), and lacked formal property definitions. | 1. Conduct systematic literature review of foundational (Song, Curtmola, Kamara) and dynamic/volume-hiding SSE (Bost, Demertzis SEAL, Patel DVH, SGX-SE).<br>2. Create full-width native LaTeX comparative table evaluating 10 schemes across 9 dimensions (Search Complexity, Update Complexity, Forward Privacy, Backward Privacy, Volume Hiding, Result-Size Leakage, TEE Dependency, Mobile Suitability, Dynamic Updates). | Section II, Table I, Response Doc R2.2 |
| **R2.3** | **Accurate explanation of Song et al.** | Over-simplified claim: "Song showed how to search encrypted files without decrypting them [3], [4], [13]" with conflated citations. | 1. Accurately explain the Song, Wagner, and Perrig (SWP00) construction: sequential scan over stream-cipher encrypted words using a two-layered PRF construction where client provides search tokens allowing the server to test matches without decrypting plaintexts.<br>2. Detail limitations: linear $O(N)$ scan time, no inverted index, vulnerable to statistical frequency analysis.<br>3. Fix citations: cite Song et al. (IEEE S&P 2000) exclusively for this contribution. | Section I, Section II, Response Doc R2.3 |
| **R2.4** | **Establish genuine scientific novelty** | Reviewer noted that assembling existing primitives does not automatically establish cryptographic novelty. | 1. Create Contribution-to-Evidence Table mapping each claimed novelty to existing art, VisioCrypt's specific contribution, supporting code/experiments, and security theorems.<br>2. Articulate genuine novelty: first co-designed client-side dynamic volume-hiding SSE scheme optimized for constrained mobile devices, combining hardware-anchored key derivation, multi-tiered power-of-two padding with client-side deletion acceleration, and sub-millisecond mobile search. | Section I, Section VII, Response Doc R2.4 |
| **R2.5** | **Double-blind & IEEE layout compliance** | Paper must preserve double-blind anonymity, strict 6.0 page ceiling, and IEEE conference style guidelines. | 1. Retain `Anonymous Author(s)` and third-person citations.<br>2. Maintain exact 6.0-page budget with zero overflow onto page 7.<br>3. Validate font embedding, PDF text extraction, and resolution. | `2015_Revised_Manuscript.pdf`, `submission_guide.md`, Response Doc R2.5 |

---

## 4. Execution Plan & Next Steps

1. **Experimental Benchmarking Suite**: Implement a dedicated Dart/Python experimental harness executing 100 runs per benchmark to collect empirical latency, throughput, padding overhead, Bloom filter false-positive rates, and timing correlation metrics.
2. **Comparative Literature Matrix**: Generate native LaTeX, Markdown, and CSV comparison tables comparing VisioCrypt against 9 peer schemes.
3. **Complete Manuscript Rewrite**: Draft `2015_Revised_Manuscript.tex` with native LaTeX equations, algorithms, and tables, ensuring mathematically rigorous security proofs, accurate threat models, and exact 6.0-page IEEE layout.
4. **Highlighted Manuscript**: Generate `2015_Highlighted_Manuscript.pdf` with visual revision highlights.
5. **Comprehensive Author Response**: Compile `2015_Author_Response.tex` and `.pdf` thoroughly addressing all 15 reviewer points with section references and empirical evidence.
6. **Validation Report**: Document testbed execution, compile logs, and compliance checklist in `2015_Validation_Report.md`.
