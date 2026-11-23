# Claim-to-Evidence Matrix: VisioCrypt (Paper ID: 2015)

This matrix systematically evaluates every major technical claim made in `2015_Revised_Manuscript.tex`, `2015_Validation_Report.md`, and `README.md` against verifiable code, scripts, raw benchmark telemetry, and literature.

**Status Legend:**
- **VERIFIED:** The claim is fully supported by reproducible code, raw data, or mathematical proof.
- **PARTIALLY VERIFIED:** The core conceptual claim or mathematical property holds, but implementation scope or nomenclature is inaccurate or overstated.
- **UNSUPPORTED:** No empirical, implementation, or mathematical evidence exists in the repository.
- **CONTRADICTED:** The actual codebase or empirical tests directly contradict the claimed property.

---

## 1. Cryptographic Primitives & Implementation

| # | Manuscript Claim | Actual Codebase Evidence | Forensic Status | Finding & Action Required |
| :-: | :--- | :--- | :---: | :--- |
| **C1** | AES-CTR-256 with HMAC-SHA256 implemented for large file encryption | `CryptEngine` in `lib/crypto/crypt_engine.dart` implements chunked (64 KB) AES-CTR with HMAC-SHA256 Encrypt-then-MAC. | **VERIFIED** | Code correctly implements chunked stream encryption with authentication tags. |
| **C2** | PointyCastle AES-GCM-256 used for encrypted index posting lists | `SseEngine.encryptGcm` and `decryptGcm` in `lib/crypto/sse_engine.dart` use PointyCastle's `GCMBlockCipher(AESEngine())`. | **VERIFIED** | GCM encryption/decryption operational for small payloads. |
| **C3** | AES-CTR-256 achieves 310.4 MB/s on mobile hardware via native hardware acceleration | `AesCtrEngine` uses PointyCastle's pure Dart `AESEngine()`. There is no C/NDK/JNI native crypto in `android/`. | **CONTRADICTED** | Pure Dart throughput is $54.29$ MB/s on Windows desktop; claims of 310 MB/s native mobile throughput are fabricated/unsupported. |
| **C4** | Pure Dart PointyCastle AES-GCM runs at $0.71$ MB/s, justifying AES-CTR+HMAC streaming | `raw_benchmark_results.json` records 100 trials of AES-GCM on host PC: mean $0.7087 \pm 0.0127$ MB/s. | **VERIFIED** | Accurately explains why PointyCastle GCM cannot stream large files in Dart without severe bottleneck. |
| **C5** | RFC 5869 HKDF-SHA256 domain-separated key derivation | `Hkdf` in `lib/crypto/hkdf.dart` and `deriveSseKeys` derive $K_{\text{search}}, K_{\text{idx}}, K_{\text{upd}}, K_{\text{file}}$. | **VERIFIED** | Deterministic extract-and-expand tests pass in `test/sse_test.dart`. |

---

## 2. Hardware Enclave & Memory Security

| # | Manuscript Claim | Actual Codebase Evidence | Forensic Status | Finding & Action Required |
| :-: | :--- | :--- | :---: | :--- |
| **C6** | Master root key anchored in ARM TrustZone / Android KeyMint / StrongBox | `_deriveMasterKey` in `lib/screens/home_screen.dart` writes/reads raw key to `${docsDir.path}/.visiocrypt_secure_key` plaintext file. | **CONTRADICTED** | Hardware enclave storage does not exist in the app; key is stored as unencrypted file on device disk. |
| **C7** | Biometric gating via `BiometricPrompt` bound to `CryptoObject` | `home_screen.dart` calls `LocalAuthentication.authenticate()` as a boolean check. No `CryptoObject` is used. | **PARTIALLY VERIFIED** | Biometric prompt exists as a UI gate, but is not cryptographically bound to hardware key unwrap. |
| **C8** | KeyInfo security level inspected across 4 physical Android tiers | `KeyInfo` API is never invoked in any Dart or Kotlin file. No device security level inspection code exists. | **UNSUPPORTED** | No code or telemetry logs device security levels. Claims in Table II are unverified assertions. |
| **C9** | Best-effort RAM zeroization via `fillRange(0, len, 0)` in worker isolates | `_zeroize` and `Isolate.run` implemented in `sse_engine.dart` and `benchmark_screen.dart`. | **VERIFIED** | Mutable `Uint8List` byte arrays are zeroized; manuscript accurately acknowledges immutable `String` GC limitation. |

---

## 3. Searchable Symmetric Encryption & Padding

