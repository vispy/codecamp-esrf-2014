"""Test the memory bandwith between CPU and GPU when executing OpenCL kernel.
"""
# !/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from vispy import app
from vispy.gloo import gl, Program, Texture2D, VertexBuffer

import pyopencl as cl
from pyopencl.tools import get_gl_sharing_context_properties

kernel = """
__kernel void clkernel(__global float2* glpos)
{
    unsigned int i = get_global_id(0);
    // The call below does nothing: this is just to test the overhead
    // of calling an OpenCL kernel at each frame.
    glpos[i].y *= 1;
}
"""

def clinit():
    """Initialize OpenCL with GL-CL interop.
    """
    plats = cl.get_platforms()
    ctx = cl.Context(properties=[
            (cl.context_properties.PLATFORM, plats[0])]
            + get_gl_sharing_context_properties(), devices =
                                      [plats[0].get_devices()[0]])
    queue = cl.CommandQueue(ctx)
    return ctx, queue

class CLBuffer(object):
    def __init__(self, vbo, kernel):
        self.vbo = vbo
        self.kernel = kernel
        
    def create(self):
        self.vbo.activate()
        self.ctx, self.queue = clinit()
        self.glclbuf = cl.GLBuffer(self.ctx, cl.mem_flags.READ_WRITE,
                                   int(self.vbo.handle))
        self.program = cl.Program(self.ctx, kernel).build()
        self.queue.finish()

    def execute(self, *args):
        cl.enqueue_acquire_gl_objects(self.queue, [self.glclbuf])
        self.program.clkernel(self.queue, (self.vbo.count,), None, self.glclbuf, *args)
        cl.enqueue_release_gl_objects(self.queue, [self.glclbuf])
        self.queue.finish()
        gl.glFlush()

VS = """
attribute vec2 a_position;

void main (void) {
    gl_Position = vec4(a_position.x, a_position.y, 0., 1.0);
}
"""

FS = """
void main()
{
    gl_FragColor = vec4(1., 1., 1., 1.);
}
"""

RES = 1024*1024

def gendata():
    return .25*np.random.randn(RES, 2).astype(np.float32)
data1 = gendata()
    
class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self)
        self.position = 50, 50
        self.size = 512, 512
        
        self.program = Program(VS, FS)
        self.vbo = VertexBuffer(data1)
        self.program['a_position'] = self.vbo
        
        self.clbuf = CLBuffer(self.vbo, kernel)
        
        self._timer = app.Timer(.01)
        self._timer.connect(self.on_timer)
        self._timer.start()
        
        self.measure_fps(.1, callback=self.fps_callback)

    def fps_callback(self, e):
        print "{0:.1f} FPS, {1:.1f} MB/s\r".format(e, e*RES*4*2/(1024.**2)),
        
    def on_resize(self, event):
        width, height = event.size
        gl.glViewport(0, 0, width, height)

    def on_initialize(self, event):
        self.clbuf.create()
        
    def on_paint(self, event):
        gl.glClearColor(0.2, 0.4, 0.6, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.program.draw(gl.GL_POINTS)

    def on_timer(self, event):
        self.clbuf.execute()
        self.update()

if __name__ == '__main__':
    c = Canvas()
    c.show()
    app.run()
