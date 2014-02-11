import numpy as np

class Navigation(object):
    """
    tx, ty      state-space total translation
    sx, sy      total scaling 
    """
    # translation
    tx, ty = 0, 0
    offsetx = 0
    
    # scaling
    sx, sy = 1, 1
    sxmin = 0  # min scaling
    
    # scaling coefficient
    cx, cy = 5.0, -5.0
    
    # initial translation
    tx0, ty0 = -.5, -.5
    
    # keep current transform values
    sxl, syl = 1, 1 # last
        
    xmin, xmax = 0.0, 1.0
    
    def translate_x(self, x):
        """
        x is relative to the last call
        """
        self.tx += x / self.sx
    
    def translate_y(self, y):
        self.ty += y / self.sy
    
    def translate(self, x, y):
        self.translate_x(x)
        self.translate_y(y)
        
    def slide(self, x, max):
        self.tx = (.5 - .5/self.sx) * (1 - 2*x/float(max))
        return self.tx != 0
        
    def get_slide(self, max):
        if self.sx == 1:
            v = 0
        else:
            v = (float(max))*(.5 - self.tx/(1 - 1./self.sx))
        v = np.clip(v, 0, float(max))
        return v
        
    def scale_x(self, x, x0=None):
        """
        x is relative to the last call
        """
        self.sx *= np.exp(self.cx * x)
        self.sx = max(self.sx, self.sxmin)
        
        # zoom on the click point: add translation
        if (x0 is not None):
            self.tx += (.5 - x0) * (1./self.sxl - 1./self.sx)
        
        self.sxl = self.sx
        
    def scale_y(self, y, y0=None):
        self.sy *= np.exp(self.cy * y)
        
        # zoom on the click point: add translation
        if (y0 is not None):
            self.ty += (.5 - y0)*(1./self.syl - 1./self.sy)
        
        self.syl = self.sy
        
    def scale(self, x, y, x0, y0):
        self.scale_x(x, x0)
        self.scale_y(y, y0)
    
    def reset(self):
        self.tx = self.ty = 0
        self.sx = self.sy = 1
    
    def get_translation(self, centered=True):
        if centered:
            return self.tx + self.tx0, self.ty + self.ty0
        else:
            return self.tx, self.ty
        
    def get_scale(self):
        return self.sx, self.sy
       
    def get_data_coordinates(self, xscreen = 0.0, yscreen = 0.0):
        x = .5 * (1. - 1./self.sx) - self.tx + xscreen / self.sx
        y = .5 * (1. - 1./self.sy) - self.ty + yscreen / self.sy
        return x, y
       