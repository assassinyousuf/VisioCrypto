# Forensic Audit Corrections & Evidence Reconciliation: Device Factual Analysis

**Subject:** Correction of Device Existence Assertions and Multi-Tier Mobile Evaluation Taxonomy  
**Manuscript:** Paper ID 2015 ("VisioCrypt")  
**Target Directory:** `IEEE_ICCIT_2026_AUDIT_CORRECTIONS/FACTUAL_CORRECTIONS.md`  
**Auditor:** Senior Forensic Applied Cryptographer & Systems Auditor  
**Date:** November 2026  

---

## 1. Executive Summary & Retraction of Preliminary Audit Error

In the preliminary forensic audit report (`IEEE_ICCIT_2026_FORENSIC_AUDIT/DEVICE_EVIDENCE.md`, Section 2.1), the auditor asserted:
> *"Qualcomm Snapdragon 8s Gen 4 does not exist... Xiaomi never produced or sold a Redmi Turbo 4 Pro. This hardware was completely fictional in the initial manuscript submission."*

**This assertion was factually erroneous and is hereby formally corrected and retracted.**

### 1.1. Market Facts Regarding Claimed Hardware
1. **Xiaomi Redmi Turbo Series:** Xiaomi officially launched the Redmi Turbo series (initiating with the Redmi Turbo 3 in April 2024, followed by the Redmi Turbo 4 and Turbo 4 Pro announcements in late 2024 / early 2025). The device line is an active commercial smartphone family.
2. **Qualcomm Snapdragon Silicon:** Qualcomm officially designated and launched the Snapdragon 8s Gen 3 (SM8635) in early 2024, the Snapdragon 8 Gen 4 / Snapdragon 8 Elite (SM8750) in late 2024, and subsequent 8s derivatives in 2025.
3. **Audit Error Root Cause:** The preliminary auditor conflated an unfamiliarity with 2024/2025 product roadmap timing with non-existence, incorrectly treating a potential commercial availability timeline as proof of fabrication.

### 1.2. The Rigorous Forensic Distinction
A rigorous scientific audit must strictly separate five independent dimensions of reality:
1. **Market Existence:** Does the product, silicon, or model exist commercially or announced in the global market?
2. **Specification Accuracy:** Did the authors accurately state the SoC, memory architecture, operating system, and hardware security features of the device?
3. **Physical Availability:** Was a physical unit of this hardware physically present in the authors' research laboratory?
4. **ADB Execution / Benchmarking:** Was this physical hardware connected to a workstation via the Android Debug Bridge (ADB), provisioned with the VisioCrypt APK, and benchmarked?
5. **Raw Measurement Artifacts:** Do genuine raw measurement logs, execution timestamps, ADB traces, or per-trial telemetry exist in the repository?

An incorrect or forward-looking device specification does **not** prove malicious intent or fabrication; however, claiming empirical physical-device benchmark numbers in a published scientific manuscript when no physical device was connected or measured constitutes a severe scientific reporting defect.

---

## 2. Five-Tier Forensic Evaluation Matrix

To establish total transparency for the ICCIT 2026 review committee, every smartphone cited across `README.md`, `render_tables_and_listings.py`, `2015_Validation_Report.md`, and `2015_Revised_Manuscript.tex` is evaluated against this five-tier taxonomy.

| Device Name Cited | Claimed SoC & Specs | 1. Market Existence | 2. Spec Accuracy | 3. Physical Lab Availability | 4. ADB Execution Logged | 5. Raw Measurement Artifacts | Forensic Disposition |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Xiaomi Redmi K80** | Snapdragon 8 Gen 3, 16GB RAM, Android 15, KeyMint | **YES** (Released late 2024) | **ACCURATE** | **NO** | **NO** | **NONE** (`raw_benchmark_results.json` run on Win11 x64) | **REFRAME TO PROJECTED / REMOVE TABLE** |
| **Redmi Turbo 4 Pro** | Snapdragon 8s Gen 4, 12GB RAM, Android 15 | **YES** (Announced / Released 2024–2025) | **PLAUSIBLE / DERIVATIVE** | **NO** | **NO** | **NONE** | **RETRACT CLAIM OF PHYSICAL TEST** |
| **Google Pixel 7 Pro** | Tensor G2, 12GB RAM, Android 14, Titan M2 | **YES** (Released Oct 2022) | **ACCURATE** | **NO** | **NO** | **NONE** | **RETRACT CLAIM OF PHYSICAL TEST** |
| **Google Pixel 7a** | Tensor G2, 8GB RAM, Android 14, Titan M2 | **YES** (Released May 2023) | **ACCURATE** | **NO** | **NO** | **NONE** | **RETRACT CLAIM OF PHYSICAL TEST** |
| **Samsung Galaxy S21** | Exynos 2100, 8GB RAM, Android 13, Keymaster | **YES** (Released Jan 2021) | **ACCURATE** | **NO** | **NO** | **NONE** | **RETRACT CLAIM OF PHYSICAL TEST** |
| **Samsung Galaxy A14** | MediaTek Helio G88 / G80, 4GB RAM, Android 13 | **YES** (Released Feb 2023) | **ERRONEOUS SoC** (Uses G80 or Exynos 850, not G88) | **NO** | **NO** | **NONE** | **RETRACT CLAIM OF PHYSICAL TEST** |

---

## 3. Detailed Forensic Findings per Device

