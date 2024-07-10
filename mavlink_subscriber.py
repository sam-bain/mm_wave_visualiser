from pymavlink import mavutil
import time
import sys
import os
import math

class Point:
	def convert_to_cartesian(self):
                self.z = -self.distance * math.sin(math.radians(self.pitch))
                xy = self.distance * math.cos(math.radians(self.pitch))
                self.x = xy * math.cos(math.radians(self.yaw))
                self.y = xy * math.sin(math.radians(self.yaw))
            
	def __init__(self, mavlink_message):
		self.yaw, self.pitch, self.distance, self.obstacle_id = mavlink_message.yaw/1000, mavlink_message.pitch/1000, mavlink_message.distance/1000, mavlink_message.sensor_id
		self.convert_to_cartesian()
	def __str__(self):
		return "X: {}, Y: {}, Z: {}".format(self.x, self.y, self.z)

class MavlinkSubscriber:
    def __init__(self, ip_add, debug=False):
        self.debug = debug
        #Create a mavlink connection to the specificied UDP port
        self.master = mavutil.mavlink_connection('udpin:' + ip_add + ':14550')
        self.recieved_message = None
        self.altitude = 0
        self.counter = 0
        self.frame_finished = False

    def read_msg(self):
        msg_recieved = False
        msg = self.master.recv_match()

        # print("Hello")
        
        if not msg:
            pass

        else:
            if msg.get_type() == 'SHORT_RADAR_TELEM': # and (msg.x == 0 or msg.y == 0): #ignore (0,0,0) messages as these are just heartbeats
                msg_recieved = True

                if msg.yaw == 0 and msg.pitch == 0 and msg.distance == 0:
                    self.frame_finished = True
                    self.counter += 1
                else:
                    self.recieved_message = Point(msg)
                    
                if self.debug:
                    pass
                    # print(msg)
                    # if self.frame_finished:
                    #     print("--------New frame-----------")
                    #     self.frame_finished = False

            
            elif msg.get_type() == 'RANGEFINDER':
                self.altitude = msg.distance

        return msg_recieved
    
    def get_msg(self):
        return self.recieved_message
    
    def get_altitude(self):
        return self.altitude
    
    def get_frame_state(self):
         return self.frame_finished
    
    def reset_frame_state(self):
         self.frame_finished = False
    
if __name__ == "__main__":
    mavlink_subscriber = MavlinkSubscriber('192.168.2.149', True)
    start_time = time.time()
    frames_per_second_list = []
    while (True):
        try:
            #If a new obstacle message is available, append it to the new plot.
            mavlink_subscriber.read_msg()
            # time.sleep(0.0001)
            if (time.time() - start_time > 1):
                
                frames_per_second_list.append(mavlink_subscriber.counter)
                print(mavlink_subscriber.counter, sum(frames_per_second_list)/len(frames_per_second_list))
                mavlink_subscriber.counter = 0
                start_time = time.time()
            
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(130)
            except SystemExit:
                os._exit(130)
            
