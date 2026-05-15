# ABM: Active Buffer Management in Datacenter Networks

This repository contains an ns-3 based reproduction and extension of the SIGCOMM’22 paper:

> **ABM: Active Buffer Management in Datacenters**  
> Vamsi Addanki et al., ACM SIGCOMM 2022

The project reproduces the core ABM evaluation and extends it with:
- **Incast arrival-rate sensitivity analysis**
- **ML-based α tuning for Dynamic Thresholds (DT)**

---

# Project Overview

Modern datacenter traffic is:
- bursty
- latency-sensitive
- incast-heavy

ABM improves datacenter performance by jointly considering:
- **buffer occupancy**
- **queue drain time**

This repository evaluates ABM against:
- DT (Dynamic Threshold)
- FAB (Flow-Aware Buffer)
- CS (Complete Sharing)
- IB (Intelligent Buffer)

using packet-level simulation in **ns-3.39**.

---

# Key Contributions

## 1. ABM Paper Replication
Reproduced the core experiments from the original ABM paper using a scaled-down topology.

### Experiments
- Load sweep (0.2 → 0.8)
- Burst-size sweep

### Metrics
- Short-flow slowdown
- 99th percentile FCT slowdown
- Buffer occupancy
- Throughput

### Findings
- ABM achieves lowest tail latency
- ABM uses significantly less buffer
- Throughput remains unchanged across schemes

---

## 2. Incast Sensitivity Analysis
Extended the evaluation by varying incast arrival rate.

### Experiments
- Incast rate sweep: 1, 2, 5 req/sec

### Findings
- Performance is primarily driven by network load
- Latency is relatively insensitive to incast frequency
- ABM remains robust across all tested rates

---

## 3. Adaptive α vs Static α Analysis
Investigated whether ABM’s advantage comes from adaptivity or parameter tuning.

### Approach
- Swept DT across multiple α values
- Used Gaussian Process regression to identify the best static α

### Findings
- ABM still outperforms the best-tuned static DT configuration
- Demonstrates the benefit of adaptive behavior over fixed tuning

---

# Repository Structure

```text
ns3-datacenter/
│
├── simulator/ns-3.39/
│   ├── src/
│   │   └── traffic-control/
│   │       └── model/
│   │           └── gen-queue-disc.cc
│   │
│   ├── examples/ABM/
│   │   ├── run-main-bufalg-load.sh
│   │   ├── run-main-bufalg-burst.sh
│   │   ├── run-main-bufalg-incastrate.sh
│   │   ├── plots/
│   │   └── plots2/
│   │
│   └── build/
│
└── README.md
```

---

# Prerequisites

## macOS

Install required packages using Homebrew:

```bash
brew update
brew install python pkg-config gsl sqlite3 libxml2
```

Optional Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

---

# Building ns-3

```bash
cd ns3-datacenter/simulator/ns-3.39

./waf configure --enable-examples --enable-tests
./waf build -j 4
```

---

# Quick Start

Move to the ABM experiment directory:

```bash
cd ns3-datacenter/simulator/ns-3.39/examples/ABM
source config.sh
```

---

# Running Experiments

## Load Sweep

```bash
./run-main-bufalg-load.sh
```

---

## Burst Size Sweep

```bash
./run-main-bufalg-burst.sh
```

---

## Incast Arrival-Rate Sweep

```bash
./run-main-bufalg-incastrate.sh
```

---

# Plot Generation

Generate plots using:

```bash
python3 plots/plots_sigcomm.py
python3 plots/analyze_incastrate.py
```

---

# Results

Generated plots and parsed outputs are stored in:

```text
examples/ABM/plots/
examples/ABM/plots2/
examples/ABM/plots/generated_plots/
```

Example output files:

```text
results-summary.csv
results-all.dat
results-myexp*.dat
```

---

# Simulation Details

## Topology
- Leaf-spine datacenter topology
- 16 servers
- 2 leaf switches
- 1 spine switch

## Network Configuration
- 10 Gbps links
- 10 μs latency
- TCP Cubic

## Workload
- Web Search CDF
- Incast traffic
- Burst size: 0.3 × buffer

---

# Reproducibility

This project is designed for reproducible experimentation using:
- ns-3.39
- fixed workloads
- parameterized run scripts
- automated plot generation

---

# Acknowledgements

This project builds upon the public ABM ns-3 implementation released by the original authors:

https://github.com/inet-tub/ns3-datacenter