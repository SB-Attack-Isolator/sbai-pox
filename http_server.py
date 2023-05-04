import bottle
import threading
from global_variable import ATTACKER_KEY, CONTROLLER_MESSAGE_QUEUE_KEY, LOGGER_KEY
import global_variable
from util import *


@bottle.route('/')
def index():
    return "Hello, World!"


@bottle.route('/attackers')
def get_attacker():
    global_variable.lock_var(ATTACKER_KEY)
    attacker = global_variable.get_var(ATTACKER_KEY)
    global_variable.release_var(ATTACKER_KEY)
    return attacker


@bottle.route('/attackers', method='POST')
def attacker_is_fixed():
    attacker_ip = bottle.request.forms.get('attacker_ip')

    # Send message to controller
    global_variable.lock_var(CONTROLLER_MESSAGE_QUEUE_KEY)
    msg = FirewallMessage(attacker_ip, block=False)
    global_variable.get_var(CONTROLLER_MESSAGE_QUEUE_KEY).put(msg)
    global_variable.release_var(CONTROLLER_MESSAGE_QUEUE_KEY)
    
    return "OK"


def start_http_server():
    def run_server():
        bottle.run(host='0.0.0.0', port=8081)
    
    print_log("HTTP server is running")
    threading.Thread(target=run_server).start()
