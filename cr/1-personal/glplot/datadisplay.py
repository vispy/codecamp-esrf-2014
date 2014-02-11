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

class DataDisplay(object):
    buffer = None
    bgcolor = (0, 0, 0, 0) # RGB 0-255
    tz0 = -10.

    def load(self, data, databounds=None, options=None, renormalize=True):
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
        
        if renormalize is not False:
            # renormalization x,y \in [0,1]
            if type(renormalize) is not tuple:
                self.xmin, self.xmax, self.ymin, self.ymax = min(x), max(x), min(y), max(y)
            elif len(renormalize) == 2:
                self.xmin, self.xmax = renormalize
                self.ymin, self.ymax = min(y), max(y)
            elif len(renormalize) == 4:
                self.xmin, self.xmax, self.ymin, self.ymax = renormalize
            if self.xmin == self.xmax:
                self.xmin = self.xmin - .5
                self.xmax = self.xmax + .5
            if self.ymin == self.ymax:
                self.ymin = self.ymin - .5
                self.ymax = self.ymax + .5
        self.data[:,0] = (x-self.xmin)/(self.xmax-self.xmin)
        self.data[:,1] = (y-self.ymin)/(self.ymax-self.ymin)
        
    def get_bounds(self):
        return self.xmin, self.xmax, self.ymin, self.ymax
        
    def bind_data_buffer(self):
        glBufferData(GL_ARRAY_BUFFER, self.data, GL_STATIC_DRAW)
        
    def initialize(self):
        glClearColor(*self.bgcolor)
        glEnableClientState(GL_VERTEX_ARRAY)
        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
        self.bind_data_buffer()
        
    def transform(self, tx, ty, sx, sy):
        glLoadIdentity()
        glScalef(sx, sy, 1.)
        glTranslatef(tx, ty, self.tz0)
        
    def paint_single(self, i0, n, options):
        mode = options["mode"] # "line" or "points"
        lw = options["lw"] # size of line or points in pixels
        color = options["color"] # should be a tuple 0-1
        if mode == "line":
            glLineWidth(lw)
            glmode = GL_LINE_STRIP
        elif mode == "points":
            glPointSize(lw)
            glmode = GL_POINTS
        glColor(*color)
        glDrawArrays(glmode, i0, n)
        
    def paint(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        if self.buffer is not None:
            glVertexPointer(2, GL_FLOAT, 0, None)
            glBindBuffer(GL_ARRAY_BUFFER, self.buffer)
            for i in xrange(len(self.databounds)-1):
                self.paint_single(self.databounds[i], self.databounds[i+1] - self.databounds[i], self.options[i])
            glFlush()
        
    def resize(self, w, h):
        # self.w, self.h = w, h
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
        glMatrixMode(GL_MODELVIEW)

