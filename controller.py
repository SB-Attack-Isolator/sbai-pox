from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, EthAddr

from global_varible import set_var, get_var
from port_bingo import BingoThread, BingoMessage

log = core.getLogger()

class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)
        
        self.FIREWALL_PRIORITY = 200
        self.PACKET_PRIORITY = 100
        self.DEFAULT_PRIORITY = 1

        self.mac_to_port = {}
        self.bingo_thread = BingoThread(log)
    
    def block():
        pass

    def allow():
        pass

    def stat():
        pass

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
        log.info("Switch %s has come up.", dpid)
        self.mac_to_port[dpid] = {}