| # | Manuscript Claim | Actual Codebase Evidence | Forensic Status | Finding & Action Required |
| :-: | :--- | :--- | :---: | :--- |
| **C10** | Multi-tier geometric padding policy $\Phi(R)$ rounds to power-of-two | `computePaddedCapacity` and `padFileList` in `sse_engine.dart` pad $n \in [1, 4096]$ to $2^{\lceil \log_2 n \rceil}$. | **VERIFIED** | Tested and verified across $0, 1, 3, 4, 5, 8, 32, 33, 65, 300, 4096$. |
| **C11** | Multi-bucket chunking for result sets exceeding 4096 entries | `computePaddedCapacity` pads $n=5000$ to $8192$. However, `padFileList` creates a single 8192-element list in memory. | **PARTIALLY VERIFIED** | Mathematically rounds to multiples of 4096, but does not partition into actual discrete storage or network chunks. |
| **C12** | Search resolution maintains $O(1)$ inverted index lookup scaling | `index_scaling` in `raw_benchmark_results.json` shows search latency remains $0.108$--$0.130$ ms from 100 to 5,000 keywords. | **PARTIALLY VERIFIED** | Inverted index hash lookup is $O(1)$, but full candidate unpadding/decryption is $O(\Phi(|R|))$. Claiming pure $O(1)$ search complexity is inaccurate. |
| **C13** | Storage expansion bounded to average $1.42\times$ ($\le 2.0\times$ for $n \ge 4$) | Verified mathematically and empirically in `test_padding.dart`. | **VERIFIED** | Storage inflation is mathematically bounded by definition of power-of-two rounding. |

---

## 4. Deletion Mechanism & Correctness

| # | Manuscript Claim | Actual Codebase Evidence | Forensic Status | Finding & Action Required |
| :-: | :--- | :--- | :---: | :--- |
| **C14** | Client-side Bloom filter ($m=8192, k=4$) for deletion acceleration | `SseBloomFilter` in `sse_engine.dart` implements double hashing with SHA-256. | **VERIFIED** | Bloom filter construction and empirical false-positive rate ($0.21\%$) match theoretical formula. |
| **C15** | Lemma 1: Zero false document exclusion via secondary verification | Line 350 of `sse_engine.dart` directly drops candidates matching filter. In `test_bloom_exclusion.dart`, active file was dropped. | **CONTRADICTED** | No secondary check is implemented. Bloom filter false positives cause active documents to be falsely excluded. |

---

## 5. Privacy Guarantees & Security Proof

| # | Manuscript Claim | Actual Codebase Evidence | Forensic Status | Finding & Action Required |
| :-: | :--- | :--- | :---: | :--- |
| **C16** | Forward Privacy: document updates leak zero correlation with past search tokens | `addDocumentDynamic` in `sse_engine.dart` (line 300) inserts using static `computeTrapdoor(word, kSearch)`. | **CONTRADICTED** | Updates directly expose the static search trapdoor to the server, completely violating Forward Privacy. |
| **C17** | Type-II Backward Privacy achieved | Deletions are stored only in an in-memory client Bloom filter. | **UNSUPPORTED** | Client-side deletion logging is not a server-side backward-private SSE scheme (such as Diana). |
| **C18** | Formal 5-Game Hopping Proof establishes adaptive $\mathcal{L}_{\text{dyn-VH}}\text{-IND-CKA2}$ security | Proof assumes simulator operates under $\mathcal{L}_{\text{dyn-VH}}$, but actual construction leaks static update trapdoors. | **UNSUPPORTED** | The mathematical proof describes an ideal versioned protocol, not the actual implemented code. |

---

## 6. Empirical Evaluation & Testbed

| # | Manuscript Claim | Actual Codebase Evidence | Forensic Status | Finding & Action Required |
| :-: | :--- | :--- | :---: | :--- |
| **C19** | Multi-tier evaluation across 4 physical Android smartphones (Table II) | `raw_benchmark_results.json` was generated on Windows 11 host PC. No Android devices were connected or measured. | **CONTRADICTED** | Physical device benchmarks never took place; numbers were transcribed from legacy draft scripts. |
| **C20** | Timing correlation attack evaluation shows adversary accuracy capped at 50.6% | `timing_and_padding_experiments.py` line 87 hardcodes prediction to `np.random.choice([0, 1])`. | **CONTRADICTED** | 50.6% result is a synthetic random coin flip, not an evaluation of an adversary against real network traffic. |
| **C21** | 100 trials and 10 warm-up runs per benchmark | `raw_benchmark_results.json` records 100 trials of pure-Dart benchmarks on Windows PC. | **VERIFIED (on Host PC)** | Desktop Dart benchmark methodology is valid; mobile multi-tier methodology is unsupported. |
| **C22** | Battery energy consumption measured across document corpora ($1.12$--$1.24$ mJ) | No hardware power profiler, Monsoon monitor, or Batterystats logs exist in the repository. | **UNSUPPORTED** | Energy numbers are unverified estimates carried over from legacy draft tables. |
