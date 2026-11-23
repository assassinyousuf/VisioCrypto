# Systematic Comparative Literature Review: Searchable Symmetric Encryption (SSE)
**Target Venue:** IEEE ICCIT 2026  
**Manuscript:** VisioCrypt (Paper ID: 2015)  

---

## 1. Scheme Comparison Matrix

The table below contrasts VisioCrypt against foundational and state-of-the-art Searchable Symmetric Encryption schemes across nine formal cryptographic and operational dimensions.

| Scheme | Venue / Year | Search Complexity | Update Complexity | Forward Privacy | Backward Privacy | Volume Hiding | Result-Size Leakage | TEE Dependency | Mobile Suitability |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Song et al. (SWP00)** [1] | IEEE S&P 2000 | $O(N)$ sequential | $O(1)$ append | No | No | No | Exact $|R(w)|$ | None | Poor (linear mobile battery drain) |
| **Curtmola et al.** [2] | ACM CCS 2006 | $O(\|R(w)\|)$ | Static (No updates) | N/A | N/A | No | Exact $|R(w)|$ | None | Moderate (Static read-only) |
| **Kamara et al.** [3] | ACM CCS 2012 | $O(\|R(w)\|)$ | $O(d_w)$ | No | No | No | Exact $|R(w)|$ | None | Good |
| **Cash et al.** [4] | CRYPTO 2013 | $O(\|R(w)\|)$ | Static / Semi-dynamic | No | No | No | Exact $|R(w)|$ | None | Good (Large databases) |
| **Bost (Sophos)** [5] | ACM CCS 2016 | $O(\|R(w)\|)$ | $O(1)$ | **Yes** (Trapdoor permutation) | No | No | Exact $|R(w)|$ | None | Good |
| **Bost et al. (Diana)** [6] | ACM CCS 2017 | $O(\|R(w)\|)$ | $O(1)$ | **Yes** | **Yes** (Type-II / Type-III) | No | Exact $|R(w)|$ | None | Moderate |
| **Demertzis et al. (SEAL)** [7] | NDSS 2020 | $O(\|R(w)\| + \log N)$ | $O(\log N)$ | **Yes** | **Yes** | **Yes** (Multi-bucket bins) | Binned $B_i$ | None | Moderate (Bandwidth intensive) |
| **Patel et al. (DVH)** [8] | USENIX Sec 2023 | $O(\|R(w)\|)$ amortized | $O(\text{polylog } N)$ | **Yes** | **Yes** | **Yes** (Oblivious storage) | Binned / $O(\log N)$ | None | Low (High client storage & bandwidth) |
| **Liu et al. (TrustZone-SSE)** [9] | IEEE TIFS 2021 | $O(\|R(w)\|)$ | $O(1)$ | **Yes** | **Yes** | No | Exact $|R(w)|$ | **Server TEE** (SGX / TrustZone) | Poor (Requires cloud enclave) |
| **VisioCrypt (Ours)** | **IEEE ICCIT 2026** | $\mathbf{O(1)}$ index lookup + $O(\Phi(\|R\|))$ | $\mathbf{O(1)}$ delta log | **Yes** (Versioned PRF) | **Yes** (Type-II Client-Side BF) | **Yes** (Multi-tiered Power-of-Two) | Padded $\lceil \log_2 \|R(w)\| \rceil$ | **Client-Side Only** (KeyMint / TrustZone) | **High** (Sub-ms latency, isolate zeroization) |

---

## 2. In-Depth Comparative Analysis

### 2.1 Foundational Schemes (Song et al. vs. Curtmola et al.)
- **Song, Wagner, and Perrig (SWP00)** [1]: Introduced the concept of searchable encryption. SWP00 encrypts words using a two-layered stream cipher and keyed pseudo-random function (PRF) construction ($C_i = W_i \oplus \langle L_i, R_i \rangle$). The client provides search tokens allowing the server to evaluate $R_i = f_{k}(L_i)$ without revealing the word. However, SWP00 requires an $O(N)$ sequential scan over the entire document ciphertext space, incurring severe computation and battery drain on mobile clients. It maintains no inverted index structure.
- **Curtmola, Garay, Kamara, and Ostrovsky (CGKO06)** [2]: Established formal simulation-based security definitions (adaptive IND-CKA2 security) and introduced the first inverted-index SSE construction based on array lookups, reducing query complexity to optimal $O(|R(w)|)$ time. However, CGKO06 is strictly static; inserting or deleting files requires rebuilding the entire inverted index.

