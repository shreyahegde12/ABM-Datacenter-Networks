source config.sh
DIR="$NS3/examples/ABM"
DUMP_DIR="$DIR/dump_sigcomm"

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

ALPHAS=(0.0625 0.125 0.25 0.5 1.0)

cd $DIR

# Header — same 29 columns as results-all.dat for compatibility, then add 'alpha_bg' as 30th
echo "short999fct short99fct short95fct shortavgfct shortmedfct incast999fct incast99fct incast95fct incastavgfct incastmedfct long999fct long99fct long95fct longavgfct longmedfct avgTh medTh bufmax buf999 buf99 buf95 avgBuf medBuf load burst alg tcp scenario nprio alpha_bg"

for ALPHA_BG in ${ALPHAS[@]}; do
    for LOAD in 0.4 0.6 0.8; do
        FLOWFILE="$DUMP_DIR/fcts-alphasweep-$TCP-$DT-$ALPHA_BG-$LOAD-$BURST_SIZES-$BURST_FREQ.fct"
        TORFILE="$DUMP_DIR/tor-alphasweep-$TCP-$DT-$ALPHA_BG-$LOAD-$BURST_SIZES-$BURST_FREQ.stat"
        # parseData prints 29 fields then we append alpha_bg
        ROW=$(python3 parseData-singleQ.py "$FLOWFILE" "$TORFILE" $LEAF_SPINE_CAP $(( $LATENCY*8 )) $LOAD $BURST_SIZES $DT $TCP alphasweep $N_PRIO 2>/dev/null)
        if [ -n "$ROW" ]; then
            echo "$ROW $ALPHA_BG"
        fi
    done
done
