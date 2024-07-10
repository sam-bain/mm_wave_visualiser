import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.image as mpimg
import numpy as np
from enum import Enum
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import threading

FIG_DPI = 100 #Figure pixels per inch
FIG_SIZE = 10 #inches

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

images_directory = 'images/'

class Plotter:
    def __init__(self, view_orientation, aircraft_type, plot_size, refresh_rate, frames_per_plot, debug, clear=True):
        self.view_orientation = view_orientation
        self.aircraft_type = aircraft_type
        self.plot_size = plot_size
        self.refresh_rate = refresh_rate
        self.debug = debug
        self.clear = clear
        self.frames_per_plot = frames_per_plot

        self.mutex = threading.RLock()

        self.frames_since_plot = 0

        self.x_buffer = np.array([])
        self.y_buffer = np.array([])
        self.z_buffer = np.array([])
        
        self.x_plot = np.array([])
        self.y_plot = np.array([])
        self.z_plot = np.array([])

        self.altitude = 0.28

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

    def show_plot(self):
        plt.show()

    def update_data(self, msg, altitude, frame_ready):
        if frame_ready:
            self.frames_since_plot += 1
        else:
            self.x_buffer = np.append(self.x_buffer, msg.x)
            self.y_buffer = np.append(self.y_buffer, msg.y)
            self.z_buffer = np.append(self.z_buffer, msg.z)

        if self.frames_since_plot >= self.frames_per_plot:
            self.mutex.acquire()
            self.x_plot = self.x_buffer
            self.y_plot = self.y_buffer
            self.z_plot = self.z_buffer
            self.mutex.release()

            self.x_buffer = np.array([])
            self.y_buffer = np.array([])
            self.z_buffer = np.array([])
            self.frames_since_plot = 0

        self.altitude = altitude

    def update_display(self, i):
        if self.view_orientation == ViewOrientation._3D:
            self.update_3Ddisplay()
        else:
            self.update_2Ddisplay()

    def update_3Ddisplay(self):
        pass

    def update_2Ddisplay(self):
            #Clear the plot
            self.ax.clear()

            self.update_aircraft_image()

            self.mutex.acquire()
            x_plot = self.x_plot
            y_plot = self.y_plot
            z_plot = self.z_plot
            self.mutex.release()

            
            #Plot the points, determined by the view orientation
            if self.view_orientation == ViewOrientation.TopDown:
                self.mutex.acquire()
                self.ax.scatter(y_plot, x_plot, c="green")
                self.mutex.release()

                self.ax.set_xlim(left=-self.plot_size, right=self.plot_size)
                self.ax.set_ylim(bottom=-self.plot_size, top=self.plot_size)
                

                self.ax.set_xlabel('Y (m)')
                self.ax.set_ylabel('X (m)')   

            else:
                self.mutex.acquire()
                self.ax.scatter(x_plot, z_plot, c="green")
                self.mutex.release()


        
                self.ax.set_xlim(left=-self.plot_size, right=self.plot_size)
                self.ax.set_ylim(bottom=self.plot_size, top=-self.plot_size)

                self.ax.set_xlabel('X (m)')
                self.ax.set_ylabel('Z (m)') 

                self.plot_ground()

            plt.gca().set_aspect('equal', adjustable='box')


    def plot_ground(self):
        # self.ax.plot([-self.plot_size, self.plot_size], [self.altitude, self.altitude])
        rectangle = plt.Rectangle((-self.plot_size, self.plot_size), self.plot_size*2, -(self.plot_size-self.altitude), fc='green',ec="green", alpha=0.2)
        plt.gca().add_patch(rectangle)

    def update_aircraft_image(self):
        #Create the aircraft image at point (0,0) in the plot
        figure_scale = min(self.fig.get_size_inches())*FIG_DPI/(self.plot_size*2) *0.6 #pixels per inch
        image_scale = aircraft_images[2*self.aircraft_type.value + self.view_orientation.value].scale #pixels per inch
        zoom = figure_scale/image_scale
        imagebox = OffsetImage(self.aircraft_image, zoom=zoom)
        ab = AnnotationBbox(imagebox, (0,0), frameon=False)
        self.ax.add_artist(ab)

if __name__ == "__main__":
    plotter1 = Plotter(ViewOrientation.TopDown, AircraftType.NAVI, 5, 10, False, clear=True)
    plotter2 = Plotter(ViewOrientation.SideOn, AircraftType.NAVI, 5, 10, False, clear=True)
    plt.show()