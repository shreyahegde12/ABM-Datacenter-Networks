import sys
import numpy as np
import pandas as pd


flow_file = str(sys.argv[1])
tor_file = str(sys.argv[2])
linerate = int(sys.argv[3])          # Gbps
rtt = float(sys.argv[4])             # microseconds
load = float(sys.argv[5])
burst = float(sys.argv[6])
alg = str(sys.argv[7])
tcp = str(sys.argv[8])
scenario = str(sys.argv[9])
nprio = int(sys.argv[10])
flow_start = float(sys.argv[11])
flow_end = float(sys.argv[12])

bdp = linerate * 1e9 * rtt * 1e-6 / 8


def summarize(values):
    values = sorted(values)
    if len(values) == 0:
        return [0, 0, 0, 0, 0]
    return [
        values[max(0, int(len(values) * 0.999) - 1)],
        values[max(0, int(len(values) * 0.99) - 1)],
        values[max(0, int(len(values) * 0.95) - 1)],
        float(np.mean(values)),
        float(np.median(values)),
    ]


# FCT file columns:
# time flowsize fct basefct slowdown basertt flowstart priority incast
flow_df = pd.read_csv(flow_file, delim_whitespace=True)

short_flows = flow_df[(flow_df["flowsize"] < bdp) & (flow_df["incast"] == 0)]["slowdown"].tolist()
incast_flows = flow_df[(flow_df["incast"] == 1)]["slowdown"].tolist()
long_flows = flow_df[(flow_df["flowsize"] >= 30000000)]["slowdown"].tolist()

short999, short99, short95, shortavg, shortmed = summarize(short_flows)
incast999, incast99, incast95, incastavg, incastmed = summarize(incast_flows)
long999, long99, long95, longavg, longmed = summarize(long_flows)

# ToR stat columns:
# time tor bufferSizeMB occupiedBufferPct uplinkThroughput priority0..priority7
tor_df = pd.read_csv(
    tor_file,
    delim_whitespace=True,
    usecols=[0, 1, 2, 3, 4],
    names=["time", "tor", "bufferSizeMB", "occupiedBufferPct", "uplinkThroughput"],
    header=0,
)

# Use active flow window for your reduced experiments
tor_df = tor_df[(tor_df["time"] > flow_start) & (tor_df["time"] < flow_end)]

throughput = sorted(tor_df["uplinkThroughput"].tolist())
buffer = sorted(tor_df["occupiedBufferPct"].tolist())

if len(throughput) == 0:
    avg_th = med_th = 0
else:
    avg_th = float(np.mean(throughput))
    med_th = float(np.median(throughput))

if len(buffer) == 0:
    bufmax = buf999 = buf99 = buf95 = avg_buf = med_buf = 0
else:
    bufmax = buffer[-1]
    buf999 = buffer[max(0, int(len(buffer) * 0.999) - 1)]
    buf99 = buffer[max(0, int(len(buffer) * 0.99) - 1)]
    buf95 = buffer[max(0, int(len(buffer) * 0.95) - 1)]
    avg_buf = float(np.mean(buffer))
    med_buf = float(np.median(buffer))

print(
    short999, short99, short95, shortavg, shortmed,
    incast999, incast99, incast95, incastavg, incastmed,
    long999, long99, long95, longavg, longmed,
    avg_th, med_th, bufmax, buf999, buf99, buf95, avg_buf, med_buf,
    load, burst, alg, tcp, scenario, nprio
)