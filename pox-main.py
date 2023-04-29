from controller import Controller

from pox.core import core
import pox.openflow as of

def launch():
    # Run discovery and spanning tree modules
    of.discovery.launch()
    of.spanning_forest.launch()

    # Starting the controller module
    core.registerNew(Controller)
