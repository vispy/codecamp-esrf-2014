ABOUT = \
"""
High performance Qt/OpenGL-based 2D plotting visualization tool
===============================================================
This Qt widget based on OpenGL provides a fast interactive visualization 
tool for simple 1D functions (y=f(x)). Its aim is to provide a much more 
efficient tool than Matplotlib, which is designed to make nice 
figures, but not to visualize large amounts of data. Matplotlib relies
on the CPU to display data, yielding poor performance when displaying
millions of points. Indeed, the CPU is not designed for efficient 
visualization, but the GPU is.

This tool relies on the widely used and highly efficient OpenGL 
library, which can benefit from GPU acceleration to display 3D but also 2D 
graphics. The UI is written in PyQT. The data to be visualized is transferred
from system memory to the GPU at initialization (under the assumption that
it won't change during the interactive visualization session). Then, 
interactive navigation is done on the GPU, achieving very high performance 
(millions on points can be displayed smoothly).

For now, the interactive commands are:
  * left mouse button for xy-translation
  * right mouse button for xy-scaling
  * CTRL + mouse left button for x-translation
  * CTRL + mouse right button/right for x-scaling
  * SHIFT + mouse left button for y-translation
  * SHIFT + mouse right button for y-scaling
  * mouse wheel for x-translation
  * ALT + wheel for y-translation
  * CTRL + wheel for x-scaling
  * SHIFT + wheel for y-scaling
  * R: reset the view
  * Home key or G: beginning of the trace
  * End key or H: end of the trace
  * F: toggle fullscreen/normal
  * S: save image
  * A: about
  * Q: exit
  
Dependencies
============
Python 2.7, Numpy, PyQT 4, PyOpenGL
"""
import sys
import time
import numpy as np
from numpy import *
from numpy.random import *
from PyQt4 import QtCore, QtGui, QtOpenGL
try:
    from OpenGL import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from PyQt4.QtOpenGL import *
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(None, "OpenGL",
            "PyOpenGL must be installed to run this example.")
    sys.exit(1)

__all__ = ['figure', 'plot', 'iplot', 'show']
    
def get_color(char):
    if char=='r':
        return (1,0,0)
    elif char=='g':
        return (0,1,0)
    elif char=='b':
        return (0,0,1)
    elif char=='y':
        return (1,1,0)
    elif char=='c':
        return (0,1,1)
    elif char=='m':
        return (1,0,1)
    elif char=='w':
        return (1,1,1)
        
LINECOLORS = [get_color(c) for c in "yrgcmwb"]

    
    