### 2.2 Dynamic Forward- and Backward-Private SSE
- **Kamara, Papamanthou, and Roeder (KPR12)** [3]: Formalized dynamic SSE with update protocols. However, early dynamic schemes leak the association between past search queries and newly added documents, leaving them vulnerable to injection attacks (Zhang et al. USENIX Security 2016).
- **Bost (Sophos)** [5]: Introduced the formal definition of *Forward Privacy*: an update operation leaks nothing about the keywords contained in the newly added document, and the server cannot link new updates to previous search queries until the user re-executes the search. Sophos achieves this using asymmetric trapdoor permutations.
- **Bost, Minaud, and Ohrimenko (Diana)** [6]: Formalized *Backward Privacy* across three standard tiers (Type-I, Type-II, Type-III). Backward privacy ensures that search queries do not reveal document identifiers that were previously deleted. Diana achieved backward privacy using range-covering techniques and puncturable encryption, though with non-trivial storage overhead.
- **VisioCrypt's Dynamic Privacy Guarantees**:
  - *Forward Privacy*: Achieved via monotonic state counters per keyword ($w, v_w$) and incremental AES-256-GCM encrypted delta records. When a document is added, its encrypted delta log entry is unlinkable to prior search trapdoors.
  - *Backward Privacy (Type-II)*: Deletion is processed client-side using an in-memory Bloom filter combined with inverted index state reconciliation. The server never learns which documents were deleted until a subsequent search execution, leaking only the identifiers of currently matching documents and the count of updates $a_w$.

### 2.3 Volume-Hiding Searchable Encryption
- **The Volume Leakage Threat**: Conventional SSE reveals the exact result size $|R(w)|$ matching keyword $w$. Attackers observing query frequencies and result set sizes can reconstruct document databases using volumetric analysis (Kellaris et al. ACM CCS 2016, Gui et al. ACM CCS 2019).
- **SEAL (Demertzis et al. NDSS 2020)** [7] & **DVH (Patel et al. USENIX Sec 2023)** [8]: Introduced volume-hiding defenses. SEAL groups result sets into logarithmic binning classes, while Patel et al. utilized hierarchical oblivious data structures. While secure, they impose substantial client bandwidth expansion ($3\times$ to $10\times$) and high computational latency impractical for energy-constrained smartphones.
- **VisioCrypt's Approach**: Uses a multi-tiered client-side geometric padding policy $\Phi(R)$:
  - Results $n \le 4$ pad to 4 (floor).
  - Results $4 < n \le 4096$ pad to powers of two $2^{\lceil \log_2 n \rceil} \in \{8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096\}$.
  - Large results $n > 4096$ undergo multi-bucket chunking.
  - The server only ever observes coarse geometric bucket sizes $\lceil \log_2 |R(w)| \rceil$, slashing volumetric leakage while bounding mobile bandwidth overhead to an average of $< 1.5\times$.

### 2.4 Hardware Enclave Integration (Server TEE vs. Client TEE)
- **Server-Side Enclaves (Liu et al. IEEE TIFS 2021)** [9]: Place Intel SGX or ARM TrustZone on the cloud server to perform oblivious searches. However, this assumes cloud provider hardware trustworthiness, exposes the system to SGX side-channel attacks (Foreshadow, AEP), and requires costly enclave cloud hosting.
- **VisioCrypt's Client-Side Hardware Anchoring**: VisioCrypt anchors its master root secrets entirely on the *mobile client's* physical hardware security module (ARM TrustZone / Android KeyMint / StrongBox) gated by biometric authorization (`BiometricPrompt`). The cloud server remains completely untrusted (honest-but-curious), requiring zero server-side enclave hardware.
