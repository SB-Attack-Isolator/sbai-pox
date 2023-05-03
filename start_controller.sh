PATH_TO_POX=../../pox

cp global_variable.py ${PATH_TO_POX}/global_variable.py
cp util.py ${PATH_TO_POX}/util.py
cp port_bingo.py ${PATH_TO_POX}/port_bingo.py
cp http_server.py ${PATH_TO_POX}/http_server.py
cp controller.py ${PATH_TO_POX}/controller.py
cp pox-main.py ${PATH_TO_POX}/pox-main.py

# kill -9 $(lsof -t -i:6633)

${PATH_TO_POX}/pox.py pox-main