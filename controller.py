from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, EthAddr

from global_variable import ATTACKER_KEY, CONTROLLER_MESSAGE_QUEUE_KEY, LOGGER_KEY
import global_variable
from port_bingo import BingoThread, BingoMessage
from http_server import start_http_server
import Queue
import threading
import time
from util import *

log = core.getLogger()



class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)

        self.FIREWALL_PRIORITY = 200
        self.PACKET_PRIORITY = 100
        self.DEFAULT_PRIORITY = 65535

        self.dpid_to_event = {}
        self.mac_to_port = {}

        global_variable.lock_var(LOGGER_KEY)
        global_variable.set_var(LOGGER_KEY, log)
        global_variable.release_var(LOGGER_KEY)

        # Used to communicate between threads and controller
        global_variable.lock_var(CONTROLLER_MESSAGE_QUEUE_KEY)
        global_variable.set_var(CONTROLLER_MESSAGE_QUEUE_KEY, Queue.Queue())
        global_variable.release_var(CONTROLLER_MESSAGE_QUEUE_KEY)

        # Port bingo thread
        self.bingo_thread = BingoThread()
        self.bingo_thread.start_thread()

        # Http server thread
        start_http_server()

        # Firewall thread
        threading.Thread(target=self.modify_firewall_task).start()

        # Load LAN info
        self.lans = []
        
        f = open("lan_info.in", "r")
        dat = f.read().split()
        net_count = int(dat[0])
        for netstr in dat[1:]:
            addr,mask = netstr.split('/')
            self.lans.append((IPAddr(addr),int(mask)))
        f.close()

    def _in_network(self, ipaddr):
        for network in self.lans:
            if ipaddr.inNetwork(network):
                return True
        return False

    # You can write other functions as you need.
    def _handle_PacketIn(self, event):
        in_port = event.port
        packet = event.parsed
        ofp_msg = event.ofp
        dpid = dpid_to_str(event.dpid)

        if not packet.parsed:
            return

    	# forward packet to out_port
        def forward_packet(event, packet, outport):
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, in_port)
            msg.actions.append(of.ofp_action_output(port = outport))
            msg.data = ofp_msg
            event.connection.send(msg)

    	# Check the packet and decide how to route the packet
        def forward(message = None):
            if self.mac_to_port[dpid].get(packet.src) is None:
                self.mac_to_port[dpid][packet.src] = in_port
            
            if packet.dst.is_multicast:
                flood("Flood: Multicast packet")
            else:
                if self.mac_to_port[dpid].get(packet.dst) is None:
                    flood("Flood: Unknown dst")
                else:
                    # log.info("Packet from [MAC: {}], current switch DPID: {} to [MAC: {}]".format(packet.src, dpid, packet.dst))
                    
                    src_ip = None
                    dst_ip = None
                    ip_packet = packet.find('ipv4') or packet.find('ipv6')
                    if ip_packet is not None:
                        transport_packet = ip_packet.find('tcp') or ip_packet.find('udp')
                        if transport_packet is not None:
                            src_ip = ip_packet.srcip
                            dst_ip = ip_packet.dstip
                            dst_port = transport_packet.dstport
                            # log.info('IP: Packet from {} to {}:{}'.format(src_ip, dst_ip, dst_port))
                            msg = BingoMessage(src_ip=src_ip, dst_ip=dst_ip, dst_port=dst_port)
                            self.bingo_thread.send_bingo_task(msg)

                    out_port = self.mac_to_port[dpid][packet.dst]
                    forward_packet(event, packet, out_port)

        # When it knows nothing about the destination, flood but don't install the rule
        def flood (message = None):
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            msg.data = ofp_msg
            msg.in_port = in_port
            event.connection.send(msg)

        forward()


    def _handle_ConnectionUp(self, event):
        dpid = dpid_to_str(event.dpid)
        print_log("Switch {} has come up.".format(dpid))
        self.mac_to_port[dpid] = {}
        self.dpid_to_event[dpid] = event


    def modify_firewall_task(self):
        while True:
            global_variable.lock_var(CONTROLLER_MESSAGE_QUEUE_KEY)
            q = global_variable.get_var(CONTROLLER_MESSAGE_QUEUE_KEY)
            global_variable.release_var(CONTROLLER_MESSAGE_QUEUE_KEY)
            if q.empty():
                time.sleep(1)
                continue
            message = q.get()
            if message == "exit":
                break
            else:
                if message.block:
                    self.block(message.src_ip)
                else:
                    self.allow(message.src_ip)


    def block(self, src_ip):
        src_ip_object = IPAddr(src_ip)
        local_attack = self._in_network(src_ip_object)
        
        global_variable.lock_var(ATTACKER_KEY)
        attacker = global_variable.get_var(ATTACKER_KEY)
        print_log("Block IP: {}".format(src_ip))
        if src_ip in attacker:
            attacker[src_ip]['status'] = BLOCKED
            global_variable.set_var(ATTACKER_KEY, attacker)
            # modify firewall policy to block traffic
            if local_attack:
                for _, event in self.dpid_to_event.items():
                    for net in self.lans:
                        msg = of.ofp_flow_mod()
                        msg.match.dl_type = 0x0800
                        msg.match.nw_proto = 6
                        msg.priority = self.FIREWALL_PRIORITY
                        msg.match.nw_src = src_ip_object
                        msg.match.nw_dst = net
                        event.connection.send(msg)
            else:
                for _, event in self.dpid_to_event.items():
                    msg = of.ofp_flow_mod()
                    msg.match.dl_type = 0x0800
                    msg.match.nw_proto = 6
                    msg.priority = self.FIREWALL_PRIORITY
                    msg.match.nw_src = src_ip_object
                    event.connection.send(msg)

        print_log("Attacker: {}".format(attacker))
        global_variable.release_var(ATTACKER_KEY)


    def allow(self, src_ip):
        src_ip_object = IPAddr(src_ip)
        local_attack = False
        if self._in_network(src_ip_object):
            local_attack = True

        global_variable.lock_var(ATTACKER_KEY)
        attacker = global_variable.get_var(ATTACKER_KEY)
        print_log("Allow IP: {}".format(src_ip))
        if src_ip in attacker:
            attacker[src_ip]['status'] = ALLOWED
            # del attacker[attacker_ip]
            global_variable.set_var(ATTACKER_KEY, attacker)

            # modify firewall policy to allow traffic
            if local_attack:
                for _, event in self.dpid_to_event.items():
                    for net in self.lans:
                        msg = of.ofp_flow_mod()
                        msg.command = of.OFPFC_DELETE_STRICT
                        msg.match.dl_type = 0x0800
                        msg.match.nw_proto = 6
                        msg.priority = self.FIREWALL_PRIORITY
                        msg.match.nw_src = src_ip_object
                        msg.match.nw_dst = net
                        # msg.actions = [of.ofp_action_output(port = of.OFPP_NORMAL)]
                        event.connection.send(msg)
            else:
                for _, event in self.dpid_to_event.items():
                    msg = of.ofp_flow_mod()
                    msg.command = of.OFPFC_DELETE_STRICT
                    msg.match.dl_type = 0x0800
                    msg.match.nw_proto = 6
                    msg.priority = self.FIREWALL_PRIORITY
                    msg.match.nw_src = src_ip_object
                    # msg.actions = [of.ofp_action_output(port = of.OFPP_NORMAL)]
                    event.connection.send(msg)

        print_log("Attacker: {}".format(attacker))
        global_variable.release_var(ATTACKER_KEY)

