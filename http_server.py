import bottle
import threading
from global_variable import ATTACKER_KEY
import global_variable
from pox.lib.addresses import IPAddr

log = None

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
    return "OK"

def start_http_server(logger):
    def run_server():
        bottle.run(host='localhost', port=8081)
    
    log = logger
    log.info("HTTP server is running")
    threading.Thread(target=run_server).start()
