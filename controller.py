from pox.core import core

import pox.openflow.libopenflow_01 as of

from pox.lib.revent import *
from pox.lib.util import dpid_to_str
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()

class Controller(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        core.openflow_discovery.addListeners(self)
        
        filename = 'policy.in'
        f = open(filename, 'r')
        self.num_policy, self.num_premium, self.policies, self.premium_hosts = self.parse_policy_file(f)

        self.FIREWALL_PRIORITY = 200
        self.PREMIUM_HOST_PRIORITY = 100
        self.DEFAULT_PRIORITY = 1

        self.mac_to_port = {}
    
    def block():
        pass

    def allow():
        pass

    def stat():
        pass

    # You can write other functions as you need.
    def parse_policy_file(self, f):
        contents = f.read().split()
        num_policy, num_premium, info = int(contents[0]), int(contents[1]), contents[2:]
        policies = []
        for i in range(num_policy):
            policy = info[i].split(',')
            if len(policy) == 2:
                policies.append([None, policy[0], policy[1]])
            else:
                policies.append([policy[0], policy[1], policy[2]])
        premium_hosts = set()
        for i in range(num_policy, num_premium + num_policy):
            premium_hosts.add(info[i])
        
        log.info('Policies: {}, {}'.format(num_policy, policies))
        log.info('Premium hosts: {}, {}'.format(num_premium, premium_hosts))

        return num_policy, num_premium, policies, premium_hosts

    def _handle_PacketIn(self, event):
        in_port = event.port
        packet = event.parsed
        ofp_msg = event.ofp
        dpid = dpid_to_str(event.dpid)

        # log.info("Packet from [MAC: {}, DPID: {}] to [MAC: {}]".format(packet.src, dpid, packet.dst))

    	# install entries to the route table
        def install_enqueue(event, packet, outport, q_id):
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, in_port)
            msg.actions.append(of.ofp_action_enqueue(port = outport, queue_id = q_id))
            msg.data = ofp_msg
            
            if q_id == 1:
                msg.priority = self.PREMIUM_HOST_PRIORITY
            log.info('Install enqueue: {}, {}, {}, {}, {}'.format(dpid, packet.src, packet.dst, q_id, msg.priority))

            event.connection.send(msg)

        def isPremiumPacket(ip):
            return ip is not None and str(ip) in self.premium_hosts

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
                    log.info("Packet from [MAC: {}], current switch DPID: {} to [MAC: {}]".format(packet.src, dpid, packet.dst))
                    
                    src_ip = None
                    dst_ip = None
                    if packet.type == packet.IP_TYPE:
                        src_ip = packet.payload.srcip
                        dst_ip = packet.payload.dstip
                        log.info('IP: Packet from {} to {}'.format(src_ip, dst_ip))
                    elif packet.type == packet.ARP_TYPE:
                        src_ip = packet.payload.protosrc
                        dst_ip = packet.payload.protodst
                        log.info('ARP: Packet from {} to {}'.format(src_ip, dst_ip))

                    if src_ip is None and dst_ip is None:
                        q_id = 0
                    elif isPremiumPacket(src_ip):
                        log.info("Premium packet")
                        q_id = 1
                    else:
                        log.info("Normal packet")
                        q_id = 2

                    out_port = self.mac_to_port[dpid][packet.dst]
                    install_enqueue(event, packet, out_port, q_id)

        # When it knows nothing about the destination, flood but don't install the rule
        def flood (message = None):
            # log.info(message)
            # define your message here
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            msg.data = ofp_msg
            msg.in_port = in_port
            
            event.connection.send(msg)

        forward()


    def _handle_ConnectionUp(self, event):
        dpid = dpid_to_str(event.dpid)
        log.debug("Switch %s has come up.", dpid)

        self.mac_to_port[dpid] = {}
        # Send the firewall policies to the switch
        def sendFirewallPolicy(connection, policy):
            # define your message here
            msg = of.ofp_flow_mod()
            msg.match.dl_type = 0x0800
            msg.match.nw_proto = 6
            msg.priority = self.FIREWALL_PRIORITY
            if policy[0] is not None:
                msg.match.nw_src = IPAddr(policy[0])
            msg.match.nw_dst = IPAddr(policy[1])
            msg.match.tp_dst = int(policy[2])
            
            log.info('Switch {}, Firewall policy: src = {}, dst = {}, port = {}'.format(event.dpid, policy[0], policy[1], policy[2]))

            connection.send(msg)

        for policy in self.policies:
            sendFirewallPolicy(event.connection, policy)
            
