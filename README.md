# sbai-pox
Concept Validation of Software Based Attack Isolator
* Mininet version: Python3
* Pox version: fangtooth (Python2)

* Step1: clone this repo recursively: ```git clone --recurse-submodules https://github.com/SB-Attack-Isolator/sbai-pox.git```

* Step2: start the SBAI system
    * Terminal1: start controller (in python2 env): ```bash start_controller.sh```
        * may need to install bottle: ```pip install bottle```
    * Terminal2: start network: ```bash start_network.sh```