import threading
import time
import Queue
import global_varible

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 115, 135, 139, 143, 194, 443, 445, 1433, 3306, 3389, 5632, 5900, 8080, 25565]
DEFAULT_TIMEOUT = 5 # seconds

class BingoMessage:
    def __init__(self, src_ip, dst_ip, dst_port):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.dst_port = dst_port
    
class BingoThread:
    def __init__(self, logger):
        self.log = logger
        self.message_queue = Queue.Queue()
        self.bingo_thread = threading.Thread(target=self.port_bingo_task)
        self.ip_visited_port = {}
        self.bingo_thread.start()

        self.threshold = 0.8
        global_varible.set_var("attacker", {})

    def port_bingo_task(self):
        self.log.info("Port bingo thread is running")
        while True:
            message = self.message_queue.get()
            if message == "exit":
                break
            else:
                if message.dst_port in COMMON_PORTS:
                    self.add_visited_port(message.src_ip, message.dst_ip, message.dst_port)
                    self.detect_attacker()

    def detect_attacker(self):
        attacker = global_varible.get_var("attacker")
        for src_ip, d in self.ip_visited_port.items():
            for dst_ip, ports in d.items():
                if len(ports) >= len(COMMON_PORTS) * self.threshold:
                    attacker[src_ip] = {
                        "dst_ip": dst_ip,
                        "time": time.time()
                    }
                    self.log.info("Attacker: {}".format(attacker))
        global_varible.set_var("attacker", attacker)

    def add_visited_port(self, src_ip, dst_ip, dst_port):
        if src_ip not in self.ip_visited_port:
            self.ip_visited_port[src_ip] = {}
        if dst_ip not in self.ip_visited_port[src_ip]:
            self.ip_visited_port[src_ip][dst_ip] = set()
        self.ip_visited_port[src_ip][dst_ip].add(dst_port)
    
    def send_bingo_task(self, msg):
        self.message_queue.put(msg)

    def stop_bingo_thread(self):
        self.message_queue.put("exit")
    
    