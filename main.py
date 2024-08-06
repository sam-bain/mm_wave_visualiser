from mavlink_subscriber import MavlinkSubscriber
from plotter import *
import sys
import os
import time
import threading
import math

#Specify the aircraft to be displayed in the plot
AIRCRAFT_TYPE = AircraftType.NAVI

#Specify the distance from the aircraft displayed in the plot
PLOT_SIZE = 15 #meters

#Specify the plot refresh rate
REFRESH_RATE = 5 #Hz

DEBUG = False

class RadarVisualiser:
    def __init__(self):

        self.shutdown_event = threading.Event()

        #Create instances of the mavlink subscriber and plotter
        self.mavlink_subscriber = MavlinkSubscriber(DEBUG)
        self.plotter1 = Plotter(ViewOrientation.TopDown, AIRCRAFT_TYPE, PLOT_SIZE, REFRESH_RATE, DEBUG, clear=True)
        self.plotter2 = Plotter(ViewOrientation.SideOn, AIRCRAFT_TYPE, PLOT_SIZE, REFRESH_RATE, DEBUG, clear=True)

        #Start a thread to read in and update the plotting data
        self.mavlink_listener_thread = threading.Thread(target=self.mavlink_listener)
        self.mavlink_listener_thread.start()

        self.frame_processor_thread = threading.Thread(target=self.frame_processor)
        self.frame_processor_thread.start()

        self.altitude_updater_thread = threading.Thread(target=self.altitude_updater)
        self.altitude_updater_thread.start()

        #Show the plot. This function blocks anything else from executing on the main thread. The plot updates automatically at REFRESH_RATE
        plt.show()

        self.shutdown_event.set()

    def mavlink_listener(self):
        print("Mavlink listener thread running")
        while (not self.shutdown_event.is_set()):
            #If a new obstacle message is available, append it to the new plot.
            self.mavlink_subscriber.read_msg()
        print("Mavlink listener thread closed")

    def frame_processor(self):
        print("Frame processor thread running")
        while (not self.shutdown_event.is_set()):
            frame_data = self.mavlink_subscriber.get_frame()
            self.plotter1.update_data(frame_data)
            self.plotter2.update_data(frame_data)
        print("Frame processor thread closed")

    def altitude_updater(self):
        print("Altitude updater thread running")
        while (not self.shutdown_event.is_set()):
            self.plotter2.update_altitude(self.mavlink_subscriber.get_altitude())
            time.sleep(0.2)
        print("Altitude updater thread closed")

    def debug_thread(self):
        print("Debug thread running")
        while (not self.shutdown_event.is_set()):
            print(self.mavlink_subscriber.received_frames)
            self.mavlink_subscriber.received_frames.clear()
            time.sleep(2)
        print("Debug thread closed")


if __name__ == "__main__":
    radar_visualiser = RadarVisualiser()
