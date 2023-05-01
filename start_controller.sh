PATH_TO_POX=../../pox

cp global_varible.py ${PATH_TO_POX}/global_varible.py
cp port_bingo.py ${PATH_TO_POX}/port_bingo.py
cp controller.py ${PATH_TO_POX}/controller.py
cp pox-main.py ${PATH_TO_POX}/pox-main.py

# kill -9 $(lsof -t -i:6633)

${PATH_TO_POX}/pox.py pox-main