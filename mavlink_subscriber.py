from pymavlink import mavutil
import time
import sys
import os

class MavlinkSubscriber:
    def __init__(self, ip_add, debug=False):
        self.debug = debug
        #Create a mavlink connection to the specificied UDP port
        self.master = mavutil.mavlink_connection('udpin:' + ip_add + ':14550')
        self.recieved_message = None
        self.altitude = 0
        self.counter = 0

    def read_msg(self):
        msg_recieved = False
        msg = self.master.recv_match()

        # print("Hello")
        
        if not msg:
            pass

        else:          
            if msg.get_type() == 'OBSTACLE_DISTANCE_3D' and (msg.x == 0 or msg.y == 0) and msg.obstacle_id == 3: #ignore (0,0,0) messages as these are just heartbeats
                self.recieved_message = msg
                msg_recieved = True
                
                if self.debug:
                    #print("Obstacle message recieved")
                    self.counter += 1
            
            elif msg.get_type() == 'RANGEFINDER':
                self.altitude = msg.distance

        return msg_recieved
    
    def get_msg(self):
        return self.recieved_message
    
    def get_altitude(self):
        return self.altitude
    
if __name__ == "__main__":
    mavlink_subscriber = MavlinkSubscriber('192.168.2.149', True)
    start_time = time.time()
    while (True):
        try:
            #If a new obstacle message is available, append it to the new plot.
            mavlink_subscriber.read_msg()
            # time.sleep(0.0001)
            if (time.time() - start_time > 1):
                print(mavlink_subscriber.counter)
                mavlink_subscriber.counter = 0
                start_time = time.time()
            
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(130)
            except SystemExit:
                os._exit(130)
            