class GLWidget(QtOpenGL.QGLWidget):
    buffer = None
    pressedL = pressedR = False
    ctrlPressed = shiftPressed = altPressed = False
    wheel = 0
    bgcolor = (0, 0, 0) # RGB 0-255
    
    # initial translation
    tx0, ty0, tz0 = -.5, -.5, -10.
    
    # translation
    tx, ty = 0, 0
    txl, tyl = 0, 0 # last
    
    # scaling
    sx, sy = 1, 1
    sxl, syl = 1, 1 # last
    
    # normalized coordinates of the mouse click
    u0, v0 = 0, 0
    
    # normalized coordinates of the mouse
    u, v = 0, 0
    du, dv = 0, 0
    
    # scaling coefficient
    cx, cy = 5.0, -5.0
    
    # initial window size
    w, h = 640, 480
    
    # fpsLast = 0.
    
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.parent = parent
        self.setMouseTracking(True)

    def minimumSizeHint(self):
        return QtCore.QSize(50, 50)

    def sizeHint(self):
        return QtCore.QSize(self.w, self.h)
    
    # get position coordinates
    def coord(self, pos):
        return (pos.x(), pos.y())
    
    # get normalized coordinates
    def norm(self, pair):
        return (pair[0]/float(self.w), pair[1]/float(self.h))
    
    def ncoord(self, pos):
        return self.norm(self.coord(pos))
    
    def scale(self, lx = 1, ly = 1):
        glScalef(lx, ly, 1.)
    
    def translate(self, tx = 0, ty = 0):
        glTranslatef(tx, ty, 0)
    
    def transform(self):
        # initial position
        glLoadIdentity()
        glTranslatef(0,0, self.tz0)
        
        # mouse displacement since clicked
        self.du = self.u-self.u0
        self.dv = self.v-self.v0
        
        # determine translation
        if self.pressedL:
            if not(self.shiftPressed):
                self.tx = self.du/self.sxl + self.txl
            if not(self.ctrlPressed):
                self.ty = self.dv/self.syl + self.tyl
            self.slide_inv()
        
        # determine scaling
        if self.pressedR:    
            if not(self.shiftPressed):
                self.sx = self.sxl * (1 + exp(self.cx*(self.du))-1)
                # zoom on the click point: add translation
                self.tx = (.5-self.u0)*(1./self.sxl-1./self.sx) + self.txl
            if not(self.ctrlPressed):
                self.sy = self.syl * (1 + exp(self.cy*(self.dv))-1)
                # zoom on the click point: add translation
                self.ty = (.5-self.v0)*(1./self.syl-1./self.sy) + self.tyl
            self.slide_inv()
        
        # handle wheel zoom
        if self.wheel:
            if self.ctrlPressed:
                self.sx = self.sxl * (1 + exp(self.cx*(self.wheel))-1)
                self.sxl = self.sx
            elif self.shiftPressed:
                self.sy = self.syl * (1 + exp(-self.cy*(self.wheel))-1)
                self.syl = self.sy
            elif self.altPressed:
                self.ty = self.wheel/self.syl + self.tyl
                self.tyl = self.ty
            else:
                self.tx = self.wheel/self.sxl + self.txl
                self.txl = self.tx
            self.wheel = 0
            self.slide_inv()
        
        self.scale(self.sx, self.sy)
        self.translate(self.tx + self.tx0, self.ty + self.ty0)
    
    # print mouse position
    def print_mouse_pos(self):
        x = .5 * (1. - 1./self.sx) - self.tx + self.u/self.sx
        y = .5 * (1. - 1./self.sy) - self.ty + self.v/self.sy
        # inverse data normalization
        x = self.xmin + x * (self.xmax - self.xmin)
        y = self.ymin + y * (self.ymax - self.ymin)
        y = -y
        self.parent.statusbar.showMessage("%g, %g" % (x,y))
        
    # navigation slider
    def slide(self, v):
        self.tx = self.txl = (.5 - .5/self.sx) * (1 - 2*v/float(self.parent.navSlider.maximum()))
        if self.tx != 0:
            self.updateGL()
    
    # bind the x-translation value to the slider value
    def slide_inv(self):
        if self.sx == 1:
            v = 0
        else:
            v = (float(self.parent.navSlider.maximum()))*(.5 - self.tx/(1 - 1./self.sx))
        v = clip(v, 0, float(self.parent.navSlider.maximum()))
        self.parent.navSlider.setValue(v)
        
    def load_data(self, data, databounds=None, options=None):
        self.data = data
        if databounds==None:
            databounds = [0, len(data)]
        if options is None:
            options = [None] * (len(databounds)-1)
        self.options = options
        self.databounds = databounds
        x = self.data[:,0]
        # -data because the coordinate systems of the screen and the data
        # are y-reversed
        y = -self.data[:,1]
        # renormalization x,y \in [0,1]
        self.xmin, self.xmax = min(x), max(x)
        self.ymin, self.ymax = min(y), max(y)
        if self.xmin == self.xmax:
            self.xmin = self.xmin - .5
            self.xmax = self.xmax + .5
        if self.ymin == self.ymax:
            self.ymin = self.ymin - .5
            self.ymax = self.ymax + .5
        self.data[:,0] = (x-self.xmin)/(self.xmax-self.xmin)
        self.data[:,1] = (y-self.ymin)/(self.ymax-self.ymin)
        
    def reset(self):
        self.tx = self.ty = 0
        self.txl = self.tyl = 0
        self.sx = self.sy = 1
        self.sxl = self.syl = 1
        self.u0 = self.v0 = 0
        self.u = self.v = 0
        self.du = self.dv = 0
        self.slide_inv()
        self.updateGL()
        
    def capture(self):
        glReadBuffer(GL_FRONT )
        image = self.grabFrameBuffer()
        return image
        
    def initializeGL(self):
        self.qglClearColor(QtGui.QColor.fromRgb(*self.bgcolor))
        glEnableClientState(GL_VERTEX_ARRAY)
        self.buffer = glGenBuffers(1)
        # glBindBuffer(GL_ARRAY_BUFFER_ARB, self.buffer)
        # glBufferData(GL_ARRAY_BUFFER_ARB, self.data, GL_STATIC_DRAW_ARB)    
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        glBufferData(GL_ARRAY_BUFFER, self.data, GL_STATIC_DRAW)
        
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glVertexPointer(2, GL_FLOAT, 0, None)
        
        # antialiasing
        # glEnable(GL_BLEND)
        # glEnable(GL_LINE_SMOOTH)
        # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        # handle mouse interaction
        self.transform()
        
        if self.buffer is not None:
            glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
            for i in xrange(len(self.databounds)-1):
                opt = self.options[i]
                mode = opt["mode"] # "line" or "points"
                lw = opt["lw"] # size of line or points in pixels
                color = opt["color"] # should be a tuple 0-1
                if mode == "line":
                    glLineWidth(lw)
                    glmode = GL_LINE_STRIP
                elif mode == "points":
                    glPointSize(lw)
                    glmode = GL_POINTS
                glColor(*color)
                glDrawArrays(glmode, self.databounds[i],
                                     self.databounds[i+1]-self.databounds[i])
            glFlush()
    
    # handle window resizing
    def resizeGL(self, width, height):
        self.w, self.h = width, height
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
        glMatrixMode(GL_MODELVIEW)
        
    def focusInEvent(self):
        pass
        
    def focusOutEvent(self):
        self.pressedL = self.pressedR = False
        self.ctrlPressed = self.shiftPressed = self.altPressed = False
        
    def mousePressEvent(self, event):
        if event.button() == 1:
            self.pressedL = True
        elif event.button() == 2:
            self.pressedR = True
        # click normalized coordinates
        self.u0, self.v0 = self.ncoord(event.pos())
            
    def mouseReleaseEvent(self, event):
        if event.button() == 1:
            self.pressedL = False
        elif event.button() == 2:
            self.pressedR = False
        
        # keep current transform values
        self.txl, self.tyl = self.tx, self.ty
        self.sxl, self.syl = self.sx, self.sy

    def mouseMoveEvent(self, event):
        self.u, self.v = self.ncoord(event)
        self.print_mouse_pos()
        if self.pressedL or self.pressedR:
            self.updateGL()

    def wheelEvent(self, event):
        self.wheel = event.delta() * .001
        self.updateGL()
 
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Control:
            self.ctrlPressed = True        
        if e.key() == QtCore.Qt.Key_Shift:
            self.shiftPressed = True
        if e.key() == QtCore.Qt.Key_Alt:
            self.altPressed = True
        if e.key() == QtCore.Qt.Key_Left:
            self.wheel = .1
            self.updateGL()
        if e.key() == QtCore.Qt.Key_Right:
            self.wheel = -.1
            self.updateGL()
        
        
    def keyReleaseEvent(self, e):
        if e.key() == QtCore.Qt.Key_Control:
            self.ctrlPressed = False
        if e.key() == QtCore.Qt.Key_Shift:
            self.shiftPressed = False
        if e.key() == QtCore.Qt.Key_Alt:
            self.altPressed = False

