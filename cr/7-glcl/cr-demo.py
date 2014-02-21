
from PyQt4 import QtGui, QtCore, QtOpenGL
from PyQt4.QtOpenGL import QGLWidget
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo
import pyopencl as cl
from pyopencl.tools import get_gl_sharing_context_properties
import vispy.gloo as gloo

DEVICE = 0

# OpenCL kernel that generates a sine function.
clkernel = """
__kernel void clkernel(__global float2* glpos)
{
    //get our index in the array
    unsigned int i = get_global_id(0);

    // calculate the y coordinate and copy it on the GL buffer
    glpos[i].y = 0.5f * sin(10.0f * glpos[i].x);
}
"""

vertex = """
attribute vec2 position;
void main() {
   gl_Position = vec4(position,0.0,1.0);
}
"""
fragment = """
void main() {
   gl_FragColor = vec4(1.0,1.0,1.0,1.0);
}
"""


def clinit():
    """Initialize OpenCL with GL-CL interop.
    """
    plats = cl.get_platforms()
    ctx = cl.Context(properties=[
            (cl.context_properties.PLATFORM, plats[0])]
            + get_gl_sharing_context_properties(), devices =
                                      [plats[0].get_devices()[DEVICE]])
    queue = cl.CommandQueue(ctx)
    return ctx, queue

class GLPlotWidget(QGLWidget):
    # default window size
    width, height = 600, 600

    def set_data(self, data):
        """Load 2D data as a Nx2 Numpy array.
        """
        self.data = data
        self.count = data.shape[0]

    def initialize_buffers(self):
        """Initialize OpenGL and OpenCL buffers and interop objects,
        and compile the OpenCL kernel.
        """
        self.glbuf = gloo.VertexBuffer(data=self.data)
        self.prog = gloo.Program(vertex,fragment)
        self.prog["position"] = self.glbuf

        self.glbuf.activate()
        # WARNING: it seems that on some systems, the CL initialization
        # NEEDS to occur AFTER the activation of the GL object.
        # initialize the CL context
        self.ctx, self.queue = clinit()
        # create an interop object to access to GL VBO from OpenCL
        self.glclbuf = cl.GLBuffer(self.ctx, cl.mem_flags.READ_WRITE,
                                   int(self.glbuf.handle))
        # build the OpenCL program
        self.program = cl.Program(self.ctx, clkernel).build()
        # release the PyOpenCL queue
        self.queue.finish()

    def execute(self):
        """Execute the OpenCL kernel.
        """
        # get secure access to GL-CL interop objects
        cl.enqueue_acquire_gl_objects(self.queue, [self.glclbuf])
        # arguments to the OpenCL kernel
        kernelargs = (self.glclbuf,)
        # execute the kernel
        self.program.clkernel(self.queue, (self.count,), None, *kernelargs)
        # release access to the GL-CL interop objects
        cl.enqueue_release_gl_objects(self.queue, [self.glclbuf])
        self.queue.finish()

    def update_buffer(self):
        """Update the GL buffer from the CL buffer
        """
        # execute the kernel before rendering
        self.execute()
        gl.glFlush()

    def initializeGL(self):
        """Initialize OpenGL, VBOs, upload data on the GPU, etc.
        """
        # initialize OpenCL first
        self.initialize_buffers()
        # set background color
        gl.glClearColor(0,0,0,0)
        self.update_buffer()

    def paintGL(self):
        """Paint the scene.
        """
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.prog.draw(gl.GL_POINTS)

    def resizeGL(self, width, height):
        """Called upon window resizing: reinitialize the viewport. """
        self.width, self.height = width, height
        gl.glViewport(0, 0, width, height)

if __name__ == '__main__':
    import sys
    import numpy as np

    # define a QT window with an OpenGL widget inside it
    class TestWindow(QtGui.QMainWindow):
        def __init__(self):
            super(TestWindow, self).__init__()
            # generate random data points
            self.data = np.zeros((10000,2))
            self.data[:,0] = np.linspace(-1.,1.,len(self.data))
            self.data = np.array(self.data, dtype=np.float32)
            # initialize the GL widget
            self.widget = GLPlotWidget()
            self.widget.set_data(self.data)
            # put the window at the screen position (100, 100)
            self.setGeometry(100, 100, self.widget.width, self.widget.height)
            self.setCentralWidget(self.widget)
            self.show()

    # create the QT App and window
    app = QtGui.QApplication(sys.argv)
    window = TestWindow()
    window.show()
    app.exec_()
