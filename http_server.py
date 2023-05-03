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
    attacker = global_variable.get_var(ATTACKER_KEY)
    return attacker


@bottle.route('/attackers', method='POST')
def attacker_is_fixed():
    attacker_ip = bottle.request.forms.get('attacker_ip')
    attacker = global_variable.get_var(ATTACKER_KEY)
    if attacker_ip in attacker:
        del attacker[attacker_ip]
        global_variable.set_var(ATTACKER_KEY, attacker)

        # Send message to controller
        msg = FirewallMessage(attacker_ip, block=False)
        global_variable.get_var(CONTROLLER_MESSAGE_QUEUE_KEY).put(msg)

    return "OK"


def start_http_server():
    def run_server():
        bottle.run(host='0.0.0.0', port=8081)
    
    global_variable.get_var(LOGGER_KEY).info("HTTP server is running")
    threading.Thread(target=run_server).start()
