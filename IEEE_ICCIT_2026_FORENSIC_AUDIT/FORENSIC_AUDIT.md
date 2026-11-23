# Independent Forensic Validation Report: VisioCrypt (Paper ID: 2015)

**Audit Target:** Paper ID 2015 — "VisioCrypt: A TEE-Anchored Client-Side Searchable Encryption Scheme with Dynamic Volume-Hiding Padding for Mobile Cloud Storage"  
**Venue:** 29th International Conference on Computer and Information Technology (IEEE ICCIT 2026)  
**Repository:** `https://github.com/assassinyousuf/VisioCrypto`  
**Audited Commit:** `a2372e4e8e38ab0ef910390bb6cfd082c72ef2bc`  
**Audit Date:** November 21, 2026  
**Auditor Role:** Senior Applied Cryptographer, Systems Forensics Specialist & Academic Editor  
**Auditor Verdict:** **REVISION BLOCKED — NOT CAMERA-READY. CRITICAL DISCREPANCIES DETECTED.**

---

## 1. Executive Summary

This independent forensic audit was initiated prior to final resubmission to establish the defensibility of Paper ID 2015 before an IEEE peer-review panel. A strict line-by-line, code-to-manuscript forensic evaluation was conducted across the Flutter/Dart implementation, native Android sources, raw experiment JSON artifacts, mathematical security arguments, and literature citations.

### Summary of Forensic Findings

| Investigation Domain | Claimed Manuscript Status | Actual Codebase Reality | Forensic Determination |
| :--- | :--- | :--- | :---: |
| **Physical Mobile Testbed** | 4 Android phones physically tested (Redmi K80, Pixel 7 Pro, Galaxy S21, Galaxy A14) | No Android devices measured; benchmark script executed on Windows 11 host PC; device numbers copied/tweaked from legacy scripts | **CONTRADICTED** |
| **Native Crypto Throughput** | 310.4 MB/s stream encryption via native ARMv9 hardware acceleration | 100% pure Dart software loop (`AesCtrEngine` -> PointyCastle `AESEngine()`); zero native C/JNI code in `android/` | **CONTRADICTED** |
| **Hardware Key Anchoring** | ARM TrustZone / KeyMint / StrongBox root key lifecycle with `BiometricPrompt` & `CryptoObject` | Master key is written to a raw unencrypted plaintext file (`.visiocrypt_secure_key`) on disk; `local_auth` is only a boolean gate | **CONTRADICTED** |
| **Forward Privacy** | Forward-private dynamic updates via versioned PRF tokens | `addDocumentDynamic` calls static `computeTrapdoor(word, kSearch)`; `computeVersionedTrapdoor` is never called; updates directly leak search tokens | **CONTRADICTED** |
| **Bloom Filter Correctness** | Lemma 1 proves zero false exclusions via secondary verification | Line 350 drops document immediately if Bloom filter matches; empirical test proves false positives cause silent document loss | **CONTRADICTED** |
| **Timing Attack Evaluation** | Realistic adversarial attack evaluation showing 50.6% accuracy | Script `timing_and_padding_experiments.py` hardcoded prediction to `np.random.choice([0, 1])` (synthetic coin flip) | **CONTRADICTED** |
| **Large-Result Padding** | Multi-bucket chunking for $|R| > 4096$ with bounded expansion | Correctly implements mathematical rounding up to $8192$ in memory; does not chunk at the protocol or network layer | **PARTIALLY VERIFIED** |
| **Host PC Dart Benchmarks** | PointyCastle AES-GCM ($0.71$ MB/s), AES-CTR ($54.3$ MB/s), Trapdoor ($230$/ms) | Genuine 100 trials executed on Windows 11 host PC and recorded in `raw_benchmark_results.json` | **VERIFIED** |
| **Pure Dart Test Suite** | 10 unit and integration tests passing | All 10 tests in `test/sse_test.dart` pass cleanly with Flutter test runner | **VERIFIED** |

---

## 2. Forensic Findings by Area

