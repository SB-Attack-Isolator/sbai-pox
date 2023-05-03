# HOST_STATUS
ATTACKER = "attackers"
BLOCKED = "blocked"
ALLOWED = "allowed"


class FirewallMessage:
    def __init__(self, src_ip, block):
        self.src_ip = str(src_ip)
        self.block = block