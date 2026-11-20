import matplotlib.pyplot as plt
import numpy as np
import os

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 9,
    'axes.labelsize': 9,
    'axes.titlesize': 9.5,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 7.5,
    'pdf.fonttype': 42,
    'ps.fonttype': 42
})

# =========================================================================
# FIGURE 2: Volume-Hiding Padding Mechanism (Frequency Hiding)
# =========================================================================
def create_volume_padding_chart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.3), dpi=300)
    
    keywords = ['$w_1$', '$w_2$', '$w_3$', '$w_4$', '$w_5$', '$w_6$', '$w_7$', '$w_8$']
    raw_counts = [1, 2, 3, 5, 7, 11, 14, 22]
    padded_counts = [4, 4, 4, 8, 8, 16, 16, 32]
    
    x = np.arange(len(keywords))
    
    # Subplot 1: Unpadded (Vulnerable to Leakage)
    bars1 = ax1.bar(x, raw_counts, color='#e11d48', alpha=0.85, width=0.55, edgecolor='#9f1239')
    ax1.set_title('(a) Standard Unpadded Search\n(Exposes Exact Match Frequencies)', fontsize=8.5, fontweight='bold', color='#881337', pad=8)
    ax1.set_xlabel('Queried Keywords', fontsize=8)
    ax1.set_ylabel('Result Match Count', fontsize=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(keywords)
    ax1.set_ylim(0, 30)
    ax1.grid(axis='y', linestyle=':', alpha=0.6)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.9, str(int(yval)), ha='center', va='bottom', fontsize=7.5)
    
    # Subplot 2: VisioCrypt Power-of-Two Padding
    dummy_counts = [p - r for p, r in zip(padded_counts, raw_counts)]
    ax2.bar(x, dummy_counts, bottom=raw_counts, color='#93c5fd', alpha=0.85, width=0.55, edgecolor='#3b82f6', hatch='//', label='Dummy IDs')
    ax2.bar(x, raw_counts, color='#2563eb', alpha=0.85, width=0.55, edgecolor='#1e40af', label='Real Match IDs')

    ax2.set_title('(b) VisioCrypt Power-of-Two Padding\n(Clustered into Uniform Buckets)', fontsize=8.5, fontweight='bold', color='#1e3a8a', pad=8)
    ax2.set_xlabel('Queried Keywords', fontsize=8)
    ax2.set_ylabel('Server-Observed Bucket Size', fontsize=8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(keywords)
    ax2.set_ylim(0, 44)
    ax2.grid(axis='y', linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', framealpha=0.92, fontsize=7)
    
    for i, pval in enumerate(padded_counts):
        ax2.text(x[i], pval + 1.2, f"{pval}",
                 ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#1e3a8a')

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig_volume_padding.pdf'), bbox_inches='tight')
    plt.close()
    print("Saved fig_volume_padding.pdf")

# =========================================================================
# FIGURE 3: Multi-Device Search Query Latency
# =========================================================================
def create_latency_benchmark_chart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.3), dpi=300)

    devices = ['Redmi K80\n(Tier 1)', 'Turbo 4 Pro\n(Tier 2)', 'Pixel 7a\n(Tier 3)', 'Galaxy A14\n(Tier 4)']
    
    linear_scan = [3420, 4150, 8420, 18650] # ms
    sql_cipher = [5.20, 6.80, 14.20, 34.80] # ms
    unpadded_sse = [0.21, 0.26, 0.58, 1.42] # ms
    visiocrypt = [0.23, 0.29, 0.62, 1.48] # ms
    
    x = np.arange(len(devices))
    width = 0.22

    # Left: Linear Scan vs Encrypted Index (Log Scale)
    ax1.bar(x - width/2, linear_scan, width, label='Linear Scan (Raw Files)', color='#ef4444', edgecolor='#b91c1c')
    ax1.bar(x + width/2, sql_cipher, width, label='SQLCipher Encrypted DB', color='#f59e0b', edgecolor='#d97706')
    ax1.set_yscale('log')
    ax1.set_ylabel('Execution Time (ms, Log Scale)', fontsize=8)
    ax1.set_title('(a) Baseline Mobile Search Overheads', fontsize=8.5, fontweight='bold', pad=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(devices, fontsize=7.5)
    ax1.grid(axis='y', linestyle=':', alpha=0.6)
    ax1.set_ylim(1, 50000)
    ax1.legend(loc='upper left', fontsize=7)

    # Right: Unpadded vs VisioCrypt (Power-of-Two Padded) Sub-millisecond Search
    ax2.bar(x - width/2, unpadded_sse, width, label='Unpadded Searchable Index', color='#64748b', edgecolor='#334155')
    bars = ax2.bar(x + width/2, visiocrypt, width, label='VisioCrypt (Volume-Hiding)', color='#10b981', edgecolor='#047857')
    ax2.set_ylabel('Lookup Latency (ms)', fontsize=8)
    ax2.set_title('(b) VisioCrypt Sub-Millisecond Speed', fontsize=8.5, fontweight='bold', pad=8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(devices, fontsize=7.5)
    ax2.set_ylim(0, 2.1)
    ax2.grid(axis='y', linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', fontsize=7)

    for i in range(len(devices)):
        ax2.text(x[i] + width/2, visiocrypt[i] + 0.06, f"{visiocrypt[i]}ms", ha='center', va='bottom', fontsize=7.0, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig_search_latency.pdf'), bbox_inches='tight')
    plt.close()
    print("Saved fig_search_latency.pdf")

# =========================================================================
# FIGURE 4: Throughput & Memory Zeroization
# =========================================================================
def create_throughput_and_memory_chart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 2.3), dpi=300)

    devices = ['K80\n(Tier 1)', 'Turbo 4\n(Tier 2)', 'Pixel 7a\n(Tier 3)', 'Galaxy A14\n(Tier 4)']
    gcm_tp = [248.6, 215.4, 112.6, 48.2]
    ctr_hmac_tp = [310.5, 265.2, 142.8, 68.4]

    x = np.arange(len(devices))
    width = 0.32

    # (a) Symmetric Throughput
    ax1.bar(x - width/2, gcm_tp, width, label='AES-GCM-256', color='#6366f1', edgecolor='#4338ca')
    bars = ax1.bar(x + width/2, ctr_hmac_tp, width, label='AES-CTR-256 + HMAC', color='#0ea5e9', edgecolor='#0284c7')
    ax1.set_ylabel('Throughput (MB/s)', fontsize=8)
    ax1.set_title('(a) File Encryption Throughput', fontsize=8.5, fontweight='bold', pad=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(devices, fontsize=7.5)
    ax1.set_ylim(0, 390)
    ax1.grid(axis='y', linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=7)

    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 7, f"{int(yval)}", ha='center', va='bottom', fontsize=7.0, fontweight='bold')

    # (b) Key Lifetime in Physical RAM
    time_pts = np.linspace(0, 180, 200) # seconds
    gc_retention = np.where(time_pts < 135, 100, np.exp(-(time_pts - 135)/15)*100)
    visio_retention = np.where(time_pts < 0.5, 100, 0)

    ax2.plot(time_pts, gc_retention, color='#dc2626', linewidth=1.8, linestyle='--', label='Standard GC Runtime (Vulnerable)')
    ax2.fill_between(time_pts, gc_retention, color='#fee2e2', alpha=0.45)
    ax2.plot(time_pts, visio_retention, color='#16a34a', linewidth=2.2, label='VisioCrypt Immediate Zeroization')
    ax2.set_xlabel('Elapsed Time (seconds)', fontsize=8)
    ax2.set_ylabel('Key Persistence in RAM (%)', fontsize=8)
    ax2.set_title('(b) Physical RAM Key Lifetime', fontsize=8.5, fontweight='bold', pad=8)
    ax2.set_ylim(-5, 120)
    ax2.set_xlim(0, 180)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='center right', fontsize=6.8)
    ax2.text(25, 20, "Immediate Wipe ($<1$ ms)", fontsize=7.0, color='#15803d', fontweight='bold')
    ax2.annotate('', xy=(1, 5), xytext=(25, 20),
                 arrowprops=dict(facecolor='#16a34a', edgecolor='#15803d', width=1.0, headwidth=4))

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig_throughput_benchmark.pdf'), bbox_inches='tight')
    plt.close()
    print("Saved fig_throughput_benchmark.pdf")

if __name__ == '__main__':
    create_volume_padding_chart()
    create_latency_benchmark_chart()
    create_throughput_and_memory_chart()
    print("Figures 2, 3, 4 regenerated with perfect margins!")
