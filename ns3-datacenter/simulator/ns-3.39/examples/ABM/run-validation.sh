source config.sh
DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"
LOG_DIR="$DIR/logs"
ALPHASWEEP_DIR="$DIR/alphasweep"
PREDICTIONS_FILE="$DIR/plots/predicted_alphas.txt"
mkdir -p $DUMP_DIR
mkdir -p $LOG_DIR
mkdir -p $ALPHASWEEP_DIR

if [ ! -f "$PREDICTIONS_FILE" ]; then
    echo "ERROR: $PREDICTIONS_FILE not found. Run ml_alpha.py first."
    exit 1
fi

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

cd $NS3

N=0
RUN_START=$(date +%s)
echo "[$(date +%H:%M:%S)] Validation: running DT at ML-predicted optimal alpha for each load"

# Skip header line and iterate predictions
grep -v "^#" $PREDICTIONS_FILE | while read LOAD ALPHA_BG _ _; do
    [ -z "$LOAD" ] && continue

    # Generate alphas file for this validation run (alpha[1] = predicted optimum)
    ALPHASFILE="$ALPHASWEEP_DIR/alphas-validation-$ALPHA_BG"
    cat > $ALPHASFILE <<EOF
1
$ALPHA_BG
0.5
0.5
0.125
0.0625
0.03125
0.015625
EOF

    FLOWFILE="$DUMP_DIR/fcts-validation-$TCP-$DT-$ALPHA_BG-$LOAD-$BURST_SIZES-$BURST_FREQ.fct"
    TORFILE="$DUMP_DIR/tor-validation-$TCP-$DT-$ALPHA_BG-$LOAD-$BURST_SIZES-$BURST_FREQ.stat"
    SIMLOG="$LOG_DIR/sim-validation-$TCP-$DT-$ALPHA_BG-$LOAD.log"

    if [ -s "$FLOWFILE" ] && [ -s "$TORFILE" ]; then
        echo "[$(date +%H:%M:%S)] SKIP (already exists): LOAD=$LOAD ALPHA_BG=$ALPHA_BG"
        continue
    fi

    while [[ $(ps aux | grep "build/examples/ABM/ns3.39-abm-evaluation" | grep -v grep | wc -l) -ge $N_CORES ]]; do
        sleep 15
    done

    N=$((N+1))
    echo "[$(date +%H:%M:%S)] launch #$N: LOAD=$LOAD ALPHA_BG=$ALPHA_BG -> $SIMLOG"
    ( time ./waf --run "abm-evaluation --load=$LOAD --StartTime=$START_TIME --EndTime=$END_TIME --FlowLaunchEndTime=$FLOW_END_TIME --serverCount=$SERVERS --spineCount=$SPINES --leafCount=$LEAVES --linkCount=$LINKS --spineLeafCapacity=$LEAF_SPINE_CAP --leafServerCapacity=$SERVER_LEAF_CAP --linkLatency=$LATENCY --TcpProt=$TCP --BufferSize=$BUFFER --statBuf=$STATIC_BUFFER --algorithm=$DT --RedMinTh=$RED_MIN --RedMaxTh=$RED_MAX --request=$BURST_SIZE --queryRequestRate=$BURST_FREQ --nPrior=$N_PRIO --alphasFile=$ALPHASFILE --cdfFileName=$CDFFILE --alphaUpdateInterval=$ALPHA_UPDATE_INT --fctOutFile=$FLOWFILE --torOutFile=$TORFILE" ) > "$SIMLOG" 2>&1 &
    sleep 2
done

wait

RUN_END=$(date +%s)
ELAPSED=$((RUN_END - RUN_START))
echo "[$(date +%H:%M:%S)] DONE. Validation in ${ELAPSED}s ($((ELAPSED/60))m $((ELAPSED%60))s)."
