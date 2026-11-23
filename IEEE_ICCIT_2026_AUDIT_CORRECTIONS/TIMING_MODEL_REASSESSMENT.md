# Forensic Reassessment: Timing Correlation Channel & Information-Theoretic Modeling

**Subject:** Formalization of Adversarial Timing Channel, Hypothesis Testing, and Python Simulation Reclassification  
**Manuscript:** Paper ID 2015 ("VisioCrypt")  
**Target Directory:** `IEEE_ICCIT_2026_AUDIT_CORRECTIONS/TIMING_MODEL_REASSESSMENT.md`  
**Auditor:** Senior Theoretical Cryptographer & Detection Theorist  
**Date:** November 2026  

---

## 1. Executive Summary & Problem Formulation

In Section VII-B and Figure 2(b) of `2015_Revised_Manuscript.tex` and Section 4 of `2015_Validation_Report.md`, the authors asserted:
> *"Empirical evaluation... Adversary profiling accuracy under timing correlation attacks: while unmitigated and random-delayed queries allow the adversary to achieve 100% classification accuracy within M=5 observations, VisioCrypt's QueryDecorrelationPool caps adversary accuracy at 50.6%."*

### 1.1. Root Defect of Previous Claim
1. **Script Audit:** In `IEEE_ICCIT_2026_REVISION/2015_Experimental_Results/timing_and_padding_experiments.py` (Line 87), the adversary's prediction was explicitly programmed as:
   ```python
   pred_pool = np.random.choice([0, 1])
   acc_pool.append(1 if pred_pool == true_class else 0)
   ```
2. **Empirical Defect:** The reported $50.6\%$ accuracy over 500 trials was purely the realization of 500 pseudo-random Bernoulli($0.5$) coin flips ($253 / 500 = 50.6\%$).
3. **Manuscript Defect:** Describing a synthetic random coin toss as an "empirical evaluation of an adversary" violates scientific reporting standards.

This reassessment provides the **rigorous mathematical foundation** required to analyze when epoch batching decorrelates timing observations, defines the exact hypothesis testing problem, and formally reclassifies the Python script as a **synthetic mathematical illustration**.

---

## 2. Formal Detection-Theoretic Formulation of the Timing Channel

We formulate the timing correlation attack as a binary hypothesis testing problem on an observation transcript observed by an eavesdropping or honest-but-curious cloud adversary.

### 2.1. System Model & Observable Transcript
Let a client issue a sequence of $M$ search queries over a communications channel.
- Let $t_1, t_2, \dots, t_M \in \mathbb{R}^+$ denote the absolute physical dispatch timestamps of the queries observed at the cloud server boundary.
- The adversary's observable transcript is the vector of successive inter-arrival intervals:
  $$\mathcal{T} = (\Delta t_1, \Delta t_2, \dots, \Delta t_{M-1}) \in \mathbb{R}_+^{M-1}, \quad \text{where } \Delta t_i = t_{i+1} - t_i.$$

### 2.2. The Secret Classification Variable
Let $Y \in \{0, 1\}$ denote the binary secret behavioral state of the client:
- $Y = 0$: Interactive user typing (e.g., keystroke-driven keyword autocompletion with typical inter-keystroke delays $\mu_0 \approx 120$ ms).
- $Y = 1$: Automated batch processing or background synchronization (e.g., batch index update with inter-query delays $\mu_1 \approx 300$ ms).
- Alternatively, $Y \in \{0, 1\}$ represents querying sensitive Keyword Class $A$ versus sensitive Keyword Class $B$ with distinct typing cadence distributions.

### 2.3. Prior Distribution
Let the prior probability distribution of the secret state be:
$$\pi_0 = P(Y = 0), \quad \pi_1 = P(Y = 1) = 1 - \pi_0.$$
In the standard symmetric adversarial model, $\pi_0 = \pi_1 = \frac{1}{2}$.

### 2.4. Conditional Likelihood Distributions
Under the unmitigated channel:
- When $Y = 0$, intervals follow distribution $f_{\mathcal{T} \mid Y}(\mathbf{t} \mid 0) \sim \prod_{i=1}^{M-1} \mathcal{N}(\mu_0, \sigma_0^2)$.
- When $Y = 1$, intervals follow distribution $f_{\mathcal{T} \mid Y}(\mathbf{t} \mid 1) \sim \prod_{i=1}^{M-1} \mathcal{N}(\mu_1, \sigma_1^2)$.

