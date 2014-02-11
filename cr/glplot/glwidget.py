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
    
from navigation import Navigation
from navigationinterface import NavigationInterface,\
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, \
    KEY_CTRL, KEY_ALT, KEY_SHIFT
from signals import SIGNALS
from datadisplay import DataDisplay

class GLWidget(QtOpenGL.QGLWidget):
    # initial window size
    w, h = 1024, 768
    
    isInitialized = False
    
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.parent = parent
        self.setMouseTracking(True)
        
        self.nav = Navigation()
        self.navInterface = NavigationInterface(self.nav)
        self.dataDisplay = DataDisplay()
        
        # self.navigateSignal.connect(self.navigateEvent)
        SIGNALS.navigateSignal.connect(self.navigateEvent)

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
        
    def initializeGL(self):
        self.dataDisplay.initialize()
        self.isInitialized = True
        
    def paintGL(self):
        tx, ty = self.nav.get_translation()
        sx, sy = self.nav.get_scale()
        self.dataDisplay.transform(tx, ty, sx, sy)
        self.dataDisplay.paint()
    
    # handle window resizing
    def resizeGL(self, w, h):
        self.w, self.h = w, h
        self.dataDisplay.resize(w, h)
        
    def focusInEvent(self):
        pass
        
    def focusOutEvent(self):
        self.keyReleaseEvent(None)
        
    def navigateEvent(self):
        self.updateGL()
        
    def mousePressEvent(self, event):
        x, y = self.ncoord(event.pos())
        self.navInterface.mousePress(x, y, event.button())
            
    def mouseReleaseEvent(self, event):
        self.navInterface.mouseRelease()

    def mouseMoveEvent(self, event):
        x, y = self.ncoord(event.pos())
        self.navInterface.mouseMove(x, y)
        self.parent.statusbar.showMessage("%g, %g" % self.getMousePosition(x, y))
        if self.navInterface.mouseButton:
            SIGNALS.navigateSignal.emit()

    def getMousePosition(self, x, y):
        """
        convert mouse coordinates => data coordinates
        """
        tx, ty = self.nav.get_translation(False)
        sx, sy = self.nav.get_scale()
        # x = .5 * (1. - 1./sx) - tx + x/sx# + self.nav.offsetx
        # y = .5 * (1. - 1./sy) - ty + y/sy
        x, y = self.nav.get_data_coordinates(x, y)
        
        # inverse data normalization
        xmin, xmax, ymin, ymax = self.dataDisplay.get_bounds()
        x = xmin + x * (xmax - xmin)
        y = ymin + y * (ymax - ymin)
        y = -y
        return x, y
   
    def wheelEvent(self, event):
        self.navInterface.mouseWheel(event.delta())
        SIGNALS.navigateSignal.emit()
 
    def keyPressEvent(self, e):
        key = ""
        if e.key() == QtCore.Qt.Key_Control:
            key = KEY_CTRL
        if e.key() == QtCore.Qt.Key_Shift:
            key = KEY_SHIFT
        if e.key() == QtCore.Qt.Key_Alt:
            key = KEY_ALT
        if e.key() == QtCore.Qt.Key_Up:
            key = KEY_UP
        if e.key() == QtCore.Qt.Key_Down:
            key = KEY_DOWN
        if e.key() == QtCore.Qt.Key_Left:
            key = KEY_LEFT
        if e.key() == QtCore.Qt.Key_Right:
            key = KEY_RIGHT
        self.navInterface.keyPress(key)
        SIGNALS.navigateSignal.emit()
        
    def keyReleaseEvent(self, e):
        self.navInterface.keyRelease()

        
        
    # PUBLIC METHODS
    def slide(self, x, max):
        # slide, and update only if the transform is not null
        if (self.nav.slide(x, max)):
            self.updateGL()
        
    def reset(self):
        self.nav.reset()
        SIGNALS.navigateSignal.emit()
    
    def load_data(self, data, databounds=None, options=None):
        self.dataDisplay.load(data, databounds, options=options)
        # reload if already initialized
        if self.isInitialized:
            self.dataDisplay.bind_data_buffer()
            self.updateGL()
    
    def capture(self):
        glReadBuffer(GL_FRONT)
        image = self.grabFrameBuffer()
        return image
        
    