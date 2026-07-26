# VisioCrypt Paper Submission Kit

This document contains all materials, metadata, cover letters, and step-by-step instructions required to submit **VisioCrypt** to **IEEE Access** or **Springer SECRYPT**.

---

## 1. Ready-to-Upload PDF Files

- **IEEE Format Target (IEEE Access / IEEE Journals):**
  - Path: `e:\_PROJECTS\visiocrypto\writing_paper\paper_ieee.pdf`
  - Layout: IEEEtran Double-Column (6 pages, 0 overfull hboxes)

- **Springer Format Target (SECRYPT / Springer LNCS):**
  - Path: `e:\_PROJECTS\visiocrypto\writing_paper\paper.pdf`
  - Layout: Springer LNCS Single-Column (13 pages)

---

## 2. Submission Metadata (Copy & Paste Ready)

### Paper Title
`VisioCrypt: TEE-Anchored Client-Side Symmetric Searchable Encryption with Volume-Hiding Protection for Mobile Cloud Storage`

### Running Title / Short Title
`VisioCrypt: Volume-Hiding Mobile SSE`

### Abstract (Plain Text for Portal Forms)
Mobile cloud storage services frequently handle sensitive user data, necessitating end-to-end client-side encryption. However, standard Symmetric Searchable Encryption (SSE) protocols exhibit vulnerabilities to access volume and query pattern leakage-abuse attacks, allowing curious cloud providers to reconstruct plaintext keyword frequencies. Furthermore, executing resource-intensive cryptographic operations within garbage-collected mobile runtimes introduces heap key residency risks. In this paper, we present VisioCrypt, a TEE-anchored client-side SSE framework optimized for mobile cloud environments. VisioCrypt integrates power-of-two candidate list quantization to enforce a volume-hiding leakage profile (L_VH) while maintaining sub-millisecond keyword lookup latencies. To mitigate side-channel vulnerability in managed mobile runtimes, VisioCrypt enforces transient memory hygiene through contiguous byte-buffer zeroization within background application isolates. We formulate a game-theoretic IND-CKA2 security reduction under our volume-hiding leakage profile. Our multi-device empirical evaluation across a heterogeneous mobile hardware testbed—including Xiaomi Redmi K80 (Snapdragon 8 Gen 3), Redmi Turbo 4 Pro (Snapdragon 8s Gen 4), Google Pixel 7a, and Samsung Galaxy A14—demonstrates query search latencies of 0.23 ms to 1.48 ms over 10,000 keyword entries, outperforming page-encrypted database baselines (SQLCipher) by up to 23.5x while quantifying the 50.8% storage inflation required for access volume privacy.

### Keywords / Index Terms
- Symmetric Searchable Encryption (SSE)
- Volume-Hiding Padding
- Mobile Security
- Trusted Execution Environment (TEE)
- Cryptographic Storage
- Memory Hygiene
- IND-CKA2 Security
- Cloud Security

### Primary Subject Categories / EDICS
- **Primary Category:** Cryptography and Security Systems
- **Secondary Category:** Mobile Systems and Computing Security / Cloud Security

---

## 3. Formal Cover Letter to Editor-in-Chief

To the Editor-in-Chief,

We wish to submit an original research article entitled "VisioCrypt: TEE-Anchored Client-Side Symmetric Searchable Encryption with Volume-Hiding Protection for Mobile Cloud Storage" for consideration in your journal.

This manuscript addresses a critical challenge in mobile cloud computing: protecting user search query privacy against server-side leakage-abuse attacks without sacrificing client responsiveness or key security in managed mobile execution runtimes (such as Android Dart isolates).

Key contributions of our work include:
1. A practical volume-hiding Symmetric Searchable Encryption (SSE) scheme utilizing power-of-two candidate list quantization to mitigate frequency analysis leakage attacks.
2. A formal IND-CKA2 security reduction proof proving indistinguishability under our volume-hiding leakage profile (L_VH).
3. A client-side managed memory hygiene architecture utilizing contiguous byte-buffer zeroization to prevent heap key exposure.
4. Comprehensive 4-tier mobile hardware benchmarking across Xiaomi Redmi K80 (Snapdragon 8 Gen 3), Redmi Turbo 4 Pro (Snapdragon 8s Gen 4), Google Pixel 7a, and Samsung Galaxy A14 hardware demonstrating sub-millisecond retrieval (0.23 ms) and a 23.5x speedup over SQLCipher baselines.

We confirm that this work is original, has not been published elsewhere, and is not currently under consideration for publication in any other venue.

Thank you for your time and consideration.

Sincerely,

The Authors of VisioCrypt

---

## 4. Step-by-Step Submission Instructions for IEEE Access

1. **Go to the Submission Portal:**
   - Link: https://mc.manuscriptcentral.com/ieee-access
   - Log in or click **"Create an Account"**.

2. **Start New Submission:**
   - Click **"Author"** tab -> **"Start a New Submission"** -> **"Begin Submission"**.

3. **Upload Files:**
   - Main Document: Upload `e:\_PROJECTS\visiocrypto\writing_paper\paper_ieee.pdf`.
   - Select File Designation: **"Main File"** or **"Manuscript PDF"**.

4. **Fill Metadata Fields:**
   - Copy-paste Title, Abstract, and Keywords from Section 2 of this guide.

5. **Attach Cover Letter:**
   - Copy-paste or attach the Cover Letter text from Section 3 of this guide.

6. **Review & Submit:**
   - Preview the generated submission proof PDF.
   - Click **"Submit"**.
