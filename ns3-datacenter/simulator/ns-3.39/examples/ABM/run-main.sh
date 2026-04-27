source config.sh
DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"
LOG_DIR="$DIR/logs"
mkdir -p $DUMP_DIR
mkdir -p $LOG_DIR

DT=101
FAB=102
CS=103
IB=104
ABM=110

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

ALPHAFILE="$DIR/alphas"
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
echo "[$(date +%H:%M:%S)] Plan A: 5 algs (DT,FAB,CS,IB,ABM) x 3 loads (0.4,0.6,0.8), N_CORES=$N_CORES"
echo "[$(date +%H:%M:%S)] DUMP_DIR=$DUMP_DIR  LOG_DIR=$LOG_DIR"

for ALG in $DT $FAB $CS $IB $ABM; do
    for LOAD in 0.4 0.6 0.8; do
        FLOWFILE="$DUMP_DIR/fcts-single-$TCP-$ALG-$LOAD-$BURST_SIZES-$BURST_FREQ.fct"
        TORFILE="$DUMP_DIR/tor-single-$TCP-$ALG-$LOAD-$BURST_SIZES-$BURST_FREQ.stat"
        SIMLOG="$LOG_DIR/sim-$TCP-$ALG-$LOAD.log"

        if [ -s "$FLOWFILE" ] && [ -s "$TORFILE" ]; then
            echo "[$(date +%H:%M:%S)] SKIP (already exists): ALG=$ALG LOAD=$LOAD"
            continue
        fi

        while [[ $(ps aux | grep abm-evaluation-optimized | grep -v grep | wc -l) -ge $N_CORES ]]; do
            sleep 15
        done

        N=$((N+1))
        echo "[$(date +%H:%M:%S)] launch #$N: ALG=$ALG LOAD=$LOAD  -> log: $SIMLOG"
        ( time ./waf --run "abm-evaluation --load=$LOAD --StartTime=$START_TIME --EndTime=$END_TIME --FlowLaunchEndTime=$FLOW_END_TIME --serverCount=$SERVERS --spineCount=$SPINES --leafCount=$LEAVES --linkCount=$LINKS --spineLeafCapacity=$LEAF_SPINE_CAP --leafServerCapacity=$SERVER_LEAF_CAP --linkLatency=$LATENCY --TcpProt=$TCP --BufferSize=$BUFFER --statBuf=$STATIC_BUFFER --algorithm=$ALG --RedMinTh=$RED_MIN --RedMaxTh=$RED_MAX --request=$BURST_SIZE --queryRequestRate=$BURST_FREQ --nPrior=$N_PRIO --alphasFile=$ALPHAFILE --cdfFileName=$CDFFILE --alphaUpdateInterval=$ALPHA_UPDATE_INT --fctOutFile=$FLOWFILE --torOutFile=$TORFILE" ) > "$SIMLOG" 2>&1 &
        sleep 2
    done
done

wait

RUN_END=$(date +%s)
ELAPSED=$((RUN_END - RUN_START))
echo "[$(date +%H:%M:%S)] DONE. Launched $N new sims in ${ELAPSED}s ($((ELAPSED/60))m $((ELAPSED%60))s)."
echo "Per-sim wall times are in $LOG_DIR/sim-*.log (look for 'real' line)."
