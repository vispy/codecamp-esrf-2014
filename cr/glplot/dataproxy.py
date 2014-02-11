import numpy as np
from h5 import read_hdf5

class DataProxy(object):
    def __init__(self, data, freq):
        self.fulldata = data
        self.data = None  # current data
        self.arr = None  # contains the y as a N*channels array
        self.freq = freq
        self.channels = data.shape[1]
        self.duration = (data.shape[0] - 1) / float(freq)
        
    def get_indices(self, databuffer):
        x0, x1 = databuffer
        i0 = int(np.round(x0 * self.freq))
        i1 = int(np.round(x1 * self.freq))
        return i0, i1
        
    def get_x(self, databuffer, offsetx=None):
        if offsetx is None:
            offsetx = 0.0
        x0, x1 = databuffer
        i0, i1 = self.get_indices(databuffer)
        n = i1 - i0 + 1
        x = np.linspace(x0 - offsetx, x1 - offsetx, n)
        return x
        
    def get_y(self, databuffer):
        """
        Return an array N x channels
        """
        x0, x1 = databuffer
        i0, i1 = self.get_indices(databuffer)
        arr = self.fulldata[i0:i1 + 1,:]
        return arr
        
    def get(self, databuffer, offsetx=None):
        """
        Return the data corresponding to the interval databuffer = (x0, x1),
        this interval should contain the current 1s viewport, plus the
        previous and next viewports.
        """
        # determine x
        x = self.get_x(databuffer, offsetx=offsetx)
        
        # determine y
        arr = self.get_y(databuffer)
        self.arr = arr
        
        # concatenate x and y and generate self.data
        x = x.reshape((-1,1))
        x = np.tile(x, (self.channels, 1))
        
        y = arr.flatten('F')
        y = y.reshape((-1,1))
        
        self.data = np.array(np.hstack((np.array(x), np.array(y))), np.float32)
        return self.data

        
class H5DataProxy(DataProxy):
    def __init__(self, h5data):
        self.h5data = h5data
        self.data = None
        self.freq = h5data.attrs["freq"]
        self.channels = h5data.attrs["channels"]
        self.duration = h5data.attrs["duration"]
        
    def get_y(self, databuffer):
        x0, x1 = databuffer
        arr = read_hdf5(self.h5data, x0, x1 - x0)
        return arr
        