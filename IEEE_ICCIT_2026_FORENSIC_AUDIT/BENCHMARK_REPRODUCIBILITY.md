# Benchmark Reproducibility & Empirical Verification Report

**Subject:** Empirical Verification of Benchmarks, Timing Attack Simulation, Bloom Filter Correctness, and Test Suites  
**Manuscript:** Paper ID 2015 ("VisioCrypt")  
**Location:** `IEEE_ICCIT_2026_FORENSIC_AUDIT/BENCHMARK_REPRODUCIBILITY.md`  

---

## 1. Clean Environment Test Suite Execution

We executed the complete Flutter test suite from a clean environment.

### Execution Record
- **Command:** `G:\_PROJECTS\flutter\bin\flutter.bat test test/sse_test.dart`
- **Working Directory:** `G:\_PROJECTS\visiocrypto`
- **Execution Timestamp:** `2026-11-21T01:23:22+06:00`
- **Dart Version:** `Dart SDK 3.9.2 (stable)`
- **Flutter Framework:** `Flutter 3.35.0-1.0.pre.1`
- **Platform:** `Windows 11 Pro 64-bit (Build 26300)`
- **Exit Code:** `0` (Success)
- **Total Test Cases:** **10**
- **Passing Cases:** **10**
- **Failing Cases:** **0**

### Detailed Test Manifest
| Test Case Name | Target Mechanism | Result | Execution Time |
| :--- | :--- | :---: | :---: |
| `HKDF-Extract and Expand produces deterministic split keys` | RFC 5869 Extract/Expand | **PASSED** | $< 10$ ms |
| `AES-CTR engine initialization and keystream sequence` | PointyCastle AES-CTR stream | **PASSED** | $< 10$ ms |
| `Different keys produce different keystreams` | Key sensitivity | **PASSED** | $< 10$ ms |
| `Tokenization removes stopwords and filters valid keywords` | Keyword pre-processing | **PASSED** | $< 10$ ms |
| `Trapdoor generation is deterministic` | HMAC-SHA256 search token | **PASSED** | $< 10$ ms |
| `Encrypt and decrypt roundtrip matches original data` | AEAD Encrypt-then-MAC file | **PASSED** | $< 15$ ms |
| `Decryption fails if ciphertext is altered` | HMAC integrity verification | **PASSED** | $< 15$ ms |
| `Indexing and searching a document retrieves matching files` | SSE index database | **PASSED** | $< 25$ ms |
| `Volume-Hiding padding pads index lists and search filters dummy` | Power-of-two padding $\Phi$ | **PASSED** | $< 20$ ms |
| `Volume-Hiding padding correctly handles result sets exceeding 32 entries` | Large results ($33, 65, 300, 2500, 5000$) | **PASSED** | $< 35$ ms |

---

## 2. Raw Benchmark JSON Verification (`raw_benchmark_results.json`)

We audited `IEEE_ICCIT_2026_REVISION/2015_Experimental_Results/raw_benchmark_results.json` to verify whether genuine 100 trials were measured.

### 2.1. Verification of 100 Measured Trials
- **Execution Script:** `IEEE_ICCIT_2026_REVISION/2015_Experimental_Results/run_experiments.dart`
- **Host System:** Windows 11 Pro (Build 26300) x86_64, Dart 3.9.2
- **Warmup Procedure:** 10 unrecorded warmup trials executed prior to timing
- **Recorded Sample Size:** 100 iterations per benchmark metric
- **Actual Measured Host Data:**
  1. **AES-CTR-256 Throughput:**
     - Mean: $54.2898$ MB/s
     - Standard Deviation: $3.0091$ MB/s
     - Median: $54.9013$ MB/s
     - 95% Confidence Interval: $[53.7001, 54.8796]$ MB/s
  2. **AES-GCM-256 Throughput:**
     - Mean: $0.7087$ MB/s
     - Standard Deviation: $0.0127$ MB/s
     - Median: $0.7136$ MB/s
     - 95% Confidence Interval: $[0.7062, 0.7112]$ MB/s
  3. **Trapdoor Generation Rate:**
     - Mean: $230.2379$ evals/ms
     - Standard Deviation: $13.662$ evals/ms
     - Median: $232.7747$ evals/ms
  4. **Inverted Index Scaling:**
     - 100 Keywords: Search latency $0.114$ ms (median)
     - 500 Keywords: Search latency $0.106$ ms (median)
     - 1,000 Keywords: Search latency $0.103$ ms (median)
     - 2,500 Keywords: Search latency $0.1085$ ms (median)
     - 5,000 Keywords: Search latency $0.119$ ms (median)

**Verdict:** The host PC Dart benchmark results are **genuine, reproducible, and mathematically consistent**. However, they reflect desktop execution, not mobile execution.

