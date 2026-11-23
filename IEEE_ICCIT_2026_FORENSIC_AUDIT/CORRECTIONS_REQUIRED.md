# Actionable Scientific Corrections Required for Defensibility

**Target:** Paper ID 2015 ("VisioCrypt")  
**Venue:** IEEE ICCIT 2026  
**Location:** `IEEE_ICCIT_2026_FORENSIC_AUDIT/CORRECTIONS_REQUIRED.md`  
**Guiding Principle:** *"Do not optimize for making the paper look impressive. Optimize for making every sentence defensible before an IEEE reviewer."*

---

## 1. Codebase Technical Repairs

Before updating the manuscript, the following implementation flaws must be rectified in the code:

### 1.1. Bloom Filter False Exclusion Bug (`lib/crypto/sse_engine.dart`)
- **Current Defect (Line 350):**
  ```dart
  if (deletionFilter != null && deletionFilter.mightContain('$keyword::$name')) return false;
  ```
  Immediately drops the candidate file if the Bloom filter matches, causing active non-deleted files to be silently excluded upon a false positive ($p \approx 0.21\%$).
- **Mandatory Repair:**
  Implement the secondary state verification promised in Lemma 1:
  ```dart
  if (deletionFilter != null && deletionFilter.mightContain('$keyword::$name')) {
    // Secondary check: verify if the document actually exists in active state
    final candidatePath = '${indexFile.parent.path}/$name';
    if (!File(candidatePath).existsSync()) {
      return false; // Document was genuinely deleted
    }
    // False positive detected: retain active document
  }
  ```

### 1.2. Dynamic Update Trapdoor Fix (`lib/crypto/sse_engine.dart`)
- **Current Defect (Line 300):**
  `addDocumentDynamic` calls static `computeTrapdoor(word, kSearch)`, leaking search trapdoors and destroying forward privacy.
- **Mandatory Repair:**
  Either:
  1. Clearly document in the code and manuscript that dynamic additions in the current prototype use append-logging under index re-encryption, OR
  2. Implement a consistent version-chained PRF token system that both update and search traverse.

---

## 2. Manuscript Textual Corrections (`2015_Revised_Manuscript.tex`)

### 2.1. Title & Abstract Adjustments
- **Current Claim:**
  > *"Master root keys are anchored in hardware-backed mobile enclaves (ARM TrustZone / Android KeyMint) with biometric gating... Empirical evaluation across four physical Android hardware tiers confirms sub-millisecond search latencies (0.23–1.48 ms), file streaming throughput up to 310 MB/s..."*
- **Defensible Replacement:**
  > *"We architect a hardware-anchored key lifecycle model for mobile enclaves (ARM TrustZone / Android KeyMint) with biometric gating... Empirical evaluation on our reference implementation confirms sub-millisecond search resolution (0.10–0.13 ms for up to 5,000 keywords), streaming throughput up to 54.3 MB/s in pure Dart, and query decorrelation that mitigates statistical timing analysis."*

---

### 2.2. Section V: Hardware Key Anchoring & Enclave Boundary
- **Current Claim:**
  > *"VisioCrypt anchors its root secret inside hardware-backed storage via the Android Keystore provider: (1) Key Generation: Generates a 256-bit AES master key inside Android KeyMint / StrongBox... (2) Biometric Gating: Access requires valid user authentication via Android BiometricPrompt bound to a cryptographic CryptoObject..."*
- **Defensible Replacement:**
  > *"VisioCrypt specifies an architectural root-key anchoring model targeting platform hardware enclaves: (1) Architecture Model: The production specification binds master secrets to Android KeyMint / StrongBox enclaves via KeyGenParameterSpec with PURPOSE_ENCRYPT | PURPOSE_DECRYPT and AUTH_BIOMETRIC_STRONG. (2) Prototype Implementation: In our cross-platform reference prototype, biometric authorization is verified via the platform biometric service, gating access to application-isolated key stores, while operational keys are derived in ephemeral worker isolates with active buffer zeroization."*

---

### 2.3. Section VI: Security Claims & Theorem 1
- **Current Claim:**
  > *"VisioCrypt achieves forward privacy and Type-II backward privacy..."*
- **Defensible Replacement:**
  > *"VisioCrypt achieves volume-hiding inverted-index security for static corpora, while dynamic deletions are processed client-side via our negative-lookup Bloom filter accelerator without server-side index leakage at deletion time. Full forward-private dynamic updating via trapdoor permutations represents an active area of future integration."*
- **Theorem 1 Statement:**
  Limit Theorem 1 strictly to $\mathcal{L}_{\text{VH}}\text{-IND-CKA2}$ security for static queries with client-side deletion filtering.

---

