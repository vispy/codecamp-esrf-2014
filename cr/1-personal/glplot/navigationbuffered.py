import numpy as np
from navigation import Navigation

class NavigationBuffered(Navigation):
    txmax = 1  # max translation
        
    def set_offsetx(self, x):
        self.offsetx = x
    
    def slide(self, x, max):
        txnew = .5 * (1. - 1. / self.sx) - self.xmin - float(x) / max * (self.xmax - self.xmin - 1. / self.sx)
        
        if self.tx != txnew:
            self.tx = txnew
            return True
        return False
        
    def get_slide(self, max):
        v = int(max * (.5 * (1. - 1. / self.sx) - self.xmin - self.tx) / (self.xmax - self.xmin - 1. / self.sx))
        return v

    def reset(self):
        self.ty = 0.
        self.sx = self.sy = 1.
        self.slide(0., 1.)