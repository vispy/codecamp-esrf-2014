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
from glwidget import GLWidget
from signals import SIGNALS


class GLPlot(QtGui.QMainWindow):
    fullscreen = False
    slidervalue = 0

    def __init__(self, interactive=True, windowIndex=0, glwidgetclass=GLWidget):
        """
        windowIndex = index of the window, used to know which window to clear when
        closing a window
        """
        super(GLPlot, self).__init__()
        self.interactive = interactive
        self.windowIndex = windowIndex
        
        # focus
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        
        # dummy widget
        mainWidget = QtGui.QWidget(self)
        self.setCentralWidget(mainWidget)
        
        # OpenGL widget
        self.glWidget = glwidgetclass(self)
        
        # navigation slider
        self.navSlider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.navSlider.setMaximum(1000)
        self.navSlider.sliderMoved[int].connect(self.sliderChangedValue)
        
        # main layout: stack panel
        mainLayout = QtGui.QVBoxLayout(mainWidget)
        mainLayout.addWidget(self.glWidget)
        mainLayout.addWidget(self.navSlider)
        
        SIGNALS.navigateSignal.connect(self.navigateEvent)
        
        self.setWindowTitle("GLPlot")
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
        self.addMenuItem('&Exit', 'Q', 'Exit application', self.closeEvent)
        
        # nav commands
        self.addMenuItem('&Reset', 'R', 'Reset', self.reset, self.navMenu)
        self.addMenuItem('&Start', [QtCore.Qt.Key_Home, 'G'], 'Start', self.startEvent, self.navMenu)
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
    
    def navigateEvent(self):
        slide = self.glWidget.nav.get_slide(self.navSlider.maximum())
        self.navSlider.setValue(slide)
        
    def sliderChangedValue(self, value):
        self.glWidget.slide(value, self.navSlider.maximum())
    
    def reset(self, e):
        self.glWidget.reset()
        self.navSlider.setValue(self.navSlider.minimum())
    
    def startEvent(self, e):
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
        # print ABOUT
        QtGui.QMessageBox.about(self, 'About', ABOUT)
    
    def closeEvent(self, e):
        self.hide()
        SIGNALS.windowCloseSignal.emit(self.windowIndex)
        if not(self.interactive):
            QtGui.qApp.quit()
    