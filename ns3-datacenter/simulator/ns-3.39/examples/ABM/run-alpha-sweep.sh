source config.sh
DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"
LOG_DIR="$DIR/logs"
ALPHASWEEP_DIR="$DIR/alphasweep"
mkdir -p $DUMP_DIR
mkdir -p $LOG_DIR
mkdir -p $ALPHASWEEP_DIR

DT=101
TCP=1   # CUBIC

SERVERS=16
LEAVES=2
SPINES=1
LINKS=2
SERVER_LEAF_CAP=10
LEAF_SPINE_CAP=10
LATENCY=10

RED_MIN=65
RED_MAX=65
N_PRIO=2

CDFFILE="$DIR/websearch.txt"
ALPHA_UPDATE_INT=1

STATIC_BUFFER=0
BUFFER_PER_PORT_PER_GBPS=9.6
BUFFER=$(python3 -c "print(int($BUFFER_PER_PORT_PER_GBPS*1024*($SERVERS+$LINKS*$SPINES)*$SERVER_LEAF_CAP))")

START_TIME=0
END_TIME=3
FLOW_END_TIME=1.5

BURST_SIZES=0.3
BURST_SIZE=$(python3 -c "print($BURST_SIZES*$BUFFER)")
BURST_FREQ=2

# Alpha sweep — vary background priority (alpha[1]); keep incast (alpha[0]) at 1.0
ALPHAS=(0.0625 0.125 0.25 0.5 1.0)
ALPHA_INCAST=1

cd $NS3

N=0
RUN_START=$(date +%s)
echo "[$(date +%H:%M:%S)] Alpha sweep: 5 alphas x 3 loads = 15 DT sims, N_CORES=$N_CORES"
echo "[$(date +%H:%M:%S)] DUMP_DIR=$DUMP_DIR  ALPHASWEEP_DIR=$ALPHASWEEP_DIR"

for ALPHA_BG in ${ALPHAS[@]}; do
    # Custom alphas file: alpha[0]=1.0 (incast, fixed), alpha[1]=$ALPHA_BG (varied)
    ALPHASFILE="$ALPHASWEEP_DIR/alphas-$ALPHA_BG"
    cat > $ALPHASFILE <<EOF
$ALPHA_INCAST
$ALPHA_BG
0.5
0.5
0.125
0.0625
0.03125
0.015625
EOF

    for LOAD in 0.4 0.6 0.8; do
        FLOWFILE="$DUMP_DIR/fcts-alphasweep-$TCP-$DT-$ALPHA_BG-$LOAD-$BURST_SIZES-$BURST_FREQ.fct"
        TORFILE="$DUMP_DIR/tor-alphasweep-$TCP-$DT-$ALPHA_BG-$LOAD-$BURST_SIZES-$BURST_FREQ.stat"
        SIMLOG="$LOG_DIR/sim-alphasweep-$TCP-$DT-$ALPHA_BG-$LOAD.log"

        if [ -s "$FLOWFILE" ] && [ -s "$TORFILE" ]; then
            echo "[$(date +%H:%M:%S)] SKIP (already exists): ALPHA_BG=$ALPHA_BG LOAD=$LOAD"
            continue
        fi

        # Throttle on actual binary path (fixed from previous run)
        while [[ $(ps aux | grep "build/examples/ABM/ns3.39-abm-evaluation" | grep -v grep | wc -l) -ge $N_CORES ]]; do
            sleep 15
        done

        N=$((N+1))
        echo "[$(date +%H:%M:%S)] launch #$N: ALPHA_BG=$ALPHA_BG LOAD=$LOAD -> $SIMLOG"
        ( time ./waf --run "abm-evaluation --load=$LOAD --StartTime=$START_TIME --EndTime=$END_TIME --FlowLaunchEndTime=$FLOW_END_TIME --serverCount=$SERVERS --spineCount=$SPINES --leafCount=$LEAVES --linkCount=$LINKS --spineLeafCapacity=$LEAF_SPINE_CAP --leafServerCapacity=$SERVER_LEAF_CAP --linkLatency=$LATENCY --TcpProt=$TCP --BufferSize=$BUFFER --statBuf=$STATIC_BUFFER --algorithm=$DT --RedMinTh=$RED_MIN --RedMaxTh=$RED_MAX --request=$BURST_SIZE --queryRequestRate=$BURST_FREQ --nPrior=$N_PRIO --alphasFile=$ALPHASFILE --cdfFileName=$CDFFILE --alphaUpdateInterval=$ALPHA_UPDATE_INT --fctOutFile=$FLOWFILE --torOutFile=$TORFILE" ) > "$SIMLOG" 2>&1 &
        sleep 2
    done
done

wait

RUN_END=$(date +%s)
ELAPSED=$((RUN_END - RUN_START))
echo "[$(date +%H:%M:%S)] DONE. Launched $N new sims in ${ELAPSED}s ($((ELAPSED/60))m $((ELAPSED%60))s)."
echo "Per-sim wall times in $LOG_DIR/sim-alphasweep-*.log"
