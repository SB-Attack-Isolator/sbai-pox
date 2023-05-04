from global_variable import LOGGER_KEY
import global_variable

# HOST_STATUS
ATTACKER = "attackers"
BLOCKED = "blocked"
ALLOWED = "allowed"

class FirewallMessage:
    def __init__(self, src_ip, block):
        self.src_ip = str(src_ip)
        self.block = block

def print_log(msg):
    global_variable.lock_var(LOGGER_KEY)
    global_variable.get_var(LOGGER_KEY).info(msg)
    global_variable.release_var(LOGGER_KEY)