Because $\mu_0 = 120$ ms and $\mu_1 = 300$ ms with moderate variances ($\sigma_0, \sigma_1 \approx 30$ ms), the distributions are separated:
$$\frac{|\mu_1 - \mu_0|}{\sqrt{\sigma_0^2 + \sigma_1^2}} = \frac{180}{42.4} \approx 4.24.$$
For $M \ge 5$ observations, the sample mean $\bar{\Delta t}$ provides almost perfect hypothesis separation, yielding adversary classification accuracy:
$$\text{Acc}_{\text{unmit}} \to 1.0 \quad (100\%).$$

---

## 3. Bayes Optimal Classifier & Total Variation Distance

The adversary's goal is to construct a decision rule $\delta: \mathbb{R}_+^{M-1} \to \{0, 1\}$ that maximizes classification accuracy:
$$\text{Acc}(\delta) = P(\delta(\mathcal{T}) = Y).$$

By the Neyman-Pearson lemma and Bayes decision theory, the optimal classifier is the maximum a posteriori (MAP) rule:
$$\delta^*(\mathcal{T}) = \arg\max_{y \in \{0, 1\}} P(Y = y \mid \mathcal{T}) = \begin{cases} 0 & \text{if } \frac{f_{\mathcal{T} \mid Y}(\mathcal{T} \mid 0)}{f_{\mathcal{T} \mid Y}(\mathcal{T} \mid 1)} \ge \frac{\pi_1}{\pi_0} \\ 1 & \text{otherwise} \end{cases}$$

### 3.1. Fundamental Limit on Adversary Accuracy
The minimum achievable Bayes error rate $P_e^*$ is directly governed by the **Total Variation Distance** $\| \cdot \|_{\text{TV}}$ between the conditional observation distributions:
$$P_e^* = \frac{1}{2} - \frac{1}{2} \| P_{\mathcal{T} \mid Y=0} - P_{\mathcal{T} \mid Y=1} \|_{\text{TV}}$$

Consequently, the optimal adversary accuracy is bounded by:
$$\text{Acc}^* = 1 - P_e^* = \frac{1}{2} + \frac{1}{2} \| P_{\mathcal{T} \mid Y=0} - P_{\mathcal{T} \mid Y=1} \|_{\text{TV}}.$$

---

## 4. Rigorous Conditions for 50% Bayes Accuracy (Decorrelation)

To establish that an adversary cannot exceed random guessing ($\text{Acc}^* = \frac{1}{2} = 50\%$), the defense mechanism must guarantee that:
$$\| P_{\mathcal{T} \mid Y=0} - P_{\mathcal{T} \mid Y=1} \|_{\text{TV}} = 0 \iff P(\mathcal{T} \mid Y = 0) \equiv P(\mathcal{T} \mid Y = 1).$$

This condition holds **if and only if** the observation transcript $\mathcal{T}$ is statistically independent of the secret $Y$, which implies that the mutual information vanishes:
$$I(Y; \mathcal{T}) = 0.$$

### 4.1. The Necessary Architectural Assumptions for Statistical Independence

To guarantee $I(Y; \mathcal{T}) = 0$, VisioCrypt's `QueryDecorrelationPool` must strictly satisfy the following four physical assumptions:

1. **Strict Epoch Quantization ($T_e$):**
   - Transmissions occur **exclusively** at discrete epoch ticks $t_k = k \cdot T_e$, where $T_e$ is a fixed system epoch duration (e.g., $T_e = 100$ ms).
   - Any query generated at time $t$ where $(k-1)T_e < t \le k T_e$ is queued until $k T_e$.

2. **State-Independent Dummy Injection Distribution:**
   - At each epoch boundary $k T_e$, the pool must emit a number of tokens $K_k$ according to a fixed probability distribution $P_K(k)$ that is completely invariant to user activity $Y$.
   - In a single-token pool ($K_k \in \{0, 1\}$), the dispatch decision $D_k \in \{0, 1\}$ must follow an independent Bernoulli distribution $\text{Bernoulli}(p)$:
     - If the user query queue is non-empty, a genuine trapdoor is emitted.
     - If the queue is empty, a dummy trapdoor $T_{\text{dummy}} = \text{HMAC}(K, \text{random})$ is emitted with probability $p$.
   - Because $T_{\text{dummy}}$ is computationally indistinguishable from genuine trapdoors under the PRF security of HMAC, the server cannot distinguish dummy tokens from real queries.

