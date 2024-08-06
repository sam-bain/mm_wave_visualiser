from pymavlink import mavutil
import time
import sys
import os
import math
from collections import deque
import threading
import socket
from enum import Enum

class SensorStatus(Enum):
    FRAME_NOT_PROCESSED = 0
    FRAME_PROCESSING = 1
    FRAME_PROCESSED = 2

class RadarIDs(Enum):
    UNDEFINED = 0
    FRONT_RIGHT = 1
    REAR_LEFT = 2
    FRONT_LEFT = 3
    REAR_RIGHT = 4
    LENGTH = 5

class PlotData:
    def __init__(self):
        self.x_plot = []
        self.y_plot = []
        self.z_plot = []
        self.missing_radars = []

class Point:
    def convert_to_cartesian(self):
                self.z = -self.distance * math.sin(math.radians(self.pitch))
                xy = self.distance * math.cos(math.radians(self.pitch))
                self.x = xy * math.cos(math.radians(self.yaw))
                self.y = xy * math.sin(math.radians(self.yaw))
            
    def __init__(self, mavlink_message):
        self.yaw, self.pitch, self.distance, self.sensor_id = mavlink_message.yaw/10, mavlink_message.pitch/10, mavlink_message.distance/100, mavlink_message.sensor_id
        self.convert_to_cartesian()
    def __str__(self):
        return "ID: {}, Yaw: {}".format(self.sensor_id, self.yaw) #, self.pitch, self.distance)

class MavlinkSubscriber:
    def __init__(self, debug=False):
        self.debug = debug
        #Create a mavlink connection to the specificied UDP port
        self.master = mavutil.mavlink_connection('udpin:'+ socket.gethostbyname(socket.gethostname()) + ':14550')
        self.altitude = 2.5
        self.counter = 0
        self.frame_finished = False

        self.max_yaw = 0
        self.min_yaw = 0

        self.mutex = threading.RLock()

        self.radar_statuses = [SensorStatus.FRAME_NOT_PROCESSED]*RadarIDs.LENGTH.value
        self.received_obstacle_buffer = deque()
        self.received_altitude_buffer = deque()


    def read_msg(self):
        msg = self.master.recv_match(blocking=True) #Hopefully this thread sleeps while it is being blocked waiting for more messages!
        
        if not msg:
            return
        
        elif msg.get_type() == "SHORT_RADAR_TELEM":
            self.received_obstacle_buffer.append(msg)

        elif msg.get_type() == "RANGEFINDER":
            self.received_altitude_buffer.append(msg)
        
    def get_frame(self):
        data = PlotData()
        frame_complete = False
        while (not frame_complete):  
            if not self.received_obstacle_buffer: #Wait until messages are in buffer before processing
                time.sleep(0.05)
                continue

            msg = self.received_obstacle_buffer.popleft()

            if msg.distance == 0: #A message to indicated the start of a frame
                if (self.radar_statuses[msg.sensor_id] == SensorStatus.FRAME_NOT_PROCESSED):
                    self.radar_statuses[msg.sensor_id] = SensorStatus.FRAME_PROCESSING
                
                elif (self.radar_statuses[msg.sensor_id] == SensorStatus.FRAME_PROCESSING): #two subsequent frame have been received from a single radar, so all radars should have sent their frame
                    frame_complete = True

                    for radar_id in range(len(self.radar_statuses)): 
                        if self.radar_statuses[radar_id] == SensorStatus.FRAME_NOT_PROCESSED:
                            data.missing_radars.append(radar_id)
                        self.radar_statuses[radar_id] = SensorStatus.FRAME_NOT_PROCESSED #Reset frame state for all radars
                    self.radar_statuses[msg.sensor_id] = SensorStatus.FRAME_PROCESSING #already popped the start message for this radar
                
            elif (self.radar_statuses[msg.sensor_id] == SensorStatus.FRAME_PROCESSING):
                point = Point(msg)
                data.x_plot.append(point.x)
                data.y_plot.append(point.y)
                data.z_plot.append(point.z)
        
        return data

    def get_altitude(self):
        distance = None
        while (distance == None):
            if (len(self.received_altitude_buffer) > 0):
                distance = self.received_altitude_buffer.pop().distance
                self.received_altitude_buffer.clear()
            else:
                time.sleep(0.2)
        return distance

    
    
    
if __name__ == "__main__":
    mavlink_subscriber = MavlinkSubscriber(True)
    start_time = time.time()
    while (True):
        try:
            mavlink_subscriber.get_altitude()
            time.sleep(0.2)
            
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(130)
            except SystemExit:
                os._exit(130)
            
