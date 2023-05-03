import threading
import time
import Queue
from global_variable import ATTACKER_KEY, CONTROLLER_MESSAGE_QUEUE_KEY, LOGGER_KEY
import global_variable
from util import *

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 115, 135, 139, 143, 194, 443, 445, 1433, 3306, 3389, 5632, 5900, 8080, 25565]
DEFAULT_TIMEOUT = 5 # seconds
DETECTOR_INTERVAL = 1 # seconds


class BingoMessage:
    def __init__(self, src_ip, dst_ip, dst_port):
        self.src_ip = str(src_ip)
        self.dst_ip = str(dst_ip)
        self.dst_port = int(dst_port)


class BingoThread:
    def __init__(self):
        self.message_queue = Queue.Queue()
        self.bingo_thread = threading.Thread(target=self.port_bingo_task)
        self.tracked_connections = {}

        self.threshold = 0.8
        global_variable.set_var(ATTACKER_KEY, {})
    

    def start_thread(self):
        self.bingo_thread.start()
        threading.Timer(DETECTOR_INTERVAL, self.run_detector).start()


    def port_bingo_task(self):
        global_variable.get_var(LOGGER_KEY).info("Port bingo thread is running")
        while True:
            message = self.message_queue.get()
            if message == "exit":
                break
            else:
                if message.dst_port in COMMON_PORTS:
                    self.add_visited_port(message.src_ip, message.dst_ip, message.dst_port)
    

    def run_detector(self):
        attacker = global_variable.get_var(ATTACKER_KEY)
        cur_time = time.time()
        for src_ip, d in self.tracked_connections.items():
            for dst_ip, conn_info in d.items():
                last_updated_time = conn_info["time"]
                if cur_time - last_updated_time > DEFAULT_TIMEOUT:
                    # Reset connection info after timeout
                    self.tracked_connections[src_ip][dst_ip]["time"] = cur_time
                    self.tracked_connections[src_ip][dst_ip]["ports"] = set()
                    continue

                ports = conn_info["ports"]
                if len(ports) >= len(COMMON_PORTS) * self.threshold:
                    if src_ip in attacker and attacker[src_ip]["status"] == BLOCKED:
                        attacker[src_ip]["time"] = time.time()
                        continue
                    
                    attacker[src_ip] = {
                        "dst_ip": dst_ip,
                        "time": time.time(),
                        "status": ATTACKER
                    }
                    global_variable.get_var(LOGGER_KEY).info("Attacker: {}".format(attacker))

                    # Send message to controller
                    msg = FirewallMessage(src_ip, block=True)
                    global_variable.get_var(CONTROLLER_MESSAGE_QUEUE_KEY).put(msg)

        global_variable.set_var(ATTACKER_KEY, attacker)
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
    
    