class Window(QtGui.QMainWindow):
    fullscreen = False
    slidervalue = 0

    def __init__(self):
        super(Window, self).__init__()
        
        # focus
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        
        # dummy widget
        mainWidget = QtGui.QWidget(self)
        self.setCentralWidget(mainWidget)
        
        # OpenGL widget
        self.glWidget = GLWidget(self)
        
        # navigation slider
        self.navSlider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.navSlider.setMaximum(1000)
        self.navSlider.sliderMoved[int].connect(self.sliderChangedValue)
        
        # main layout: stack panel
        mainLayout = QtGui.QVBoxLayout(mainWidget)
        mainLayout.addWidget(self.glWidget)
        mainLayout.addWidget(self.navSlider)
        
        self.setWindowTitle("glplot")
        self.statusbar = self.statusBar()
        self.initMenubar()
        
    def initMenubar(self):
        self.menubar = self.menuBar()
        # file, nav, help menus
        self.fileMenu = self.menubar.addMenu('&File')
        self.navMenu = self.menubar.addMenu('&Navigation')
        self.helpMenu = self.menubar.addMenu('&?')
        
        # file commands
        self.addMenuItem('&Save image', 'S', 'Save image', self.saveEvent)
        self.addMenuItem('&Exit', 'Q', 'Exit application', self.exitEvent)
        
        # nav commands
        self.addMenuItem('&Reset', 'R', 'Reset', self.reset, self.navMenu)
        self.addMenuItem('&Home', [QtCore.Qt.Key_Home, 'G'], 'Home', self.homeEvent, self.navMenu)
        self.addMenuItem('&End', [QtCore.Qt.Key_End, 'H'], 'End', self.endEvent, self.navMenu)
        self.addMenuItem('&Fullscreen', 'F', 'Toggle fullscreen mode', \
                         self.fullscreenEvent, self.navMenu)
                         
        # help commands
        self.addMenuItem('&About', 'A', 'About', self.aboutEvent, self.helpMenu)
        
    def addMenuItem(self, name, shortcut, tooltip, actionMethod, menu=None):
        if menu is None:
            menu = self.fileMenu
        action = QtGui.QAction(QtGui.QIcon(), name, self)
        # multiple shortcuts
        if type(shortcut) is list:
            action.setShortcuts(shortcut)
        else:
            action.setShortcut(shortcut)
        action.setStatusTip(tooltip)
        action.triggered.connect(actionMethod)
        menu.addAction(action)
        
    def keyPressEvent(self, e):
        self.glWidget.keyPressEvent(e)
        
    def keyReleaseEvent(self, e):
        self.glWidget.keyReleaseEvent(e)
    
    def sliderChangedValue(self, value):
        self.glWidget.slide(value)
    
    def reset(self, e):
        self.glWidget.reset()
    
    def homeEvent(self, e):
        self.sliderChangedValue(self.navSlider.minimum())
        self.navSlider.setValue(self.navSlider.minimum())
        
    def endEvent(self, e):
        self.sliderChangedValue(self.navSlider.maximum())
        self.navSlider.setValue(self.navSlider.maximum())
    
    def fullscreenEvent(self, e):
        if not(self.fullscreen):
            self.showFullScreen()
            self.fullscreen = True
        else:
            self.showNormal()
            self.fullscreen = False
    
    def focusInEvent(self, event):
        self.glWidget.focusInEvent()
        
    def focusOutEvent(self, event):
        self.glWidget.focusOutEvent()
    
    def saveEvent(self, e):
        image = self.glWidget.capture()
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save as', 'capture.png'))
        image.save(filename)
    
    def aboutEvent(self, e):
        print ABOUT
        # QtGui.QMessageBox.about(self, 'About', ABOUT)
    
    def exitEvent(self, e):
        self.hide()
        # QtGui.qApp.quit()
    
    def load_data(self, data, databounds=None, options=None):
        self.glWidget.load_data(data, databounds, options=options)