3. **Absence of Buffer Overflow / Queue Length Coupling:**
   - The user query generation rate $\lambda_{\text{user}}$ must not exceed the channel epoch throughput:
     $$\lambda_{\text{user}} < \frac{1}{T_e}.$$
   - If $\lambda_{\text{user}} > 1/T_e$, client queue depth builds up, inducing cross-epoch burst delays that re-introduce timing correlation.

4. **Negligible Network Jitter Distortion:**
   - The transmission delay $\delta_{\text{net}}$ introduced by the mobile cellular/Wi-Fi link must be independent and identically distributed (i.i.d.) and not dependent on packet content or burst size:
     $$\delta_{\text{net}} \sim \mathcal{D}_{\text{net}}, \quad \mathcal{D}_{\text{net}} \perp Y.$$

### 4.2. Mathematical Proof of Decorrelation Under the Model
Under Assumptions 1–4:
- The observed inter-arrival time is $\Delta t_i = (k_{i+1} - k_i) T_e + (\delta_{i+1} - \delta_i)$.
- The epoch increments $\Delta k_i = k_{i+1} - k_i$ are governed entirely by the parameter $p$ of the Bernoulli dummy process:
  $$P(\Delta k_i = m) = p (1 - p)^{m-1}, \quad m \in \{1, 2, \dots\}$$
- This distribution is completely determined by system parameter $p$ and is mathematically independent of $Y$:
  $$P(\mathcal{T} \mid Y = 0) = P(\mathcal{T} \mid Y = 1) = \prod_{i=1}^{M-1} P(\Delta t_i).$$
- Substituting into the Bayes error bound:
  $$\| P_{\mathcal{T} \mid Y=0} - P_{\mathcal{T} \mid Y=1} \|_{\text{TV}} = 0 \implies \text{Acc}^* = \frac{1}{2} = 50\%.$$

---

## 5. Realistic Breakdown Conditions & Practical Mobile Limitations

In a real-world mobile deployment, strict independence can degrade due to:

1. **Jitter-Induced Epoch Blurring:**
   If network transmission delay jitter $\sigma_{\text{jitter}}$ is comparable to epoch size ($\sigma_{\text{jitter}} \approx T_e$), packet arrivals from adjacent epochs can interleave, creating timing variance.
2. **Cellular Power-Save States (e.g., C-DRX):**
   Modern 5G/LTE modems enter Connected-Mode Discontinuous Reception (C-DRX). Waking up the baseband processor to transmit dummy tokens incurs radio wake-up latencies ($\approx 15$--$25$ ms), imprinting a physical hardware delay signature on the first token of a burst.
3. **Battery Overhead of Continuous Dummies:**
   Transmitting dummy queries at every epoch rapidly drains mobile battery and consumes mobile cellular data quota. In practice, mobile clients must throttle dummy emission during prolonged idle periods.

---

## 6. Formal Reclassification of the Python Simulation Script

`IEEE_ICCIT_2026_REVISION/2015_Experimental_Results/timing_and_padding_experiments.py` must be formally reclassified in the research record:

| Aspect | What Was Claimed | Forensic Reality | Required Resubmission Action |
| :--- | :--- | :--- | :--- |
| **Methodology** | "Empirical adversarial evaluation" | **Synthetic Mathematical Illustration** | Retitle script and section to: *"Analytical Simulation of Ideal Epoch Batching Model"*. |
| **Adversary Code** | Classification algorithm evaluating packet delays | `np.random.choice([0, 1])` | Remove line 87 or state explicitly: *"In an ideal decorrelation model with $I(Y; \mathcal{T})=0$, adversary classification degenerates to the prior distribution (a 50% coin flip)."* |
| **50.6% Number** | Measured accuracy of a real attack tool | Sample mean of 500 coin tosses | Replace $50.6\%$ with the theoretical limit: *"Under the ideal epoch-quantized Poisson/Bernoulli dummy model, the adversary's Bayes error rate is bounded below by 0.5 (random guessing)."* |