### 2.4. Section VII: Benchmarks & Table II
- **Current Table II:**
  Claims four physical devices (Redmi K80, Pixel 7 Pro, Galaxy S21, Galaxy A14) with throughputs up to 310.4 MB/s and latencies down to 0.231 ms.
- **Defensible Replacement:**
  Replace Table II with the genuine, measured benchmark results from `raw_benchmark_results.json`:

```latex
\begin{table}[t]
\centering
\caption{Cryptographic and Indexing Micro-Benchmarks ($N=100$ Trials)}
\label{tab:measured_benchmarks}
\scriptsize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lccc}
\toprule
\textbf{Primitive / Operation} & \textbf{Mean $\pm$ Std} & \textbf{Median} & \textbf{95\% Conf. Interval} \\
\midrule
AES-CTR-256 (Pure Dart) & 54.29 $\pm$ 3.01 MB/s & 54.90 MB/s & [53.70, 54.88] MB/s \\
AES-GCM-256 (PointyCastle) & 0.71 $\pm$ 0.01 MB/s & 0.71 MB/s & [0.71, 0.71] MB/s \\
Trapdoor Gen (HMAC-SHA256) & 230.2 $\pm$ 13.7 ev/ms & 232.8 ev/ms & [227.6, 232.9] ev/ms \\
Bloom Lookup (8192 bits) & 379.3 $\pm$ 12.1 ops/ms & 378.9 ops/ms & [376.9, 381.7] ops/ms \\
Inverted Index Search ($N=5000$) & 0.13 $\pm$ 0.03 ms & 0.12 ms & [0.12, 0.14] ms \\
\bottomrule
\end{tabular}
\end{table}
```

---

### 2.5. Timing Attack Evaluation (Figure 2(b))
- **Current Claim:**
  > *"Fig. 2(b) reports adversary profiling accuracy under timing attacks... VisioCrypt's QueryDecorrelationPool caps adversary accuracy at 50.6%..."*
- **Defensible Replacement:**
  > *"Fig. 2(b) models adversary classification accuracy under information-theoretic simulation: while unmitigated traffic exposes inter-query typing delays that cancel out under statistical averaging, epoch-based batching ($T_e = 50$ ms) with injected dummy queries decouples dispatch timing from user activity, reducing an optimal Bayes classifier to the prior distribution (50% random guessing)."*

---

## 3. What Missing Evidence is Needed If You Wish to Retain Specific Claims?

If the user explicitly desires to make specific claims in the paper, the following physical evidence **must** be gathered first:

| To Defensibly Claim... | You MUST Collect This Exact Evidence First: |
| :--- | :--- |
| **Physical Android Testing** | 1. Connect physical Android devices via USB with `adb`.<br>2. Install and run `flutter run --release` on each handset.<br>3. Collect raw benchmark execution output via `adb logcat` with system device model (`getprop ro.product.model`), Android build (`getprop ro.build.version.release`), and SoC info (`cat /proc/cpuinfo`).<br>4. Save the raw logcat output as verifiable JSON/CSV files in the repository. |
| **310 MB/s Hardware Throughput** | 1. Implement native Android crypto in C++ via NDK using Android `libcrypto.so` or ARM NEON/AES instructions (`#include <arm_neon.h>`).<br>2. Expose it via Dart FFI (`dart:ffi`) or Platform Channel.<br>3. Measure file throughput on a physical ARMv8/ARMv9 phone and record the benchmark log. |
| **Hardware KeyMint / StrongBox Anchoring** | 1. Write Kotlin native code in `MainActivity.kt` invoking `KeyGenParameterSpec.Builder(alias, PURPOSE_ENCRYPT \| PURPOSE_DECRYPT)` with `setIsStrongBoxBacked(true)` and `setUserAuthenticationRequired(true)`.<br>2. Inspect `KeyInfo.getSecurityLevel()` and log the returned integer.<br>3. Bind the key cipher to `BiometricPrompt.CryptoObject`. |

---

## 4. Rebuttal Letter (`2015_Author_Response.tex`) Revisions

The author response letter must be updated to reflect these rigorous, honest scientific positions:
1. Concede that physical mobile device tables in the original draft were based on simulated mobile workloads and reference desktop runs.
2. Present the honest pure-Dart performance figures ($54.3$ MB/s) and frame hardware enclaves and native acceleration as production architectural specifications.
3. Present the corrected Lemma 1 secondary check, explaining how the negative-lookup accelerator guarantees correctness when paired with local state checking.
4. Clarify the timing decorrelation pool as an analytical and simulated model.

By making these transparent, defensible revisions, Paper ID 2015 will withstand the most rigorous scrutiny of IEEE reviewers and editors.
