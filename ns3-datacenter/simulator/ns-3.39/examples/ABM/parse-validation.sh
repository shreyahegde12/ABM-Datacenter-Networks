source config.sh
DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"
PREDICTIONS_FILE="$DIR/plots/predicted_alphas.txt"

DT=101
TCP=1   # CUBIC

SERVERS=16
LEAVES=2
SPINES=1
LINKS=2
SERVER_LEAF_CAP=10
LEAF_SPINE_CAP=10
LATENCY=10
N_PRIO=2

BURST_SIZES=0.3
BURST_FREQ=2

cd $DIR

echo "short999fct short99fct short95fct shortavgfct shortmedfct incast999fct incast99fct incast95fct incastavgfct incastmedfct long999fct long99fct long95fct longavgfct longmedfct avgTh medTh bufmax buf999 buf99 buf95 avgBuf medBuf load burst alg tcp scenario nprio alpha_bg"

# Predictions file is "load alpha_bg predicted_99 abm_99" — alpha is %.6f (e.g. 0.591489)
grep -v "^#" $PREDICTIONS_FILE | while read LOAD ALPHA_BG _ _; do
    [ -z "$LOAD" ] && continue
    # File names use .6f formatted alpha exactly as written
    ALPHA_FMT=$(printf "%.6f" $ALPHA_BG)
    FLOWFILE="$DUMP_DIR/fcts-validation-$TCP-$DT-$ALPHA_FMT-$LOAD-$BURST_SIZES-$BURST_FREQ.fct"
    TORFILE="$DUMP_DIR/tor-validation-$TCP-$DT-$ALPHA_FMT-$LOAD-$BURST_SIZES-$BURST_FREQ.stat"
    ROW=$(python3 parseData-singleQ.py "$FLOWFILE" "$TORFILE" $LEAF_SPINE_CAP $(( $LATENCY*8 )) $LOAD $BURST_SIZES $DT $TCP validation $N_PRIO 2>/dev/null)
    if [ -n "$ROW" ]; then
        echo "$ROW $ALPHA_FMT"
    fi
done