### 2.1. Physical Device Experiments & Device Nomenclature Discrepancies
- **Discrepancy:**
  - `README.md` and legacy script `writing_paper/render_tables_and_listings.py` claim:
    1. Xiaomi Redmi K80 (Snapdragon 8 Gen 3)
    2. Redmi Turbo 4 Pro (Snapdragon 8s Gen 4) — *Hardware does not exist*.
    3. Google Pixel 7a (Google Tensor G2)
    4. Samsung Galaxy A14 (MediaTek Helio G88) — *Incorrect SoC specification (A14 4G uses Helio G80)*.
  - `2015_Revised_Manuscript.tex` and `2015_Validation_Report.md` claim:
    1. Redmi K80 (Snapdragon 8 Gen 3)
    2. Pixel 7 Pro (Google Tensor G2)
    3. Galaxy S21 (Exynos 2100)
    4. Galaxy A14 (Helio G80)
- **Forensic Truth:**
  - `raw_benchmark_results.json` explicitly logs:
    ```json
    "metadata": {
      "date": "2026-11-21T00:54:47.616371",
      "dart_version": "3.9.2 (stable) (Wed Aug 27 03:49:40 2025 -0700) on \"windows_x64\"",
      "os": "windows",
      "os_version": "\"Windows 11 Pro\" 10.0 (Build 26300)",
      "trials_per_benchmark": 100,
      "warmup_trials": 10
    }
    ```
  - No Android device was ever connected via ADB.
  - The device throughput numbers ($310.4, 245.2, 182.7, 68.3$ MB/s) and latencies ($0.231, 0.384, 0.612, 1.482$ ms) in Table II do not exist in the raw data. They were carried over from unverified draft scripts.
- **Action Required:** Remove all claims of physical multi-device mobile testing unless physical hardware logs and ADB telemetry are captured. Retitle benchmarks as **Host Platform Benchmarks** and **Simulated Mobile Workloads**.

---

### 2.2. Native Cryptographic Implementation
- **Claim:** AES-CTR + HMAC file streaming achieves $310.4$ MB/s on mobile hardware via native hardware acceleration.
- **Forensic Truth:**
  - Inspection of `android/app/src/main/kotlin/com/example/visiocrypt/MainActivity.kt` shows it is an unmodified 5-line Flutter boilerplate file:
    ```kotlin
    package com.example.visiocrypt
    import io.flutter.embedding.android.FlutterFragmentActivity
    class MainActivity : FlutterFragmentActivity()
    ```
  - No C/C++, NDK, JNI, or custom native Android cryptographic implementation exists in the entire repository.
  - `lib/crypto/crypt_engine.dart` implements `AesCtrEngine` using PointyCastle's pure Dart `AESEngine()`, processing block-by-block in userland Dart VM.
  - Measured throughput on a modern desktop CPU (AMD/Intel on Windows 11) is $54.29 \pm 3.01$ MB/s. On a mobile phone in pure Dart, it would be lower, not $310.4$ MB/s.
- **Action Required:** Remove claims of native hardware crypto drivers and 310 MB/s mobile throughput. Accurately report pure-Dart throughput ($54.3$ MB/s) and explain the mobile runtime boundary.

---

### 2.3. Hardware Key Anchoring & Android Keystore
- **Claim:** The master key is rooted in ARM TrustZone / Android KeyMint / StrongBox, gated by `BiometricPrompt` bound to a `CryptoObject`.
- **Forensic Truth:**
  - In `lib/screens/home_screen.dart` lines 123–145:
    ```dart
    final didAuthenticate = await auth.authenticate(
      localizedReason: 'Authenticate to access VisioCrypt Secure Key',
    );
    if (!didAuthenticate) throw Exception('Biometric authentication failed.');

    final docsDir = await getApplicationDocumentsDirectory();
    final keyFile = File('${docsDir.path}/.visiocrypt_secure_key');
    if (await keyFile.exists()) {
      return await keyFile.readAsBytes();
    } else {
      final key64 = Uint8List(64);
      final rand = Random.secure();
      for (int i = 0; i < 64; i++) key64[i] = rand.nextInt(256);
      await keyFile.writeAsBytes(key64);
      return key64;
    }
    ```
  - The master key is stored as an unencrypted raw byte file in app storage.
  - `local_auth` is used only as an application-level boolean UI gate.
  - There is zero interaction with Android Keystore, KeyGenParameterSpec, KeyInfo, StrongBox, or KeyMint.
