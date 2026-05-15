docker build -t abm .
docker run -it abm

cd simulator/ns-3.39

./waf configure
./waf build

bash run-main-bufalg-load.sh