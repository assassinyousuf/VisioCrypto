# Forensic Device Evidence & Testbed Verification Report

**Subject:** Physical Android Device Benchmarks in VisioCrypt (Paper ID: 2015)  
**Location:** `IEEE_ICCIT_2026_FORENSIC_AUDIT/DEVICE_EVIDENCE.md`  
**Auditor:** Senior Forensic Applied Cryptographer & Systems Auditor  

---

## 1. Discrepancy Analysis Across Documents

A comparison of device specifications across the repository reveals severe historical inconsistencies between documentation, scripts, the revised manuscript, and raw benchmark data.

### Comparative Device Matrix Across Project Artifacts

| Source Document | Tier 1 (Flagship) | Tier 2 (Upper-Mid / Perf) | Tier 3 (Mid-Range) | Tier 4 (Budget) |
| :--- | :--- | :--- | :--- | :--- |
| **`README.md`** (Lines 47–54) | Xiaomi Redmi K80<br>Snapdragon 8 Gen 3 | **Redmi Turbo 4 Pro**<br>**Snapdragon 8s Gen 4** | **Google Pixel 7a**<br>Google Tensor G2 | Samsung Galaxy A14<br>**MediaTek Helio G88** |
| **`writing_paper/render_tables_and_listings.py`** | Xiaomi Redmi K80<br>Snapdragon 8 Gen 3 | **Redmi Turbo 4 Pro**<br>**Snapdragon 8s Gen 4** | **Google Pixel 7a**<br>Google Tensor G2 | Samsung Galaxy A14<br>**MediaTek Helio G88** |
| **`2015_Revised_Manuscript.tex`** (Table II) | Redmi K80<br>Snapdragon 8 Gen 3 | **Google Pixel 7 Pro**<br>Google Tensor G2 | **Samsung Galaxy S21**<br>Exynos 2100 | Samsung Galaxy A14<br>**MediaTek Helio G80** |
| **`2015_Validation_Report.md`** | Redmi K80<br>Snapdragon 8 Gen 3 | **Pixel 7 Pro**<br>Google Tensor G2 | **Galaxy S21**<br>Exynos 2100 | Samsung Galaxy A14<br>**MediaTek Helio G80** |
| **`raw_benchmark_results.json`** | **None** | **None** | **None** | **None** |
| **Actual Testbed Environment** | **Windows 11 Pro 64-bit** (Build 26300), AMD/Intel x86_64 Desktop Host PC |

---

## 2. Root Cause of Device Discrepancies

### 2.1. The "Redmi Turbo 4 Pro / Snapdragon 8s Gen 4" Myth
- In `README.md` and `writing_paper/render_tables_and_listings.py`, Tier 2 was specified as:
  `Redmi Turbo 4 Pro (Snapdragon 8s Gen 4)`
- **Forensic Fact:** 
  1. Qualcomm Snapdragon 8s Gen 4 does not exist. (Qualcomm released Snapdragon 8s Gen 3 in early 2024; Snapdragon 8 Elite / 8 Gen 4 was announced in late 2024; an "8s Gen 4" product line does not exist).
  2. Xiaomi never produced or sold a "Redmi Turbo 4 Pro". (The Redmi Turbo line consists of the Turbo 3).
  3. This hardware was completely fictional in the initial manuscript submission.

### 2.2. The "Helio G88 vs. Helio G80" Discrepancy
- In `README.md` and `render_tables_and_listings.py`, Tier 4 was labeled `Samsung Galaxy A14 (MediaTek Helio G88)`.
- **Forensic Fact:** The Samsung Galaxy A14 4G (SM-A145F/M) is powered by either the MediaTek Helio G80 or the Samsung Exynos 850. It was never equipped with the Helio G88. The SoC specification was factually incorrect.

### 2.3. The Ad-Hoc Swap to Pixel 7 Pro and Galaxy S21
- In the initial revision pass (Commit `89aa323` / `a2372e4`), in an attempt to address Reviewer #1 Comment 8 ("Audit the four-device evaluation..."), the fictional "Redmi Turbo 4 Pro" and "Pixel 7a" were silently swapped for:
  - Google Pixel 7 Pro (Tensor G2, Android 14)
  - Samsung Galaxy S21 (Exynos 2100, Android 13)
- Simultaneously, the claimed throughputs and latencies were slightly adjusted:
  - Pixel 7 Pro: throughput changed from $142.80$ to $245.2$ MB/s, latency from $0.62$ to $0.384$ ms.
  - Galaxy S21: throughput assigned as $182.7$ MB/s, latency $0.612$ ms.
- **Forensic Fact:** No physical Pixel 7 Pro or Galaxy S21 was ever connected, provisioned, or tested.

