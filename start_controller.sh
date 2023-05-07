PATH_TO_POX=./pox

ln -f ./global_variable.py ${PATH_TO_POX}/global_variable.py
ln -f ./util.py ${PATH_TO_POX}/util.py
ln -f ./port_bingo.py ${PATH_TO_POX}/port_bingo.py
ln -f ./http_server.py ${PATH_TO_POX}/http_server.py
ln -f ./controller.py ${PATH_TO_POX}/controller.py
ln -f ./pox-main.py ${PATH_TO_POX}/pox-main.py
ln -f ./lan_info.in ${PATH_TO_POX}/lan_info.in
ln -f ./index.htm ${PATH_TO_POX}/index.htm

# kill -9 $(lsof -t -i:6633)

cd ${PATH_TO_POX}

python pox.py pox-main