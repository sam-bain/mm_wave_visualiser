from mavlink_subscriber import MavlinkSubscriber
from plotter import *
import sys
import os
import time
import threading

#Specify the IP address to point to for mavlink messages
UDP_IP_ADD = '192.168.2.149'

#Specify the aircraft to be displayed in the plot
AIRCRAFT_TYPE = AircraftType.NAVI

#Specify the distance from the aircraft displayed in the plot
PLOT_SIZE = 5 #meters

#Specify the plot refresh rate
REFRESH_RATE = 10 #Hz

DEBUG = False

class RadarVisualiser:
    def __init__(self):

        #Create instances of the mavlink subscriber and plotter
        self.mavlink_subscriber = MavlinkSubscriber(UDP_IP_ADD, DEBUG)
        self.plotter1 = Plotter(ViewOrientation.TopDown, AIRCRAFT_TYPE, PLOT_SIZE, REFRESH_RATE, DEBUG, clear=True)
        # self.plotter2 = Plotter(ViewOrientation.SideOn, AIRCRAFT_TYPE, PLOT_SIZE, REFRESH_RATE, DEBUG, clear=True)

        #Start a thread to read in and update the plotting data
        self.thread = threading.Thread(target = self.spin)
        self.thread.start()

        #Show the plot. This function blocks anything else from executing on the main thread. The plot updates automatically at REFRESH_RATE
        plt.show()

    def spin(self):
        while (True):
            try:
                #If a new obstacle message is available, append it to the new plot.
                if self.mavlink_subscriber.read_msg():
                    self.plotter1.update_data(self.mavlink_subscriber.get_msg(), self.mavlink_subscriber.get_altitude())
                    # self.plotter2.update_data(self.mavlink_subscriber.get_msg(), self.mavlink_subscriber.get_altitude())
                time.sleep(0.001)
            except KeyboardInterrupt:
                print('Interrupted')
                try:
                    sys.exit(130)
                except SystemExit:
                    os._exit(130)
        

if __name__ == "__main__":
    radar_visualiser = RadarVisualiser()