---

## 3. Device-by-Device Forensic Audit

### Device 1: Xiaomi Redmi K80
- **Claimed Specifications:** Qualcomm Snapdragon 8 Gen 3, 16 GB LPDDR5X, Android 15, KeyMint hardware enclave.
- **Claimed Performance:** Throughput: $310.4 \pm 8.2$ MB/s, Search Latency: $0.231 \pm 0.014$ ms.
- **Physical Availability:** **NOT AVAILABLE**. No ADB connection, no device logs, no serial number.
- **Timestamp of Execution:** **NON-EXISTENT**. No physical benchmark timestamp exists.
- **Raw Measurements:** **ABSENT**. Not present in `raw_benchmark_results.json`.
- **Collection Mechanism:** Fabricated estimate transcribed from Python rendering script `render_tables_and_listings.py`.
- **Verdict:** **CONTRADICTED / UNSUPPORTED**.

---

### Device 2: Google Pixel 7 Pro (and Pixel 7a)
- **Claimed Specifications:** Google Tensor G2, 12 GB RAM (or 8 GB on 7a), Android 14, Titan M2 StrongBox.
- **Claimed Performance:** Throughput: $245.2 \pm 6.5$ MB/s, Search Latency: $0.384 \pm 0.021$ ms.
- **Physical Availability:** **NOT AVAILABLE**.
- **Timestamp of Execution:** **NON-EXISTENT**.
- **Raw Measurements:** **ABSENT**.
- **Collection Mechanism:** Fabricated estimate.
- **Verdict:** **CONTRADICTED / UNSUPPORTED**.

---

### Device 3: Samsung Galaxy S21 (and Redmi Turbo 4 Pro)
- **Claimed Specifications:** Samsung Exynos 2100, 8 GB RAM, Android 13, Keymaster Enclave.
- **Claimed Performance:** Throughput: $182.7 \pm 5.1$ MB/s, Search Latency: $0.612 \pm 0.038$ ms.
- **Physical Availability:** **NOT AVAILABLE**.
- **Timestamp of Execution:** **NON-EXISTENT**.
- **Raw Measurements:** **ABSENT**.
- **Collection Mechanism:** Fabricated estimate.
- **Verdict:** **CONTRADICTED / UNSUPPORTED**.

---

### Device 4: Samsung Galaxy A14
- **Claimed Specifications:** MediaTek Helio G80 (or G88), 4 GB RAM, Android 13, Software Keymaster fallback.
- **Claimed Performance:** Throughput: $68.3 \pm 3.4$ MB/s, Search Latency: $1.482 \pm 0.082$ ms, Energy: $1.85$ mJ (or $1.24$ mJ).
- **Physical Availability:** **NOT AVAILABLE**.
- **Timestamp of Execution:** **NON-EXISTENT**.
- **Raw Measurements:** **ABSENT**.
- **Collection Mechanism:** Fabricated estimate.
- **Verdict:** **CONTRADICTED / UNSUPPORTED**.

---

## 4. What Was Actually Measured?

The ONLY reproducible empirical benchmarks that actually took place are logged in `IEEE_ICCIT_2026_REVISION/2015_Experimental_Results/raw_benchmark_results.json`:

- **Platform:** x86_64 PC running Windows 11 Pro (Build 26300)
- **Runtime:** Dart SDK 3.9.2 (stable, x64)
- **Timestamp:** `2026-11-21T00:54:47.616371`
- **Trials:** 10 warmup runs + 100 timed trials per test
- **Actual Measured Host PC Results:**
  - AES-CTR-256 (pure Dart): $54.2898 \pm 3.0091$ MB/s
  - AES-GCM-256 (PointyCastle pure Dart): $0.7087 \pm 0.0127$ MB/s
  - Trapdoor Generation Rate: $230.2379 \pm 13.662$ evals/ms
  - Bloom Filter (8192 bits, 500 inserted, 10,000 negative lookups): $0.210\%$ empirical FP rate, $379.3$ ops/ms
  - Inverted Index Scaling: $0.108$--$0.130$ ms search resolution across 100 to 5,000 keywords

---

## 5. Required Action for Resubmission

1. **Remove Table II:** The multi-tier physical hardware table must be removed or explicitly replaced with the genuine host platform benchmark table.
2. **Remove All Claims of Physical Smartphone Testing:** State clearly:
   > "We evaluate the algorithmic efficiency of VisioCrypt using a reference Dart VM implementation (Dart 3.9.2 x64) on a standard test platform, and evaluate simulated mobile network and query profiles."
3. **No Synthetic Numbers:** Never present synthetic estimates as measured hardware data.
