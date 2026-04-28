"""
ML-driven alpha optimization for buffer management.

Trains a Gaussian Process regression model on a sweep of DT (static-alpha) runs,
then uses the model to predict the optimal alpha per load. Compares predicted-optimal
DT against ABM (adaptive alpha) using existing data.

Pipeline:
1. Load alpha-sweep results from results-alphasweep.dat (15 rows: 5 alphas x 3 loads)
2. Load ABM baseline from results-all.dat (3 rows: ABM at loads 0.4, 0.6, 0.8)
3. Fit GP regression: (load, log2(alpha)) -> log(short99fct)
4. Search over alpha grid per load -> predict optimal alpha
5. Plot: heatmap, best-alpha-per-load, ABM vs best-static, GP uncertainty
6. Write predictions to predicted_alphas.txt for run-validation.sh

Run from the plots/ directory:
    python3 ml_alpha.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.preprocessing import StandardScaler

# ----------------- Config -----------------
SWEEP_FILE = "results-alphasweep.dat"
BASELINE_FILE = "results-all.dat"
VALIDATION_FILE = "results-validation.dat"
OUT_DIR = "generated_plots"
PREDICTIONS_FILE = "predicted_alphas.txt"
TARGET_METRIC = "short99fct"  # the metric to minimize
ALG_DT = 101
ALG_ABM = 110
ALPHA_GRID = np.geomspace(0.03125, 2.0, 100)  # fine grid for prediction
LOADS = [0.4, 0.6, 0.8]

os.makedirs(OUT_DIR, exist_ok=True)
sns.set_theme(style="whitegrid")


# ----------------- Data loading -----------------
def load_sweep():
    if not os.path.exists(SWEEP_FILE):
        sys.exit(f"ERROR: {SWEEP_FILE} not found. Run parse-alphasweep.sh first.")
    df = pd.read_csv(SWEEP_FILE, sep=r"\s+")
    # The sweep parser tags scenario='alphasweep' and adds alpha_bg as last column
    df = df[df["scenario"] == "alphasweep"].copy()
    df["alpha_bg"] = df["alpha_bg"].astype(float)
    df["load"] = df["load"].astype(float)
    df[TARGET_METRIC] = df[TARGET_METRIC].astype(float)
    return df.reset_index(drop=True)


def load_abm_baseline():
    if not os.path.exists(BASELINE_FILE):
        sys.exit(f"ERROR: {BASELINE_FILE} not found. Run results.sh first.")
    df = pd.read_csv(BASELINE_FILE, sep=r"\s+")
    df = df[(df["alg"] == ALG_ABM) & (df["scenario"] == "single")].copy()
    df["load"] = df["load"].astype(float)
    df[TARGET_METRIC] = df[TARGET_METRIC].astype(float)
    return df.reset_index(drop=True)


def load_validation():
    """Load validation runs (DT measured at ML-predicted optimal alphas). Returns None if absent."""
    if not os.path.exists(VALIDATION_FILE):
        return None
    df = pd.read_csv(VALIDATION_FILE, sep=r"\s+")
    df = df[df["scenario"] == "validation"].copy()
    if df.empty:
        return None
    df["alpha_bg"] = df["alpha_bg"].astype(float)
    df["load"] = df["load"].astype(float)
    df[TARGET_METRIC] = df[TARGET_METRIC].astype(float)
    return df.reset_index(drop=True)


# ----------------- ML model -----------------
def fit_gp(df):
    """Fit Gaussian Process: features = (load, log2(alpha)), target = log(short99fct)."""
    X = np.column_stack([df["load"].values, np.log2(df["alpha_bg"].values)])
    y = np.log(df[TARGET_METRIC].values)

    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    kernel = ConstantKernel(1.0, (0.01, 10.0)) * RBF(
        length_scale=[1.0, 1.0], length_scale_bounds=(0.1, 10.0)
    ) + WhiteKernel(noise_level=0.01, noise_level_bounds=(1e-5, 1.0))

    gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, n_restarts_optimizer=10)
    gp.fit(Xs, y)
    return gp, scaler


def predict(gp, scaler, load, alpha):
    X = np.array([[load, np.log2(alpha)]])
    Xs = scaler.transform(X)
    mu_log, sd_log = gp.predict(Xs, return_std=True)
    return float(np.exp(mu_log[0])), float(sd_log[0])


def predict_grid(gp, scaler, loads, alphas):
    """Returns (n_loads, n_alphas) arrays of predicted mean and stddev."""
    XX, YY = np.meshgrid(loads, np.log2(alphas), indexing="ij")
    grid = np.column_stack([XX.ravel(), YY.ravel()])
    grid_s = scaler.transform(grid)
    mu_log, sd_log = gp.predict(grid_s, return_std=True)
    mu = np.exp(mu_log).reshape(XX.shape)
    sd = sd_log.reshape(XX.shape)
    return mu, sd


# ----------------- Plots -----------------
def plot_heatmap(df, gp, scaler):
    """Heatmap of predicted short99fct over (load, alpha) grid, with sweep points overlaid."""
    fine_loads = np.linspace(0.4, 0.8, 30)
    fine_alphas = np.geomspace(0.03125, 2.0, 60)
    mu, _ = predict_grid(gp, scaler, fine_loads, fine_alphas)

    plt.figure(figsize=(9, 6))
    extent = [np.log2(fine_alphas[0]), np.log2(fine_alphas[-1]), fine_loads[0], fine_loads[-1]]
    plt.imshow(mu, aspect="auto", origin="lower", extent=extent, cmap="viridis_r")
    cbar = plt.colorbar(label="Predicted 99p Short FCT slowdown")
    # Overlay actual sweep points
    plt.scatter(np.log2(df["alpha_bg"]), df["load"], c="white", edgecolor="black", s=70, label="Sweep observations")
    plt.xlabel("log2(alpha_bg)")
    plt.ylabel("Load")
    plt.title("ML-predicted 99p slowdown over (load, alpha) — DT static-alpha sweep")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/ml_heatmap_alpha_load.png", dpi=200)
    plt.close()
    print(f"  wrote {OUT_DIR}/ml_heatmap_alpha_load.png")


def plot_best_alpha_per_load(gp, scaler):
    """For each load in 0.4..0.8, find argmin alpha via fine grid search."""
    fine_loads = np.linspace(0.4, 0.8, 41)
    best_alphas = []
    best_predictions = []
    best_uncertainty = []
    for L in fine_loads:
        ms, sds = [], []
        for a in ALPHA_GRID:
            mu, sd = predict(gp, scaler, L, a)
            ms.append(mu)
            sds.append(sd)
        ms = np.array(ms)
        sds = np.array(sds)
        i_min = int(np.argmin(ms))
        best_alphas.append(ALPHA_GRID[i_min])
        best_predictions.append(ms[i_min])
        best_uncertainty.append(sds[i_min])

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].plot(fine_loads, best_alphas, "o-", color="tab:blue")
    axes[0].set_yscale("log", base=2)
    axes[0].set_xlabel("Load")
    axes[0].set_ylabel("ML-predicted optimal alpha")
    axes[0].set_title("Optimal static alpha vs load (ML prediction)")
    axes[0].grid(True, which="both", alpha=0.4)

    axes[1].plot(fine_loads, best_predictions, "o-", color="tab:green", label="Predicted FCT (best alpha)")
    axes[1].fill_between(
        fine_loads,
        np.array(best_predictions) * np.exp(-np.array(best_uncertainty)),
        np.array(best_predictions) * np.exp(np.array(best_uncertainty)),
        alpha=0.25,
        color="tab:green",
        label="GP uncertainty (1σ)",
    )
    axes[1].set_xlabel("Load")
    axes[1].set_ylabel("Predicted 99p slowdown at optimal alpha")
    axes[1].set_title("Best-case static-alpha 99p FCT (ML prediction)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.4)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/ml_best_alpha_per_load.png", dpi=200)
    plt.close()
    print(f"  wrote {OUT_DIR}/ml_best_alpha_per_load.png")
    return fine_loads, best_alphas, best_predictions


def plot_abm_vs_best_static(gp, scaler, abm_df, val_df=None):
    """Bar chart: ABM vs ML-predicted-DT vs (optional) measured-DT-at-predicted-alpha."""
    abm_by_load = {row["load"]: row[TARGET_METRIC] for _, row in abm_df.iterrows()}
    best_static = []
    best_alpha = []
    for L in LOADS:
        ms = [predict(gp, scaler, L, a)[0] for a in ALPHA_GRID]
        i = int(np.argmin(ms))
        best_static.append(ms[i])
        best_alpha.append(ALPHA_GRID[i])

    abm_vals = [abm_by_load[L] for L in LOADS]

    # Match validation to predicted alphas (validation should run at exactly best_alpha[i])
    val_vals = [None] * len(LOADS)
    if val_df is not None:
        for i, L in enumerate(LOADS):
            cand = val_df[(val_df["load"] == L)]
            if not cand.empty:
                # Pick row with alpha closest to predicted optimal
                idx = (cand["alpha_bg"] - best_alpha[i]).abs().idxmin()
                val_vals[i] = float(cand.loc[idx, TARGET_METRIC])

    has_val = val_df is not None and any(v is not None for v in val_vals)

    plt.figure(figsize=(10, 6))
    x = np.arange(len(LOADS))
    width = 0.27 if has_val else 0.35
    plt.bar(x - width, best_static, width, label="DT @ ML-optimal α (GP predicted)", color="tab:blue")
    if has_val:
        plt.bar(x, val_vals, width, label="DT @ ML-optimal α (measured)", color="tab:purple")
    plt.bar(x + (width if has_val else width / 2 * 2 - width / 2), abm_vals, width,
            label="ABM (adaptive α, measured)", color="tab:orange")
    for i, L in enumerate(LOADS):
        plt.annotate(f"α*={best_alpha[i]:.3g}", (x[i] - width, best_static[i]),
                     ha="center", va="bottom", fontsize=9)
    plt.xticks(x, [f"Load = {L}" for L in LOADS])
    plt.ylabel("99p Short FCT slowdown")
    plt.title("ABM (adaptive) vs ML-found best static α — value of adaptivity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/ml_abm_vs_best_static.png", dpi=200)
    plt.close()
    print(f"  wrote {OUT_DIR}/ml_abm_vs_best_static.png")
    return list(zip(LOADS, best_alpha, best_static, abm_vals, val_vals))


def plot_observed_grid(df):
    """Observed sweep data: scatter colored by 99p slowdown — sanity check before ML."""
    plt.figure(figsize=(9, 5.5))
    sc = plt.scatter(df["alpha_bg"], df["load"], c=df[TARGET_METRIC], cmap="viridis_r", s=130, edgecolor="black")
    plt.xscale("log", base=2)
    plt.colorbar(sc, label="99p Short FCT slowdown")
    plt.xlabel("alpha_bg (log scale)")
    plt.ylabel("Load")
    plt.title("Observed alpha-sweep: 99p slowdown across (load, alpha)")
    for _, r in df.iterrows():
        plt.annotate(f"{r[TARGET_METRIC]:.1f}", (r["alpha_bg"], r["load"]),
                     textcoords="offset points", xytext=(8, 4), fontsize=8)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/ml_observed_sweep.png", dpi=200)
    plt.close()
    print(f"  wrote {OUT_DIR}/ml_observed_sweep.png")


# ----------------- Main -----------------
def main():
    print("=" * 70)
    print("ML-driven alpha optimization")
    print("=" * 70)

    print("\n[1/5] Loading data...")
    sweep = load_sweep()
    abm = load_abm_baseline()
    val = load_validation()
    print(f"  alpha-sweep: {len(sweep)} rows ({sweep['alpha_bg'].nunique()} alphas x {sweep['load'].nunique()} loads)")
    print(f"  ABM baseline: {len(abm)} rows")
    if val is not None:
        print(f"  validation: {len(val)} rows (measured DT at ML-predicted α)")
    else:
        print("  validation: NOT FOUND — re-run after parse-validation.sh > results-validation.dat")

    print("\n[2/5] Sweep observations (DT, varying alpha):")
    pivot = sweep.pivot_table(index="alpha_bg", columns="load", values=TARGET_METRIC)
    print(pivot.to_string(float_format=lambda x: f"{x:7.2f}"))

    print("\n[3/5] Fitting Gaussian Process regression...")
    gp, scaler = fit_gp(sweep)
    print(f"  fitted kernel: {gp.kernel_}")
    print(f"  log marginal likelihood: {gp.log_marginal_likelihood(gp.kernel_.theta):.3f}")

    print("\n[4/5] Generating plots...")
    plot_observed_grid(sweep)
    plot_heatmap(sweep, gp, scaler)
    plot_best_alpha_per_load(gp, scaler)
    comparison = plot_abm_vs_best_static(gp, scaler, abm, val)

    print("\n[5/5] Comparison table:")
    if val is not None:
        print(f"  {'Load':>6}  {'α*':>10}  {'GP pred':>10}  {'Measured':>10}  {'GP error':>10}  {'ABM':>8}  {'ABM gain':>10}")
        print(f"  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*8}  {'-'*10}")
        for L, alpha, static_pred, abm_val, measured in comparison:
            if measured is None:
                continue
            err = (static_pred - measured) / measured * 100
            gain = (measured - abm_val) / measured * 100
            print(f"  {L:>6.2f}  {alpha:>10.4f}  {static_pred:>10.2f}  {measured:>10.2f}  {err:>+9.1f}%  {abm_val:>8.2f}  {gain:>+9.1f}%")
    else:
        print(f"  {'Load':>6}  {'Best static α (predicted)':>26}  {'DT@best static':>16}  {'ABM (adaptive)':>16}  {'ABM gain':>10}")
        print(f"  {'-'*6}  {'-'*26}  {'-'*16}  {'-'*16}  {'-'*10}")
        for L, alpha, static_pred, abm_val, _ in comparison:
            gain = (static_pred - abm_val) / static_pred * 100
            print(f"  {L:>6.2f}  {alpha:>26.4f}  {static_pred:>16.2f}  {abm_val:>16.2f}  {gain:>+9.1f}%")

    # Write predictions only if validation hasn't run yet (don't clobber)
    if val is None:
        print(f"\n  Writing predictions to {PREDICTIONS_FILE} for run-validation.sh")
        with open(PREDICTIONS_FILE, "w") as f:
            f.write("# Format: load alpha_bg predicted_99fct abm_99fct\n")
            for L, alpha, static_pred, abm_val, _ in comparison:
                f.write(f"{L} {alpha:.6f} {static_pred:.4f} {abm_val:.4f}\n")

    print("\nDONE.")


if __name__ == "__main__":
    main()
