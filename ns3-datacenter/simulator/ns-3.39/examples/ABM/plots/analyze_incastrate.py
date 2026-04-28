#!/usr/bin/env python3
"""
Parse and analyze incastrate experiment results.
Tests how ABM performs under varying incast arrival rates (1, 2, 5 queries/s).
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Setup
DUMP_DIR = Path("/Users/shreyahegde/ABM-Datacenter-Networks/ns3-datacenter/simulator/ns-3.39/examples/ABM/dump_sigcomm")
PLOTS_DIR = Path("/Users/shreyahegde/ABM-Datacenter-Networks/ns3-datacenter/simulator/ns-3.39/examples/ABM/plots")
PLOTS_DIR.mkdir(exist_ok=True)

ALG_MAP = {101: "DT", 102: "FAB", 103: "CS", 104: "IB", 110: "ABM"}
COLORS = {"DT": "#1f77b4", "FAB": "#ff7f0e", "CS": "#2ca02c", "IB": "#d62728", "ABM": "#9467bd"}

def parse_flow_file(flow_file, rtt=20, linerate=10):
    """Parse FCT file and extract slowdown metrics."""
    bdp = linerate * 1e9 * rtt * 1e-6 / 8
    
    df = pd.read_csv(flow_file, sep=r"\s+")
    
    short_flows = df[(df["flowsize"] < bdp) & (df["incast"] == 0)]["slowdown"].tolist()
    incast_flows = df[(df["incast"] == 1)]["slowdown"].tolist()
    
    def summarize(values):
        if len(values) == 0:
            return [0, 0, 0, 0, 0]
        values = sorted(values)
        return [
            values[max(0, int(len(values) * 0.999) - 1)],  # p99.9
            values[max(0, int(len(values) * 0.99) - 1)],   # p99
            values[max(0, int(len(values) * 0.95) - 1)],   # p95
            float(np.mean(values)),                          # avg
            float(np.median(values)),                        # median
        ]
    
    short999, short99, short95, shortavg, shortmed = summarize(short_flows)
    incast999, incast99, incast95, incastavg, incastmed = summarize(incast_flows)
    
    return {
        "short99.9": short999,
        "short99": short99,
        "short95": short95,
        "short_avg": shortavg,
        "short_med": shortmed,
        "incast99.9": incast999,
        "incast99": incast99,
        "incast95": incast95,
        "incast_avg": incastavg,
        "incast_med": incastmed,
    }

# Parse all incastrate results
results = []

for alg_id, alg_name in ALG_MAP.items():
    for load in [0.4, 0.6, 0.8]:
        for rate in [1, 2, 5]:
            fct_file = DUMP_DIR / f"fcts-incastrate-1-{alg_id}-{load}-0.3-{rate}.fct"
            
            if fct_file.exists():
                metrics = parse_flow_file(str(fct_file))
                metrics.update({
                    "alg": alg_name,
                    "alg_id": alg_id,
                    "load": load,
                    "rate": rate,
                })
                results.append(metrics)

results_df = pd.DataFrame(results)

# Display summary
print("=" * 80)
print("INCAST RATE EXTENSION: Analysis of ABM under varying query arrival rates")
print("=" * 80)
print(f"\nParsed {len(results_df)} experiment runs")
print(f"Algorithms: {', '.join(ALG_MAP.values())}")
print(f"Loads: {sorted(results_df['load'].unique())}")
print(f"Incast Rates (queries/s): {sorted(results_df['rate'].unique())}")

# Summary statistics
print("\n" + "=" * 80)
print("AVG SHORT FLOW SLOWDOWN (by Algorithm and Incast Rate at Load=0.4)")
print("=" * 80)
summary = results_df[results_df['load'] == 0.4].groupby(['alg', 'rate'])['short_avg'].mean().unstack()
print(summary.to_string())

print("\n" + "=" * 80)
print("AVG INCAST FLOW SLOWDOWN (by Algorithm and Incast Rate at Load=0.4)")
print("=" * 80)
summary_incast = results_df[results_df['load'] == 0.4].groupby(['alg', 'rate'])['incast_avg'].mean().unstack()
print(summary_incast.to_string())

# Plot 1: Short flow slowdown vs incast rate (fixed load=0.4)
plt.figure(figsize=(10, 6))
for alg in ALG_MAP.values():
    data = results_df[(results_df['alg'] == alg) & (results_df['load'] == 0.4)]
    data = data.sort_values('rate')
    plt.plot(data['rate'], data['short_avg'], marker='o', label=alg, 
             color=COLORS[alg], linewidth=2, markersize=8)

plt.xlabel('Incast Arrival Rate (queries/s)', fontsize=12)
plt.ylabel('Short Flow Slowdown (avg)', fontsize=12)
plt.title('Impact of Incast Rate on Short Flows (Load=0.4)', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'incastrate_short_flows.png', dpi=150)
print(f"\n✓ Saved: incastrate_short_flows.png")

# Plot 2: Incast flow slowdown vs incast rate (fixed load=0.4)
plt.figure(figsize=(10, 6))
for alg in ALG_MAP.values():
    data = results_df[(results_df['alg'] == alg) & (results_df['load'] == 0.4)]
    data = data.sort_values('rate')
    plt.plot(data['rate'], data['incast_avg'], marker='s', label=alg, 
             color=COLORS[alg], linewidth=2, markersize=8)

plt.xlabel('Incast Arrival Rate (queries/s)', fontsize=12)
plt.ylabel('Incast Flow Slowdown (avg)', fontsize=12)
plt.title('Impact of Incast Rate on Incast Flows (Load=0.4)', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'incastrate_incast_flows.png', dpi=150)
print(f"✓ Saved: incastrate_incast_flows.png")

# Plot 3: Heatmap of incast rate impact
plt.figure(figsize=(10, 6))
pivot_data = results_df[results_df['load'] == 0.4].pivot_table(
    values='short_avg', index='alg', columns='rate'
)
sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='RdYlGn_r', cbar_kws={'label': 'Slowdown'})
plt.title('Short Flow Slowdown: Algorithm vs Incast Rate (Load=0.4)', fontsize=14)
plt.ylabel('Algorithm', fontsize=12)
plt.xlabel('Incast Rate (queries/s)', fontsize=12)
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'incastrate_heatmap.png', dpi=150)
print(f"✓ Saved: incastrate_heatmap.png")

# Plot 4: Multi-load comparison for ABM
plt.figure(figsize=(12, 6))
for load in [0.4, 0.6, 0.8]:
    data = results_df[(results_df['alg'] == 'ABM') & (results_df['load'] == load)]
    data = data.sort_values('rate')
    plt.plot(data['rate'], data['short_avg'], marker='o', label=f'Load={load}', 
             linewidth=2, markersize=8)

plt.xlabel('Incast Arrival Rate (queries/s)', fontsize=12)
plt.ylabel('Short Flow Slowdown (avg)', fontsize=12)
plt.title('ABM Performance Across Different Network Loads and Incast Rates', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'incastrate_abm_multiload.png', dpi=150)
print(f"✓ Saved: incastrate_abm_multiload.png")

print("\n" + "=" * 80)
print("All plots saved to:", PLOTS_DIR)
print("=" * 80)
