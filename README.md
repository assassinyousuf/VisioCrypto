# VisioCrypt

> **A TEE-Anchored Client-Side Searchable Encryption Scheme with Dynamic Volume-Hiding Padding for Mobile Cloud Storage**

---

## 🌟 Key Architecture & Highlights

VisioCrypt provides an end-to-end symmetric searchable encryption (SSE) framework designed specifically for mobile and resource-constrained platforms, eliminating the need to trust cloud storage providers with plaintext files or access patterns.

### 🛡️ Core Security Capabilities

1. **Volume-Hiding Padding ($\Phi$)**:
   - Quantizes matching document lists to power-of-two equivalence classes ($\max(L_{\min}, 2^{\lceil \log_2(|L_w|) \rceil})$).
   - Prevents volume-based query recovery and statistical frequency-analysis attacks.

2. **Dynamic Forward & Type-II Backward Privacy**:
   - **Forward Privacy**: Incrementally appends new encrypted documents via versioned PRF trapdoors ($T_{w,\text{dyn}}$), ensuring newly added files cannot be linked to prior search queries.
   - **Type-II Backward Privacy**: Integrates an in-memory Bloom Filter ($\mathbf{BF}$) for $O(1)$ deleted-document membership filtering without leaking cancellation pairings.

3. **Query Decorrelation Pool ($\mathcal{P}_{\text{decorr}}$)**:
   - Buffers search requests into a client-side $\theta$-sampling pool.
   - Injects synthetic dummy trapdoors and randomizes dispatch timings ($\delta t \sim \mathcal{U}(t_{\min}, t_{\max})$) to thwart temporal co-occurrence and access-pattern analysis.

4. **Hardware Key Anchoring & Transient Memory Hygiene**:
   - **At Rest**: 256-bit master key anchored in hardware-backed TEE (ARM TrustZone / Android Keystore) via biometric gating and Argon2id.
   - **In Execution**: Sub-keys derived via domain-separated HKDF-SHA256 (`K_enc`, `K_search`, `K_index_val`, `K_update`) with explicit typed byte-buffer zeroization (`.fillRange(0, length, 0)`).

---

## 📁 Repository Structure

* **`lib/crypto/`**:
  * [`sse_engine.dart`](file:///e:/_PROJECTS/visiocrypto/lib/crypto/sse_engine.dart): Dynamic SSE engine, `SseBloomFilter`, `QueryDecorrelationPool`, and volume-hiding padding.
  * [`crypt_engine.dart`](file:///e:/_PROJECTS/visiocrypto/lib/crypto/crypt_engine.dart): Streaming AES-CTR-256 and HMAC-SHA256 authenticated encryption primitives.
  * [`hkdf.dart`](file:///e:/_PROJECTS/visiocrypto/lib/crypto/hkdf.dart): Domain-separated key expansion.
  * [`benchmark.dart`](file:///e:/_PROJECTS/visiocrypto/lib/crypto/benchmark.dart): Performance and scalability benchmark harness.
* **`writing_paper/`**:
  * [`paper.pdf`](file:///e:/_PROJECTS/visiocrypto/writing_paper/paper.pdf): Full research manuscript in Springer LNCS format (11 pages).
  * [`paper_ieee.pdf`](file:///e:/_PROJECTS/visiocrypto/writing_paper/paper_ieee.pdf): Research manuscript in IEEE Transactions format (5 pages).
  * [`references.bib`](file:///e:/_PROJECTS/visiocrypto/writing_paper/references.bib): BibTeX literature database.

---

## 📊 Empirical Performance Summary

Benchmarked across flagship, high-performance, mid-range, and budget mobile hardware:

| Benchmark Metric | Xiaomi Redmi K80 (Snapdragon 8 Gen 3) | Redmi Turbo 4 Pro (Snapdragon 8s Gen 4) | Google Pixel 7a (Tensor G2) | Samsung Galaxy A14 (Helio G88) |
| :--- | :---: | :---: | :---: | :---: |
| **Search Latency (Padded SSE)** | **0.23 ms** | **0.29 ms** | **0.62 ms** | **1.48 ms** |
| **SQLCipher DB Search** | 5.20 ms | 6.80 ms | 14.20 ms | 34.80 ms |
| **Stream File Enc Throughput** | **310.50 MB/s** | **265.20 MB/s** | **142.80 MB/s** | **68.40 MB/s** |
| **Bloom Filter Lookup Rate** | > 22,000 ops/ms | > 20,000 ops/ms | > 15,000 ops/ms | > 8,000 ops/ms |
