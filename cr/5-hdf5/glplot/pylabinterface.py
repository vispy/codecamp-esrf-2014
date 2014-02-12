import numpy as np
import sys
from PyQt4 import QtCore, QtGui
from glwidget import GLWidget
from glplotwin import GLPlot
from colors import LINECOLORS, get_color
from signals import SIGNALS

def in_ipython():
    try:
        __IPYTHON__
    except NameError:
        return False
    else:
        return True

# are we in IPython?
IPYTHON = in_ipython()

def get_databounds(data):
    # bounds for the different plots
    databounds = [0]
    databounds += [len(d) for d in data]
    databounds = np.cumsum(databounds)
    return databounds
    
def get_options(opt, lw):
    mode = "line"
    color = None # LINECOLORS[0] #len(data) % len(LINECOLORS)]
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

    
class Line(object):
    def __init__(self, x, y=None, opt=None, lw=1.0):
        if type(y) is str:
            opt = y
            y = None
        if y is None:
            y = x.copy()
            x = np.arange(0, len(y))

        x = x.reshape((-1,1))
        y = y.reshape((-1,1))
        data = np.array(np.hstack((np.array(x), np.array(y))), np.float32)
                
        self.options = get_options(opt, lw)
        self.data = data
        
    def set_color(self, color):
        self.options["color"] = color


class Window(object):
    def __init__(self, interactive=False, windowIndex=0):
        """
        Interactive=True means that "plot" displays the figure immediately
        Interactive=False means that "plot" load the data, but show will display all figures at once
        """
        self.reset()
        self.interactive = interactive
        self.windowIndex = windowIndex
        
    def reset(self):
        self.lines = []
        self.glplot = None
        
    def plot(self, *args, **kwargs):
        line = Line(*args, **kwargs)
        if line.options["color"] is None:
            line.set_color(LINECOLORS[len(self.lines) % len(LINECOLORS)])
        self.lines.append(line)
        
    def show(self):
        data = [l.data for l in self.lines]
        fulldata = np.vstack(data)
        options = [l.options for l in self.lines]
        databounds = get_databounds(data)
    
        if not(self.interactive):
            app = QtGui.QApplication(sys.argv)
           
        if self.glplot is None:
            self.glplot = GLPlot(self.interactive, self.windowIndex)
            
        self.glplot.glWidget.load_data(fulldata, databounds, options)
        self.glplot.show()
        
        if not(self.interactive):
            sys.exit(app.exec_())
        
    def close(self):
        self.glplot.hide()
        self.reset()
    

WINDOWS = []
    
def figure(interactive=IPYTHON):
    global WINDOWS
    w = Window(interactive, len(WINDOWS))
    # print "figure", w, interactive
    WINDOWS.append(w)
    
def get_last_window():
    global WINDOWS
    if len(WINDOWS)>0:
        return WINDOWS[-1]
    else:
        return None
    
def close_window(i):
    if (i>=0) and (i<len(WINDOWS)):
        WINDOWS[i].close()
        del WINDOWS[i]

def close_last_window():
    global WINDOWS
    i = len(WINDOWS)-1
    if i>0:
        close_window(i)
        return True
    else:
        return False
        
def clear(windowIndex=None):
    """
    Full reset: clear all windows
    """
    # print "clear", windowIndex
    if windowIndex is None:
        while close_last_window():
            pass
    else:
        close_window(windowIndex)
        
def plot(x, y=None, opt=None, lw=1.0):
    global WINDOWS
    if len(WINDOWS)==0:
        figure()
    w = get_last_window()
    # print "plot", w
    w.plot(x, y, opt, lw)
    
    # if w.interactive:
        # w.show()
        
def iplot(*args, **kwargs):
    plot(*args, **kwargs)
    show()
        
def show():
    global WINDOWS
    for w in WINDOWS:
        w.show()

# clear all windows when upon window exit
SIGNALS.windowCloseSignal.connect(clear)


