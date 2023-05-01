import threading
import time
import Queue
from global_varible import ATTACKER_KEY
import global_varible

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 115, 135, 139, 143, 194, 443, 445, 1433, 3306, 3389, 5632, 5900, 8080, 25565]
DEFAULT_TIMEOUT = 5 # seconds
DETECTOR_INTERVAL = 1 # seconds


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
        self.tracked_connections = {}
        self.bingo_thread.start()

        self.threshold = 0.8
        global_varible.set_var(ATTACKER_KEY, {})
        threading.Timer(DETECTOR_INTERVAL, self.run_detector).start()


    def port_bingo_task(self):
        self.log.info("Port bingo thread is running")
        while True:
            message = self.message_queue.get()
            if message == "exit":
                break
            else:
                if message.dst_port in COMMON_PORTS:
                    self.add_visited_port(message.src_ip, message.dst_ip, message.dst_port)
    

    def run_detector(self):
        attacker = global_varible.get_var(ATTACKER_KEY)
        for src_ip, d in self.tracked_connections.items():
            for dst_ip, conn_info in d.items():
                last_updated_time = conn_info["time"]
                ports = conn_info["ports"]
                if len(ports) >= len(COMMON_PORTS) * self.threshold:
                    attacker[src_ip] = {
                        "dst_ip": dst_ip,
                        "time": time.time()
                    }
                    self.log.info("Attacker: {}".format(attacker))
        global_varible.set_var(ATTACKER_KEY, attacker)
        threading.Timer(DETECTOR_INTERVAL, self.run_detector).start()


    def add_visited_port(self, src_ip, dst_ip, dst_port):
        if src_ip not in self.tracked_connections:
            self.tracked_connections[src_ip] = {}
        if dst_ip not in self.tracked_connections[src_ip]:
            self.tracked_connections[src_ip][dst_ip] = {
                "time": time.time(),
                "ports": set()
            }
        self.tracked_connections[src_ip][dst_ip]["time"] = time.time()
        self.tracked_connections[src_ip][dst_ip]["ports"].add(dst_port)
    

    def send_bingo_task(self, msg):
        self.message_queue.put(msg)


    def stop_bingo_thread(self):
        self.message_queue.put("exit")
    
    