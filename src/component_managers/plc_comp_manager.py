import canopen
import time

class PLCComponentManager:

    def __init__(self):
        self.dishmode=None
        self.network0=canopen.Network()

    def connect_to_network (self):
        (self.network0).connect(channel='can0', bustype='socketcan')

    def connect_to_plc_node(self):
        node2 = canopen.RemoteNode(2, '/home/abednigo/repos/asst-cam-software/src/component_managers/cpp-slave.eds')
        (self.network0).add_node(node2)
        return node2

    
    def set_plc_node_to_operational(self,node):
        node.nmt.state='OPERATIONAL'

    def set_plc_node_to_preoperational(self,node):
        node.nmt.state='PRE-OPERATIONAL'

    def get_plc_state(self,node):
        return node.nmt.state


    def point_to_coordinates(self,node,timestamp,az,el):
        node.sdo[0x2000][1].raw=timestamp + 20
        node.sdo[0x2000][2].raw=az
        node.sdo[0x2000][3].raw=el

    def az_el_change_callback(self,incoming_object):
        for node_record in incoming_object: 
            if node_record.name=='Position Feedback.Azimuth(R64) of position':
                print(f"current Azumuth : {node_record.raw} ")
            if node_record.name=='Position Feedback.Elevation(R64) of position':
                print(f"current Elevation : {node_record.raw}")

    def subscribe_to_az_change(self,node):
        node.tpdo.read()
        # Mapping the Azimuth to tpdo
        node.tpdo[1].clear()
        #node.tpdo[1].add_variable(0x2001,2)
        node.tpdo[1].add_variable('Position Feedback','Azimuth(R64) of position')
        node.tpdo[1].trans_type = 255
        node.tpdo[1].event_timer = 300
        node.tpdo[1].enabled = True

        node.nmt.state = 'PRE-OPERATIONAL'
        print(node.nmt.state)
        node.tpdo.save()

        node.tpdo[1].add_callback(self.az_el_change_callback)

    def subscribe_to_el_change(self,node):
        node.tpdo[2].read()
        # Mapping the Elevation to tpdo
        node.tpdo[2].clear()
        node.tpdo[2].add_variable(0x2001,3)
        node.tpdo[2].trans_type = 1
        node.tpdo[2].event_timer = 0
        node.tpdo[2].enabled = True
        
        node.nmt.state = 'PRE-OPERATIONAL'
        print(node.nmt.state)
        node.tpdo.save()

        node.tpdo[2].add_callback(self.az_el_change_callback)

    def trigger_transmission(self,node):
        # Triggers the transmission of Tpdo. The PDO is transmitted when the state of the node goes to OPERATIONAL
        node.nmt.state = 'OPERATIONAL'
        (self.network0).sync.start(0.5)
        while True:
            time.sleep(1)

if __name__ == '__main__':

    cm=PLCComponentManager()
    cm.connect_to_network()
    node2=cm.connect_to_plc_node()
    cm.subscribe_to_az_change(node2)
    cm.subscribe_to_el_change(node2)
    cm.point_to_coordinates(node2,int(time.time()),50.0,60.0)
    cm.trigger_transmission(node2)