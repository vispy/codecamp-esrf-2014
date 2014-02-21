"""Test the memory bandwith between CPU and GPU when transferring textures.
"""
# !/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from vispy import app
from vispy.gloo import gl, Program, Texture2D, VertexBuffer


RES = 1024
positions = np.array([[-1, -1], 
                      [+1, -1],
                      [-1, +1],
                      [+1, +1]], np.float32)

texcoords = np.array([[1.0, 1.0],
                      [0.0, 1.0],
                      [1.0, 0.0],
                      [0.0, 0.0]], np.float32)

VS = """
attribute vec2 a_position;
attribute vec2 a_texcoord;
varying vec2 v_texcoord;

void main (void) {
    v_texcoord = a_texcoord;
    gl_Position = vec4(a_position.x, a_position.y, 0., 1.0);
}
"""

FS = """
uniform sampler2D u_tex;
varying vec2 v_texcoord;

void main()
{
    vec4 clr1 = texture2D(u_tex, v_texcoord);
    gl_FragColor.rgb = clr1.rgb;
    gl_FragColor.a = 1.0;
}
"""


def gendata():
    return np.random.rand(RES, RES, 3).astype(np.float32)
data1 = gendata()
data2 = gendata()
    
class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self)
        self.position = 50, 50
        self.size = 512, 512
        
        self.program = Program(VS, FS)
        self.tex = Texture2D(data1)
        self.program['a_position'] = VertexBuffer(positions)
        self.program['a_texcoord'] = VertexBuffer(texcoords)
        self.program['u_tex'] = self.tex
        
        self._timer = app.Timer(.01)
        self._timer.connect(self.on_timer)
        self._timer.start()
        
        self.measure_fps(.05, callback=self.fps_callback)

    def fps_callback(self, e):
        print "{0:.1f} FPS, {1:.1f} MB/s\r".format(e, e*RES*RES*4*3/(1024.**2)),

    def on_resize(self, event):
        width, height = event.size
        gl.glViewport(0, 0, width, height)

    def on_paint(self, event):
        gl.glClearColor(0.2, 0.4, 0.6, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.program.draw(gl.GL_TRIANGLE_STRIP)

    def on_timer(self, event):
        if event.iteration % 2 == 0:
            data = data1
        else:
            data = data2
        self.tex.set_subdata((0,0), data)
        self.update()

if __name__ == '__main__':
    c = Canvas()
    c.show()
    app.run()