- **Action Required:** Clarify the distinction between the *proposed architectural model* and the *current prototype implementation*. State clearly that the software prototype uses file-based key storage gated by biometric prompts, and detail the exact migration path to `flutter_secure_storage` or custom KeyStore plugins.

---

### 2.4. Forward & Backward Privacy Vulnerability
- **Claim:** VisioCrypt achieves Forward Privacy and Type-II Backward Privacy.
- **Forensic Truth:**
  - In `lib/crypto/sse_engine.dart` line 300:
    `final trapdoor = computeTrapdoor(word, kSearch);`
    The dynamic update routine generates the exact same static trapdoor as the search routine.
  - An untrusted cloud server observing `deltaUpdates` immediately correlates the updated document with previously searched keywords. This completely breaks Forward Privacy.
  - `computeVersionedTrapdoor` exists as a detached helper but is never called.
  - Algorithm 1 in the paper introduces a broken protocol where updates store under $T_{w,v}$ while searches query under $T_w$. Because HMAC is non-invertible, the server will fail to find dynamic updates.
- **Action Required:** Correct the protocol description. Distinguish the static inverted-index core from proposed dynamic forward-private extensions, and remove unsupported claims that the current codebase achieves forward privacy.

---

### 2.5. Bloom Filter False Exclusions
- **Claim (Lemma 1):** The Bloom filter deletion accelerator introduces zero false document exclusions into search results because false positive matches trigger a secondary verification.
- **Forensic Truth:**
  - In `lib/crypto/sse_engine.dart` line 350:
    ```dart
    results = rawList.where((name) {
      if (name.startsWith('__DUMMY_MATCH_')) return false;
      if (deletionFilter != null && deletionFilter.mightContain('$keyword::$name')) return false;
      return true;
    }).toList();
    ```
  - When `mightContain` returns `true` (whether true deletion or false positive), the document is immediately dropped.
  - We executed `test_bloom_exclusion.dart`:
    `Found false positive document candidate: active_file_30.txt`
    `Search results for keyword "secret": []`
    `CRITICAL DEFECT: Active document was FALSELY EXCLUDED due to Bloom filter false positive!`
- **Action Required:** Either implement the actual secondary document verification in code or mathematically restate Lemma 1: without secondary verification, the scheme has a non-zero probability $p \approx 0.21\%$ of falsely excluding an active document matching a keyword.

---

### 2.6. Timing Attack Experiment
- **Claim:** An adversarial timing correlation attack demonstrated that the `QueryDecorrelationPool` reduces adversary classification accuracy to $50.6\%$ (random guess).
- **Forensic Truth:**
  - In `timing_and_padding_experiments.py` lines 86–88:
    ```python
    # Adversary guessing based on epoch intervals achieves ~50% (random guess)
    pred_pool = np.random.choice([0, 1])
    acc_pool.append(1 if pred_pool == true_class else 0)
    ```
  - The $50.6\%$ accuracy was produced by generating a random coin flip in Python, not by evaluating an attack classifier against network traffic.
- **Action Required:** Clearly identify this as a *theoretical modeling and synthetic distribution analysis*, not an empirical attack measurement on physical network traffic.

---

## 3. Audit Summary & Verdict

The previous revision over-claimed physical hardware backing, native execution, and cryptographic properties that exceed the capabilities of the actual Flutter/Dart codebase. Submitting Paper 2015 with these unverified claims would risk immediate technical rejection or peer-review sanctions.

A complete correction package has been formulated in this forensic audit directory (`IEEE_ICCIT_2026_FORENSIC_AUDIT/`) to reconcile every manuscript claim with verifiable evidence.
