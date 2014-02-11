import numpy as np

class DynamicViewport(object):
    viewportsize = 1.0  # x-size of the viewport, in seconds
    databuffersize = 3.0  # size of the data buffer
    
    viewportindex = -1  # current viewportindex0
    databuffer = (0.0, 0.0)  # current extended viewport, as (x0, x1)
    
    def __init__(self, duration, xmin = 0.0):
        self.xmin = xmin
        self.xmax = xmin + duration
        self.max_viewportindex = int(duration/self.viewportsize)
        
    def get_viewport_index(self, x):
        """
        Determine the viewport index containing a given x value.
        """
        viewportindex = np.clip(int((x - self.xmin)/self.viewportsize), 0, self.max_viewportindex)
        return viewportindex
        
    def get_viewport(self, index):
        x0v = max(self.xmin, index * self.viewportsize)
        x1v = min(self.xmax, x0v + self.viewportsize)
        return (x0v, x1v)
        
    def get_databuffer(self, viewport):
        (x0v, x1v) = viewport
        side = (self.databuffersize - self.viewportsize) / 2
        if x0v - side <= self.xmin:
            databuffer = (self.xmin, min(self.xmin + self.databuffersize, self.xmax))
        # elif x1v + side >= self.xmax:
            # databuffer = (max(self.xmax - self.databuffersize, self.xmin), self.xmax)
        else:
            databuffer = (x0v - side, min(x1v + side, self.xmax))
        return databuffer
        
    # def update_viewport(self, index):
    def update_viewport(self, viewport):
        self.viewport = viewport
        databuffer = self.get_databuffer(self.viewport)
        # no change if new databuffer is included in old databuffer
        if (databuffer[0] >= self.databuffer[0]) & (databuffer[1] <= self.databuffer[1]):
            return False
        self.databuffer = databuffer
        return True
        