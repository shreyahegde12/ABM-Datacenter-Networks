import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

def load_data(filepath):
    # Read the data, ensuring whitespace is treated as the delimiter
    try:
        df = pd.read_csv(filepath, sep=r'\s+')
        return df
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def main():
    filepath = "results-all.dat"
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return
    
    df = load_data(filepath)
    if df is None or df.empty:
        print("Warning: The dataset is empty. Please ensure your simulations have completed and results.sh parsed the data successfully.")
        return
        
    print(f"Loaded {len(df)} rows from {filepath}")
    
    # Map numeric IDs to names based on results.sh
    tcp_map = {0: 'RENO', 1: 'CUBIC', 2: 'DCTCP', 3: 'HPCC', 4: 'POWERTCP', 5: 'HOMA', 6: 'TIMELY', 7: 'THETAPOWERTCP'}
    alg_map = {101: 'DT', 102: 'FAB', 103: 'CS', 104: 'IB', 110: 'ABM'}
    
    df['tcp_name'] = df['tcp'].map(tcp_map).fillna(df['tcp']).astype(str)
    df['alg_name'] = df['alg'].map(alg_map).fillna(df['alg']).astype(str)

    # Create plots directory if it doesn't exist
    os.makedirs("generated_plots", exist_ok=True)
    
    sns.set_theme(style="whitegrid")

    # Plot 1: Average Short FCT vs Load
    if 'load' in df.columns and 'shortavgfct' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.lineplot(data=df, x='load', y='shortavgfct', hue='alg_name', style='tcp_name', markers=True)
        plt.title('Average Short Flow Completion Time vs Load')
        plt.xlabel('Load')
        plt.ylabel('Average FCT')
        plt.savefig('generated_plots/short_fct_vs_load.png', dpi=300)
        plt.close()
        print("Generated short_fct_vs_load.png")

    # Plot 2: 99th Percentile Short FCT vs Load
    if 'load' in df.columns and 'short99fct' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.lineplot(data=df, x='load', y='short99fct', hue='alg_name', style='tcp_name', markers=True)
        plt.title('99th Percentile Short Flow Completion Time vs Load')
        plt.xlabel('Load')
        plt.ylabel('99p FCT')
        plt.savefig('generated_plots/short99_fct_vs_load.png', dpi=300)
        plt.close()
        print("Generated short99_fct_vs_load.png")

    # Plot 3: Average Throughput vs Load
    if 'load' in df.columns and 'avgTh' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.lineplot(data=df, x='load', y='avgTh', hue='alg_name', style='tcp_name', markers=True)
        plt.title('Average Tor Uplink Throughput vs Load')
        plt.xlabel('Load')
        plt.ylabel('Average Throughput')
        plt.savefig('generated_plots/throughput_vs_load.png', dpi=300)
        plt.close()
        print("Generated throughput_vs_load.png")
        
    # Plot 4: Average Buffer Occupancy vs Load
    if 'load' in df.columns and 'avgBuf' in df.columns:
        plt.figure(figsize=(8, 6))
        sns.lineplot(data=df, x='load', y='avgBuf', hue='alg_name', style='tcp_name', markers=True)
        plt.title('Average Buffer Occupancy vs Load')
        plt.xlabel('Load')
        plt.ylabel('Buffer Occupancy %')
        plt.savefig('generated_plots/buffer_vs_load.png', dpi=300)
        plt.close()
        print("Generated buffer_vs_load.png")

    print("All available plots have been generated in the 'generated_plots' folder.")

if __name__ == "__main__":
    main()
