import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.image as mpimg
import numpy as np
from enum import Enum
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import threading
from matplotlib.patches import Wedge

from mavlink_subscriber import RadarIDs

FIG_DPI = 100 #Figure pixels per inch
FIG_SIZE = 10 #inches

CORRECTION_FACTOR = 20

class ViewOrientation(Enum):
    TopDown = 0
    SideOn = 1
    _3D = 2

class AircraftType(Enum):
    NAVI = 0
    SKYJIB = 1
    ICON = 2

class Image:
    def __init__(self, source, scale):
        self.source = source
        self.scale = scale #Pixels per meter

    
aircraft_images = [Image('navi_topview.png', 413),
                   Image('navi_sideview.png', 567),
                   Image('skyjib_topview.png', 200),
                   Image('skyjib_sideview.png', 200),
                   Image('icon_topview.png', 200),
                   Image('icon_sideview.png', 200)]

radar_angles = [0, 52.3, -140.8, -52.3, 140.8] #The angle of each of the radars on the drone (CCW +ve, 0 = straight ahead). Order is defined by standard X4 motor order {UNDEFINED, FR, RL, FL, RR}
radar_pos = [[     0,      0,     0],  #For undefined radar position, don't translate
            [ 0.247,  0.319, 0.075],  #The position of the front right radar on the drone {x, y, z} [m]
            [-0.372, -0.303, 0.075],  #The position of the rear left radar on the drone {x, y, z} [m]
            [ 0.247, -0.319, 0.075],  #The position of the front left radar on the drone {x, y, z} [m]
            [-0.372,  0.303, 0.075]]  #The position of the rear right radar on the drone {x, y, z} [m]

RADAR_FOV_AZIMUTH = 60 #+/-
RADAR_MIN_RANGE = 0.35
RADAR_MAX_RANGE = 25

images_directory = 'images/'

class Plotter:
    def __init__(self, view_orientation, aircraft_type, plot_size, refresh_rate, debug, clear=True):
        self.view_orientation = view_orientation
        self.aircraft_type = aircraft_type
        self.plot_size = plot_size
        self.refresh_rate = refresh_rate
        self.debug = debug
        self.clear = clear

        self.mutex = threading.RLock()
        self.missing_radars_mutex = threading.RLock()
        
        self.x_plot = []
        self.y_plot = []
        self.z_plot = []
        self.missing_radars = []

        self.altitude = 0

        #Select appropriate aircraft image for specified aircraft type and orientation
        self.aircraft_image = mpimg.imread(images_directory + aircraft_images[2*self.aircraft_type.value + self.view_orientation.value].source)

        #Create the figure, specify the size
        self.fig = plt.figure(figsize = (FIG_SIZE, FIG_SIZE), dpi=FIG_DPI)

        #Create the axis within the figure
        if self.view_orientation == ViewOrientation._3D:
            self.ax = plt.axes(projection ="3d")
        else:
            self.ax = plt.axes()

        #Create an animation so the plot can be updated in real time. Specify the update interval in ms
        self.ani = animation.FuncAnimation(self.fig, self.update_display, interval=1000/self.refresh_rate)

    def update_data(self, data):
        
        self.mutex.acquire()
        self.x_plot = data.x_plot.copy()
        self.y_plot = data.y_plot.copy()
        self.z_plot = data.z_plot.copy()
        self.mutex.release()

        self.missing_radars_mutex.acquire()
        self.missing_radars = data.missing_radars.copy()
        self.missing_radars_mutex.release()

    def update_display(self, i):
        if self.view_orientation == ViewOrientation._3D:
            self.update_3Ddisplay()
        else:
            self.update_2Ddisplay()

    def update_3Ddisplay(self):
        pass

    def update_2Ddisplay(self):
            if self.clear:
                self.ax.clear()

            self.update_aircraft_image()

            #Plot the points, determined by the view orientation
            if self.view_orientation == ViewOrientation.TopDown:
                self.mutex.acquire()
                self.ax.scatter(self.y_plot, self.x_plot, c="green")
                self.mutex.release()

                self.ax.set_xlim(left=-self.plot_size, right=self.plot_size)
                self.ax.set_ylim(bottom=-self.plot_size, top=self.plot_size)
                

                self.ax.set_xlabel('Y (m)')
                self.ax.set_ylabel('X (m)')   

                self.plot_missing_radars()

            else:
                self.mutex.acquire()
                self.ax.scatter(self.x_plot, self.z_plot, c="green")
                self.mutex.release()
        
                self.ax.set_xlim(left=-self.plot_size, right=self.plot_size)
                self.ax.set_ylim(bottom=self.plot_size, top=-self.plot_size)

                self.ax.set_xlabel('X (m)')
                self.ax.set_ylabel('Z (m)') 

                self.plot_ground()

            plt.gca().set_aspect('equal', adjustable='box')


    def plot_ground(self):
        rectangle = plt.Rectangle((-self.plot_size, self.plot_size), self.plot_size*2, -(self.plot_size-self.altitude), fc='green',ec="green", alpha=0.2)
        plt.gca().add_patch(rectangle)

    def update_aircraft_image(self):
        #Create the aircraft image at point (0,0) in the plot
        figure_scale = min(self.fig.get_size_inches())*FIG_DPI/(self.plot_size*2) *0.6 #pixels per inch
        image_scale = aircraft_images[2*self.aircraft_type.value + self.view_orientation.value].scale #pixels per inch
        zoom = figure_scale/image_scale
        imagebox = OffsetImage(self.aircraft_image, zoom=zoom)
        ab = AnnotationBbox(imagebox, (0,-0.05), frameon=False)
        self.ax.add_artist(ab)

    def plot_missing_radars(self):
        self.missing_radars_mutex.acquire()
        for radar_id in self.missing_radars:
            if radar_id != RadarIDs.UNDEFINED.value:
                wedge = Wedge((radar_pos[radar_id][1], radar_pos[radar_id][0]), RADAR_MAX_RANGE, 90 - (radar_angles[radar_id]+RADAR_FOV_AZIMUTH), 90 - (radar_angles[radar_id]-RADAR_FOV_AZIMUTH), width=RADAR_MAX_RANGE-RADAR_MIN_RANGE, alpha=0.2, color="r")
                self.ax.add_artist(wedge)
        self.missing_radars_mutex.release()
            


    def update_altitude(self, altitude):
        self.altitude = altitude

if __name__ == "__main__":
    plotter1 = Plotter(ViewOrientation.TopDown, AircraftType.NAVI, 5, 1, False, clear=True)
    # plotter2 = Plotter(ViewOrientation.SideOn, AircraftType.NAVI, 5, 10, False, clear=True)
    plotter1.x_plot = [1, 2]
    plotter1.y_plot = [1, 2]
    plotter1.missing_radars.append(RadarIDs.FRONT_RIGHT.value)
    plotter1.missing_radars.append(RadarIDs.REAR_LEFT.value)
    plotter1.missing_radars.append(RadarIDs.FRONT_LEFT.value)
    plotter1.missing_radars.append(RadarIDs.REAR_RIGHT.value)
    plt.show()