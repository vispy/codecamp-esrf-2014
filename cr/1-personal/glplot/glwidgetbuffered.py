import sys
import time
import numpy as np
from numpy import *
from glwidget import GLWidget
from navigationbuffered import NavigationBuffered
from navigationinterface import NavigationInterface
from signals import SIGNALS
from datadisplay import DataDisplay
from h5 import *
from colors import *
from dynamicviewport import DynamicViewport
from dataproxy import H5DataProxy, DataProxy

    
def get_options(opt, lw):
    mode = "line"
    color = LINECOLORS[0] #len(data) % len(LINECOLORS)]
    if opt is None:
        mode = "line"
    else:
        # mode?
        if opt[0] == '-':
            mode = "line"
        elif opt[0] == ',':
            mode = "points"
            
        # color?
        if (len(opt)==1):
            if opt not in "-,":
                color = get_color(opt[0])
        else:
            color = get_color(opt[1])
    return dict(lw=lw, mode=mode, color=color)


class GLWidgetBuffered(GLWidget):
    channels = 1
    duration = 1
    
    def __init__(self, parent=None):
        super(GLWidgetBuffered, self).__init__(parent)
        self.nav = NavigationBuffered()
        self.navInterface = NavigationInterface(self.nav)
        self.nav.sxmin = 1.  #/self.maxviewportsize
        
    def load_data(self, data, freq=None):
        self.data = data
        if type(data) is h5py.Dataset:
            self.channels = data.attrs["channels"]
            self.duration = data.attrs["duration"]
            self.freq = data.attrs["freq"]
            self.dataproxy = H5DataProxy(data)
        else:
            self.channels = data.shape[1]
            self.duration = (data.shape[0] - 1) / float(freq)
            self.freq = freq
            self.dataproxy = DataProxy(data, freq)
        
        self.dynamicviewport = DynamicViewport(self.duration)
        
        # max translation, used for the slider
        self.nav.xmin = self.dynamicviewport.xmin
        self.nav.xmax = self.dynamicviewport.xmax
        self.nav.txmax = self.duration - self.dynamicviewport.viewportsize
        
        # get the first view port and data buffer to load the data at first
        viewport = self.dynamicviewport.get_viewport(0)
        data = self.update_data(self.dynamicviewport.get_databuffer(viewport),\
                                viewport)
        
        # reload if already initialized
        if self.isInitialized:
            self.dataDisplay.bind_data_buffer()
            self.updateGL()
        
    def paintGL(self):
        # retrieve the transformation, from the user interface functions
        tx, ty = self.nav.get_translation()
        sx, sy = self.nav.get_scale()
        
        # get the current viewport index
        x0, y0 = self.nav.get_data_coordinates()
        viewportindex = self.dynamicviewport.get_viewport_index(x0)
        # get the viewport
        viewport = self.dynamicviewport.get_viewport(viewportindex)
        # get the data buffer x coordinates (x0, x1)
        changed = self.dynamicviewport.update_viewport(viewport)
        
        # databuffer = self.dynamicviewport.get_databuffer(viewport)
        self.nav.set_offsetx(self.dynamicviewport.databuffer[0])
        # translate the data, using the compensation of the translation with offsetx
        self.dataDisplay.transform(tx + self.nav.offsetx, ty, sx, sy)
                        
        # update the viewport and the data buffer if needed
        # if self.dynamicviewport.update_viewport(viewportindex):
        if changed: #self.dynamicviewport.update_viewport(viewport):
            print "Load (%.1fs, %.1fs)" % (self.dynamicviewport.databuffer)
            self.update_data(self.dynamicviewport.databuffer, renormalize=False)
            self.dataDisplay.bind_data_buffer()
            self.updateGL()
        
        self.dataDisplay.paint()
        
    def update_data(self, databuffer=None, renormalize=True):
        if databuffer is None:
            databuffer = self.dynamicviewport.databuffer
        data = self.dataproxy.get(databuffer, offsetx=self.nav.offsetx)
        n = data.shape[0] / self.channels
        databounds = [i * n for i in xrange(self.channels + 1)]
        # TODO: allow options
        options = [get_options(None, 1.0) for _ in xrange(self.channels)]
        self.dataDisplay.load(data, databounds, options=options, renormalize=renormalize)
        
        return data
