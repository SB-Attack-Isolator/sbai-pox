import bottle
import threading
from global_variable import ATTACKER_KEY, CONTROLLER_MESSAGE_QUEUE_KEY
import global_variable
from util import *
import json


@bottle.route('/')
def index():
    return bottle.static_file("index.htm","./")


@bottle.route('/attackers')
def get_attacker():
    attacker = global_variable.get_var(ATTACKER_KEY,useLock = True)
    bottle.response.content_type = "application/json"
    return json.dumps(attacker)


@bottle.route('/attackers', method='POST')
def attacker_is_fixed():
    attacker_ip = bottle.request.forms.get('attacker_ip')

    # Send message to controller
    global_variable.lock_var(CONTROLLER_MESSAGE_QUEUE_KEY)
    msg = FirewallMessage(attacker_ip, block=False)
    global_variable.get_var(CONTROLLER_MESSAGE_QUEUE_KEY).put(msg)
    global_variable.release_var(CONTROLLER_MESSAGE_QUEUE_KEY)
    
    bottle.response.content_type = "application/json"
    
    return json.dumps({"message":"OK"})


def start_http_server():
    def run_server():
        bottle.run(host='0.0.0.0', port=8081)
    
    print_log("HTTP server is running")
    threading.Thread(target=run_server).start()