### 3.1. Xiaomi Redmi K80 & Redmi Turbo 4 Pro
- **Historical Analysis:** In `README.md` and legacy script `writing_paper/render_tables_and_listings.py`, Tier 1 was assigned to the Redmi K80 ($310.4$ MB/s throughput, $0.231$ ms latency) and Tier 2 was assigned to the Redmi Turbo 4 Pro ($214.6$ MB/s throughput, $0.342$ ms latency).
- **Physical Verification:**
  - Neither device leaves any trace in `local.properties`, Gradle build logs, ADB device lists, or Dart test runners.
  - The VisioCrypt Flutter application was never compiled into an AAB/APK and deployed via `adb install` to either device during the benchmark execution window.
- **Root Cause of Performance Numbers:**
  - The throughput numbers ($310.4$ MB/s, $214.6$ MB/s) were analytical projections computed from theoretical clock frequency ratios and memory bandwidth ceilings of modern Cortex-X4 / Cortex-A720 cores, rather than physical ADB measurements.
  - In `render_tables_and_listings.py`, these values were hardcoded into LaTeX table formatting strings.

### 3.2. Google Pixel 7 Pro vs. Pixel 7a Swap
- **Historical Analysis:**
  - In `README.md`, Tier 3 was designated as `Google Pixel 7a (Google Tensor G2)` with $142.8$ MB/s throughput and $0.62$ ms search latency.
  - In `2015_Revised_Manuscript.tex` (Table II) and `2015_Validation_Report.md`, the authors substituted `Google Pixel 7 Pro (Google Tensor G2)` with $245.2$ MB/s throughput and $0.384$ ms search latency.
- **Physical Verification:**
  - No physical Pixel device (neither 7a nor 7 Pro) was attached to the development workstation.
  - The silent substitution was undertaken in an attempt to respond to Reviewer #1 Comment 8 regarding multi-device hardware tiers.
  - Adjusting performance figures between iterations without running new physical benchmarks confirms that these values were theoretical models rather than hardware telemetry.

### 3.3. Samsung Galaxy S21 & Galaxy A14
- **Historical Analysis:**
  - Galaxy S21 was introduced into Table II of the revised manuscript as Tier 3 ($182.7$ MB/s throughput, $0.612$ ms latency).
  - Galaxy A14 was labeled in `README.md` as having a `MediaTek Helio G88`, but the commercial SM-A145F model is equipped with a `MediaTek Helio G80` or `Exynos 850`.
- **Physical Verification:**
  - The SoC mislabeling (Helio G88 vs. G80) reflects an authoring typo from spec sheet collation, not malicious fabrication.
  - However, no physical Galaxy S21 or Galaxy A14 was profiled. No power profiling logs (Monsoon or `dumpsys batterystats`) exist to substantiate the claimed $1.12$--$1.85$ mJ energy measurements.

---

## 4. The Genuine Empirical Evidence: Host Reference Platform

The forensic investigation reaffirms that the repository contains **one genuine, rigorous, and completely reproducible empirical benchmark dataset**:

- **Artifact:** `IEEE_ICCIT_2026_REVISION/2015_Experimental_Results/raw_benchmark_results.json`
- **Execution Script:** `IEEE_ICCIT_2026_REVISION/2015_Experimental_Results/run_experiments.dart`
- **Execution Timestamp:** `2026-11-21T00:54:47.616371`
- **Platform:** x86_64 PC, Windows 11 Pro (Build 26300), AMD/Intel x86_64 Architecture
- **Runtime:** Dart SDK 3.9.2 (stable, x64)
- **Experimental Rigor:** 10 warmup trials, 100 timed trials per primitive, formal 95% confidence intervals calculated from sample standard errors.

### Genuine Host Platform Measurements:
- **AES-CTR-256 (Pure Dart Keystream):** $54.2898 \pm 3.0091$ MB/s (Median: $54.9013$ MB/s)
- **AES-GCM-256 (PointyCastle Pure Dart):** $0.7087 \pm 0.0127$ MB/s (Median: $0.7136$ MB/s)
- **HMAC-SHA256 Trapdoor Generation:** $230.2379 \pm 13.662$ evals/ms (Median: $232.7747$ evals/ms)
- **Bloom Filter (8192 bits, 500 items, 10K queries):** $379.3$ ops/ms, Empirical FP: $0.21\%$ (Theoretical: $0.22\%$)
- **Inverted Index Query Scaling:** $0.108$--$0.130$ ms search resolution across 100 to 5,000 keywords.

---

## 5. Corrective Action & Framing for IEEE ICCIT 2026 Resubmission

To ensure absolute scientific integrity and comply with IEEE code of ethics:

1. **Retract Physical Mobile Hardware Claims:**
   - Remove Table II's multi-device physical benchmark columns or replace them explicitly with an analytical projection table clearly titled:
     *"Table II: Analytical Performance Model and Reference Platform Execution"*.
   - Replace any text stating *"We evaluated VisioCrypt on four physical smartphones"* with:
     > *"We evaluate the cryptographic throughput and index scaling of VisioCrypt using a reference implementation executed on the Dart 3.9.2 runtime. To evaluate mobile feasibility across diverse handset tiers, we combine these empirical benchmarks with an analytical execution model parameterized by mobile processor memory bandwidth and clock frequencies."*

2. **Acknowledge Platform Architecture:**
   - State clearly that the empirical benchmarks were executed on the Dart x64 VM reference platform, and discuss the architectural performance difference between pure-Dart software execution and native C/C++ ARM NEON cryptographic acceleration.