---

## 3. Bloom Filter Theoretical vs. Empirical Verification

### 3.1. Theoretical Recalculation
For a Bloom filter with $m$ bits, $k$ hash functions, and $n$ inserted items:
$$p = \left( 1 - \left( 1 - \frac{1}{m} \right)^{k n} \right)^k \approx \left( 1 - e^{-k n / m} \right)^k$$

For $m = 8192$, $k = 4$, $n = 500$:
$$\frac{k n}{m} = \frac{4 \times 500}{8192} = \frac{2000}{8192} \approx 0.24414$$
$$e^{-0.24414} \approx 0.783377$$
$$1 - e^{-0.24414} \approx 0.216623$$
$$p = (0.216623)^4 \approx 0.002202 \quad (0.2202\%)$$

### 3.2. Comparison Across Filter Sizes ($n = 500, k = 4, 10,000$ Lookups)
| Capacity $m$ (bits) | Theoretical FP Rate ($p$) | Measured Empirical FP Rate | Detected FP Count / 10K | Status |
| :---: | :---: | :---: | :---: | :---: |
| **2048** | $15.10\%$ | $15.11\%$ | 1,511 / 10,000 | **MATCH** |
| **4096** | $2.23\%$ | $2.42\%$ | 242 / 10,000 | **MATCH** |
| **8192** | $0.22\%$ | $0.21\%$ | 21 / 10,000 | **MATCH** |
| **16384** | $0.017\%$ | $0.04\%$ | 4 / 10,000 | **MATCH** |

**Verdict:** The Bloom filter mathematical formula and implementation match within standard statistical deviation.

### 3.3. Correctness Audit (False Exclusion Vulnerability)
- **Finding:** While the filter's FP rate is verified, line 350 of `sse_engine.dart` directly excludes any document matching the filter.
- **Empirical Proof (`test_bloom_exclusion.dart`):**
  Active non-deleted document `active_file_30.txt` matched the filter due to an FP and was dropped from search results.
- **Correction:** The implementation must verify local document existence (`File(path).exists()`) before exclusion, or the manuscript must retract Lemma 1.

---

## 4. Timing Attack Simulation Audit

The manuscript and rebuttal report that an adversarial evaluation demonstrated adversary profiling accuracy was reduced from $100\%$ to $50.6\%$.

### 4.1. Audit of `timing_and_padding_experiments.py`
We inspected the Python simulation script:

```python
# Unmitigated simulation:
obs_unmit = np.mean(raw_intervals)
pred_unmit = 0 if obs_unmit < 160.0 else 1
acc_unmit.append(1 if pred_unmit == true_class else 0)

# Random Delay simulation:
obs_rand_intervals = raw_intervals + (delays[1:] - delays[:-1])
obs_rand = np.mean(obs_rand_intervals)
pred_rand = 0 if obs_rand < 160.0 else 1
acc_rand.append(1 if pred_rand == true_class else 0)

# VisioCrypt Decorrelation Pool:
pool_intervals = np.random.choice([50.0, 100.0], size=M, p=[0.7, 0.3])
pred_pool = np.random.choice([0, 1])  # <--- DIRECT HARDCODED SYNTHETIC COIN FLIP
acc_pool.append(1 if pred_pool == true_class else 0)
```

### 4.2. Forensic Findings
1. **Nature of Evaluation:** This is a **pure synthetic mathematical simulation**, not an adversarial evaluation of live network traffic.
2. **Hardcoded Random Guessing:** Line 87 sets `pred_pool = np.random.choice([0, 1])`. The adversary's guess is not computed by analyzing packet arrival times; it is hardcoded to a 50/50 NumPy random coin flip.
3. **Manuscript Misrepresentation:** The manuscript describes this as an:
   > *"Empirical evaluation... Adversary profiling accuracy under timing correlation attacks: while unmitigated and random-delayed queries allow the adversary to achieve 100% classification accuracy within M=5 observations, VisioCrypt's QueryDecorrelationPool caps adversary accuracy at 50.6%."*
   Presenting a synthetic coin flip as an empirical physical measurement is scientifically indefensible.

---

## 5. Required Actions for Defensibility

1. **Reframe Timing Evaluation:** Rephrase Fig. 2(b) and Section VII-B as a **Theoretical Information-Theoretic Modeling of Epoch Batching**, explicitly stating:
   > "Under the assumption that queries are batched into fixed epochs and padded with dummy trapdoors, inter-dispatch intervals become independent of user keystroke timing, bounding an optimal Bayes classifier to the prior distribution (50% random guessing)."
2. **Correct Benchmark Scope:** State that throughput and indexing latencies were gathered on the reference runtime environment, acknowledging the mobile deployment pipeline.