Gdata = []
Goptions = []
windows = []
    
def figure():
    # reset
    global Gdata, Goptions
    Gdata = []
    Goptions = []
    
def plot(x, y=None, opt=None, lw=1.0):
    if type(y) is str:
        opt = y
        y = None
    if y is None:
        y = x.copy()
        x = arange(0, len(y))

    x = x.reshape((-1,1))
    y = y.reshape((-1,1))
    data = array(hstack((x,y)), float32)
    
    # parse options
    # we have here: i == len(Gdata)
    mode = "line"
    color = LINECOLORS[len(Gdata) % len(LINECOLORS)]
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
    Gdata.append(data)
    Goptions.append(dict(lw=lw, mode=mode, color=color))

# useful in interactive mode: shortcut to figure(); plot(...); show()
def iplot(*args, **kwargs):
    figure()
    plot(*args, **kwargs)
    show()
    
# show plots. use interactive=True for interactive use (in ipython for instance)
# or =False when launching the script with python
def show(interactive=True):
    # bounds for the different plots
    databounds = [0]
    databounds += [len(d) for d in Gdata]
    databounds = cumsum(databounds)
    
    # concatenate the data in a single array
    data = vstack(Gdata)

    # load and show the widget
    if not(interactive):
        app = QtGui.QApplication(sys.argv)
    window = Window()
    window.load_data(data, databounds, Goptions)
    window.show()
    windows.append(window)
    if not(interactive):
        app.exec_()
        # sys.exit(app.exec_())
    

    
if __name__ == '__main__':
    n = 100000
    x = linspace(0.0, 100.0, n)
    figure()
    plot(x,randn(n))
    plot(x,randn(n))
    show(False)