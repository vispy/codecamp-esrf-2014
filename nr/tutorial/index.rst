===============================
Modern OpenGL tutorial (python)
===============================

----------------------------------------
Nicolas P. Rougier - ERSF Code camp 2014
----------------------------------------

.. contents::
   :local:
   :depth: 2


This tutorial is part of the `vispy project <http://vispy.org>`_ which is an
OpenGL-based interactive visualization library in Python. During this tutorial,
only the vispy low-level interface (named **gloo**) will be used.


.. Sources are available `here <index.rst>`_. Figures are in the `figures
   <figures/>`_ directory and all scripts are located in the `scripts <scripts/>`_
   directory. Github repository is `here
   <https://github.com/rougier/opengl-tutorial>`_

All code and material is licensed under a `Creative Commons Attribution (CC by
4.0) <http://creativecommons.org/licenses/by/4.0/>`_


**Requirements**:

 * ``•`` Python 2.7 or higher
 * ``•`` PyOpenGL 3.0 or higher
 * ``•`` Numpy 1.5 or higher
 * ``•`` Vispy 0.3 or higher

|

A stand-alone **gloo** package is distributed along this tutorial but you
should use the vispy.gloo package from the latest vispy distribution which is
more up-to-date.



Introduction
============

Before diving into the core tutorial, it is important to understand that OpenGL
has evolved over the years and a big change occured in 2003 with the
introduction of the dynamic pipeline (OpenGL 2.0), i.e. the use of shaders that
allow to have direct access to the GPU.

.. note::

   ES is a light version of OpenGL for embedded systems such as tablets or
   mobiles. There also exists WebGL which is very similar to ES but is not shown on
   this graphic.

.. image:: images/gl-history.png
   :width: 75%

|


Before this version, OpenGL was using a fixed pipeline and you may still find a
lot of tutorials that still use this fixed pipeline. How to know if a tutorial
address the fixed pipeline ? It's relatively easy.  If you see GL commands such
as::

   glVertex, glColor, glLight, glMaterial
   glBegin, glEnd
   glMatrix, glMatrixMode, glLoadIdentity
   glPushMatrix, glPopMatrix
   glRect, glPolygonMode
   glBitmap, glAphaFunc
   glNewList, glDisplayList
   glPushAttrib, glPopAttrib
   glVertexPointer, glColorPointer, glTexCoordPointer, glNormalPointer

then it's most certainly a tutorial that adress the fixed pipeline.
While modern OpenGL is far more powerful than the fixed pipeline version, the
learning curve may be a bit steeper. This tutorial will try to help you start
using it.




What are shaders ?
------------------

.. Note::

   The shader language is called glsl.  There are many versions that goes from 1.0
   to 1.5 and subsequents version get the number of OpenGL version. Last version
   is 4.4 (February 2014).

Shaders are pieces of program (using a C-like language) that are build onto the
GPU and executed during the rendering pipeline. Depending on the nature of the
shaders (there are many types depending on the version of OpenGL you're using),
they will act at different stage of the rendering pipeline. To simplify this
tutorial, we'll use only **vertex** and **fragment** shader as shown below:

.. image:: images/gl-pipeline.png
   :width: 75%

|

A vertex shader acts on vertices and is supposed to output the vertex
**position** (→ ``gl_Position``) on the viewport (i.e. screen). A fragment shader
acts at the fragment level and is supposed to output the **color**
(→ ``gl_FragColor``) of the fragment. Hence, a minimal vertex shader is::

  void main()
  {
      gl_Position = vec4(0.0,0.0,0.0,1.0);
  }

while a minimal fragment shader would be::

  void main()
  {
      gl_FragColor = vec4(0.0,0.0,0.0,1.0);
  }

These two shaders are not very useful since the first will transform any
vertex into the null vertex while the second will output the black color for
any fragment. We'll see later how to make them to do more useful things.

One question remains: when are those shaders exectuted exactly ? The vertex
shader is executed for each vertex that is given to the rendering pipeline
(we'll see what does that mean exactly later) and the fragment shader is
executed on each fragment that is generated after the vertex stage. For
example, in the simple figure above, the vertex would be called 3 times, once
for each vertex (1,2 and 3) while the fragment shader would be executed 21
times, once for each fragment (pixel).


What are buffers ?
------------------

We explained earlier that the vertex shader act on the vertices. The question
is thus where do those vertices comes from ? The idea of modern GL is that
vertices are stored on the GPU and needs to be uploaded (only once) to the GPU
before rendering. The way to do that is to build buffers onto the CPU and to
send them onto the GPU. If your data does not change, no need to upload it
again. That is the big difference with the previous fixed pipeline where data
were uploaded at each rendering call (only display lists were built into GPU
memory).

But what is the structure of a vertex ? OpenGL does not assume anything about
your vertex structure and you're free to use as many information you may need
for each vertex. The only condition is that all vertices from a buffer have the
same structure (possibly with different content). This again is a big
difference with the fixed pipeline where OpenGL was doing a lot of complex
rendering stuff for you (projections, lighting, normals, etc.) with an implicit
fixed vertex structure. Now you're on your own...

| **Good news** is that you're now free to do virtually anything you want.
| **Bad news** is that you have to program everything, even the most basic things like projection and lighting.

|

Let's take a simple example of a vertex structure where we want each vertex to
hold a position and a color. The easiest way to do that in python is to use a
structured array using the `numpy <http://www.numpy.org>`_ library::

  data = numpy.zeros(4, dtype = [ ("position", np.float32, 3),
                                  ("color",    np.float32, 4)] )

We just created a CPU buffer with 4 vertices, each of them having a
``position`` (3 floats for x,y,z coordinates) and a ``color`` (4 floats for
red, blue, green and alpha channels). Note that we explicitely chose to have 3
coordinates for ``position`` but we may have chosen to have only 2 if were to
work in two-dimensions only. Same holds true for ``color``. We could have used
only 3 channels (r,g,b) if we did not want to use transparency. This would save
some bytes for each vertex. Of course, for 4 vertices, this does not really
matter but you have to realize it **will matter** if you data size grows up to
one or ten million vertices.



What are uniforms, attributes and varyings ?
--------------------------------------------

At this point in the tutorial, we know what are shaders and buffers but we
still need to explain how they may be connected together. So, let's consider
again our CPU buffer::

  data = numpy.zeros(4, dtype = [ ("position", np.float32, 2),
                                  ("color",    np.float32, 4)] )

We need to tell the vertex shader that it will have to handle vertices where a
position is a tuple of 3 floats and color is a tuple of 4 floats. This is
precisely what attributes are meant for. Let us change slightly our previous
vertex shader::

  attribute vec2 position;
  attribute vec4 color;
  void main()
  {
      gl_Position = vec4(position, 0.0, 1.0);
  }

This vertex shader now expects a vertex to possess 2 attributes, one named
``position`` and one named ``color`` with specified types (vec3 means tuple of
3 floats and vec4 means tuple of 4 floats). It is important to note that even
if we labeled the first attribute ``position``, this attribute is not yet bound
to the actual ``position`` in the numpy array. We'll need to do it explicitly
at some point in our program and there is no automagic that will bind the numpy
array field to the right attribute, you'll have to do it yourself, but we'll
see that later.

The second type of information we can feed the vertex shader are the uniforms
that may be considered as constant values (across all the vertices). Let's say
for example we want to scale all the vertices by a constant factor ``scale``,
we would thus write::

  uniform float scale;
  attribute vec2 position;
  attribute vec4 color;
  void main()
  {
      gl_Position = vec4(position*scale, 0.0, 1.0);
  }

Last type is the varying type that is used to pass information between the
vertex stage and the fragment stage. So let us suppose (again) we want to pass
the vertex color to the fragment shader, we now write::

  uniform float scale;
  attribute vec2 position;
  attribute vec4 color;
  varying vec4 v_color;

  void main()
  {
      gl_Position = vec4(position*scale, 0.0, 1.0);
      v_color = color;
  }

and then in the fragment shader, we write::

  varying vec4 v_color;

  void main()
  {
      gl_FragColor = v_color;
  }

The question is what is the value of ``v_color`` inside the fragment shader ?
If you look at the figure that introduced the gl pipleline, we have 3 vertices and 21
fragments. What is the color of each individual fragment ?

The answer is *the interpolation of all 3 vertices color*. This interpolation
is made using distance of the fragment to each individual vertex. This is a
very important concept to understand. Any varying value is interpolated between
the vertices that compose the elementary item (mostly, line or triangle).


Summary
-------

We're done with this part. We know we need a structured numpy array to hold our
vertices, a vertex shader to instruct the GPU what to do with the vertices and
a fragment shader to compute the final color. Now comes the hard part where
we'll put all this together...

Still time to flee...

|
|
|

Too late...


Hello (flat) world!
===================

Before using OpenGL, we need to open a window with a valid GL context. This can
be done using toolkit such as Gtk, Qt or Wx or any native toolkit (Windows,
Linux, OSX). Note there also exists dedicated toolkits such as GLFW or GLUT and
the advantage of GLUT is that it's already installed alongside OpenGL. Even if
it is now deprecated, we'll use GLUT since it's a very lightweight toolkit and
does not require any extra package. Here is a minimal setup that should open a
window with garbage on it (since we do not even clear the window):

.. note::

   GLUT is now deprecated and you might prefer to use `GLFW <http://www.glfw.org>`_
   which is actively maintained.

::

  import OpenGL.GL as gl
  import OpenGL.GLUT as glut

  def display():
      glut.glutSwapBuffers()

  def reshape(width,height):
      gl.glViewport(0, 0, width, height)

  def keyboard( key, x, y ):
      if key == '\033':
          sys.exit( )

  glut.glutInit()
  glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA)
  glut.glutCreateWindow('Hello world!')
  glut.glutReshapeWindow(512,512)
  glut.glutReshapeFunc(reshape)
  glut.glutDisplayFunc(display)
  glut.glutKeyboardFunc(keyboard)
  glut.glutMainLoop()

The ``glutInitDisplayMode`` tells OpenGL what are the context properties. At
this stage, we only need a swap buffer (we draw on one buffer while the other
is displayed) and we use a full RGBA 32 bits color buffer (8 bits per
channel).

Let's consider again some data (in 2 dimensions)::

  data = numpy.zeros(4, dtype = [ ("position", np.float32, 2),
                                  ("color",    np.float32, 4)] )



The hard way (OpenGL)
---------------------

Building the program
++++++++++++++++++++

.. note::

   ``vertex_code`` and ``fragment_code`` correspond to the vertex and fragment shaders
   code as shown above.

Building the program is relatively straightforward provided we do not
check for errors. First we need to request program and shader slots from GPU::

    program  = gl.glCreateProgram()
    vertex   = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)

Then we can compile shaders into GPU objects::

    # Set shaders source
    gl.glShaderSource(vertex, vertex_code)
    gl.glShaderSource(fragment, fragment_code)

    # Compile shaders
    gl.glCompileShader(vertex)
    gl.glCompileShader(fragment)


We can now build and link the program::

    gl.glAttachShader(program, vertex)
    gl.glAttachShader(program, fragment)
    gl.glLinkProgram(program)

We can not get rid of shaders, they won't be used again::

    gl.glDetachShader(program, vertex)
    gl.glDetachShader(program, fragment)


Finally, we make program the default program to be ran. We can do it now
because we'll use a single in this example::

    gl.glUseProgram(program)


Building the buffer
+++++++++++++++++++

Building the buffer is even simpler::

    # Request a buffer slot from GPU
    buffer = gl.glGenBuffers(1)

    # Make this buffer the default one
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)

    # Upload data
    gl.glBufferData(gl.GL_ARRAY_BUFFER, data.nbytes, data, gl.GL_DYNAMIC_DRAW)


Binding the buffer to the program
+++++++++++++++++++++++++++++++++

Binding the buffer to the program needs some work and computations. We need to
tell the GPU how to read the buffer and bind each value to the relevant
attribute. To do this, GPU needs to kow what is the stride between 2
consecutive element and what is the offset to read one attribute::

    stride = data.strides[0]

    offset = ctypes.c_void_p(0)
    loc = gl.glGetAttribLocation(program, "position")
    gl.glEnableVertexAttribArray(loc)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
    gl.glVertexAttribPointer(loc, 3, gl.GL_FLOAT, False, stride, offset)

    offset = ctypes.c_void_p(data.dtype["position"].itemsize)
    loc = gl.glGetAttribLocation(program, "color")
    gl.glEnableVertexAttribArray(loc)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
    gl.glVertexAttribPointer(loc, 4, gl.GL_FLOAT, False, stride, offset)

Here we're basically telling the program how to bind data to the relevant
attribute. This is made by providing the stride of the array (how many bytes
between each record) and the offset of a given attribute.


Binding the uniform
+++++++++++++++++++

Binding the uniform is much more simpler. We request the location of the
uniform and we upload the value using the dedicated function to upload one
float only::

    loc = gl.glGetUniformLocation(program, "scale")
    gl.glUniform1f(loc, 1.0)


Choosing primitives
+++++++++++++++++++

Before rendering, we need to tell OpenGL what to do with our vertices,
i.e. what does these vertices describe in term of geometrical primitives.
This is quite an important parameter since this determines how many fragments
will be actually generated by the shape as illustrated on the image below:

.. image:: images/gl-primitives.png
   :width: 75%

There exist other primitives but we won't used them during this tutorial (and
they're mainly related to *geometry shaders* that are not introduced in this
tutorial). Since we want do display a square, we can use 2 triangles to make a
square and thus we'll use a ``GL_TRIANGLE_STRIP`` primitive. We'll see later
how to make more complex shapes.


Setting data
++++++++++++

We're almost ready to render something but let's first fill some values::

  data['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
  data['position'] = [ (-1,-1),   (-1,+1),   (+1,-1),   (+1,+1)   ]

If the color field makes sense (normalized RGBA values), why do we use
coordinates such as (-1,-1) for vertex position ? We know the windows size is
512x512 pixels in our case, so why not use (0,0) or (512,512) instead ?

At this point in the tutorial, OpenGL does not really care of the actual size
of the window (also called viewport) in terms of pixels. If you look at the
GLUT code above, you may have noticed this line::

  def reshape(width,height):
      gl.glViewport(0, 0, width, height)

This function is called whenever the window is resized and the ``glViewport``
call does two things. It instructs OpenGL of the current window size and it
setup an implicit *normalized* coordinate system that goes from (-1,-1) (for the
bottom-left corner) to (+1,+1) to top-right corner. Thus, our vertices position
cover the whole window.


Rendering
+++++++++

.. image:: images/hello-world.png
   :target: scripts/hello-world-gl.py
   :align: right
   :width: 15%


Ok, we're done, we can now rewrite the display function as::

  def display():
      gl.glClear(gl.GL_COLOR_BUFFER_BIT)
      gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
      glut.glutSwapBuffers()

The 0, 4 arguments in the ``glDrawArrays`` tells OpenGL we want to display 4
vertices from our array and we start at vertex 0.

Click on the image on the right to get the source.



The easy way (gloo)
-------------------

.. image:: images/hello-world.png
   :target: scripts/hello-world-gloo.py
   :align: right
   :width: 15%


Since the above method is quite cumbersome, we'll now use the gloo interface.
Now, we can just write::

    program = gloo.Program(vertex, fragment, count=4)
    program['color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
    program['position'] = [ (-1,-1),   (-1,+1),   (+1,-1),   (+1,+1)   ]
    program['scale']    = 1.0

Gloo takes care of building the buffer because we specified the vertex count
value and will also bind the relevant attributes and uniforms to the
program provided. To render the scene, we can now write::

    program.draw(gl.GL_TRIANGLE_STRIP)

Click on the image on the right to get the source.


A step further
--------------

.. image:: images/hello-world-scale.png
   :target: scripts/hello-world-gloo-scale.py
   :align: right
   :width: 15%

The nice thing with gloo is that it takes care of any change in uniform or
attribute values. If you change them through the program interface, these
values will be updated on the GPU just-in-time. So, let's have some animation
by making the scale value to oscillate betwen 0 and 1. To do this, we need a
simple timer function where we'll update the scale value::

  def timer(fps):
      global clock
      clock += 0.005 * 1000.0/fps
      program['scale'] = np.cos(clock)
      glut.glutTimerFunc(1000/fps, timer, fps)
      glut.glutPostRedisplay()

Click on the image on the right to get the source.


Exercices
---------

Quad rotation
+++++++++++++

.. image:: images/hello-world-rotate.png
   :target: scripts/hello-world-gloo-rotate.py
   :align: right
   :width: 15%

At this point, you can start experiencing on your own. For example, instead of
scaling the quad, try to make it rotate. Note that you have access to the
``sin`` and ``cos`` function from within the shader.

Viewport aspect
+++++++++++++++

.. image:: images/hello-world-aspect.png
   :target: scripts/hello-world-gloo-viewport-aspect.py
   :align: right
   :width: 15%

Since the viewport is normalized, this means the aspect ratio of our quad is
not always 1, it can become wider or taller, depending on how the actual shape
of the window. How to change the reshape function (viewport call) to achieve a
constant ratio of 1 (square) ?


Quad aspect
+++++++++++

.. image:: images/hello-world-aspect-2.png
   :target: scripts/hello-world-gloo-quad-aspect.py
   :align: right
   :width: 15%

In the previous exercice, we manipulated the viewport such a to have a constant
ratio of 1 for the viewport. We could however only manipulate the vertex
position from within the shader, provided we know the size of the viewport, how
would you do this ?


Hello (cubic) world!
====================

*But... but, where is the 3D ? I want 3D ! I came to this tutorial because of 3D! Give me 3D !*

Actually, you've got all the pieces to render a 3D scene. Remember the bad news we talked about a few sections ago ?

::

   You have to program everything, even the most basic things like projection and lighting.

So let's just do that.




Projection matrix
-----------------

We need first to define what do we want to view, that is, we need to define a
viewing volume such that any object within the volume (even partially) will be
rendered while objects outside won't. On the image below, the yellow and red
spheres are within the volume while the green one is not and does not appear on
the projection.

.. image:: images/ViewFrustum.png
   :width: 60%

There exist many different ways to project a 3D volume onto a 2D screen but
we'll only use the `perspective projection
<https://en.wikipedia.org/wiki/Perspective_(graphical)>`_ (distant objects
appear smaller) and the `orthographic projection
<https://en.wikipedia.org/wiki/Orthographic_projection_(geometry)>`_ which is a
parallel projection (distant objects have the same size as closer ones) as
illustrated on the image above. Until now (previous section), we have been
using implicitly an orthographic projection in the z=0 plane.

|

.. note::

   In older versions of OpenGL, these matrices were available as `glFrustum
   <https://www.opengl.org/sdk/docs/man2/xhtml/glFrustum.xml>`_ and `glOrtho
   <https://www.opengl.org/sdk/docs/man2/xhtml/glOrtho.xml>`_.


Depending on the projection we want, we will use one of the two projection matrices
below:

**Perspective matrix**

.. image:: images/frustum-matrix.png
   :width: 40%

|

**Orthographic matrix**

.. image:: images/ortho-matrix.png
   :width: 40%

|

At this point, it is not necessary to understand how these matrices were built.
Suffice it to say they are standard matrices in the 3D world. Both suppose the
viewer (=camera) is located at position (0,0,0) and is looking in the direction
(0,0,1).

There exists a second form of the perpective matrix that might be easier to
manipulate. Instead of specifying the right/left/top/bottom planes, we'll use
field of view in the horizontal and vertical direction:

**Perspective matrix**

.. image:: images/perspective-matrix.png
   :width: 40%

|

where ``fovy`` specifies the field of view angle, in degrees, in the y
direction and ``aspect`` specifies the aspect ratio that determines the field
of view in the x direction.


Model and view matrices
-----------------------

We are almost done with matrices. You may have guessed that the above matrix
requires the viewing volume to be in the z direction. We could design our 3D
scene such that all objects are withing this direction but it would not be very
convenient. So instead, we'll use a view matrix that will map the the world
space to camera space. This is pretty much as if we were orienting the camera
at a given position and look toward a given direction. In the meantime, we can
further refine the whole pipeline by providing a model matrix that will maps
the object's local coordinate space into world space. For example, this wil be
useful for rotating an object around its center. To sum up, we need:

* ``•`` **Model matrix** maps from an object's local coordinate space into world space
* ``•`` **View matrix** maps from world space to camera space
* ``•`` **Projection matrix** maps from camera to screen space




Building cube
-------------

We need to define what we mean by a *cube* since there is not such thing as as
cube in OpenGL. A cube, when seen from the outside has 6 faces, each being a
square. We just saw that to render a square, we need two triangles. So, 6
faces, each of them being made of 2 triangles, we need 12 triangles.

How many vertices then ? 12 triangles ? 3 vertices per triangles ? 36 vertices
might be a reasonable answer but we can also notice that each vertex is part of
3 different faces actually, so instead we'll use no more than 8 vertices and
tell explicitly OpenGL what to draw with them::

   V = np.zeros(8, [("position", np.float32, 3)])
   V["position"] = [[ 1, 1, 1], [-1, 1, 1], [-1,-1, 1], [ 1,-1, 1],
                    [ 1,-1,-1], [ 1, 1,-1], [-1, 1,-1], [-1,-1,-1]]

These describes vertices of a cube cented on (0,0,0) that goes from (-1,-1,-1)
to (+1,+1,+1). Then we compute (mentally) what are the triangles for each face, i.e. we
describe triangles in terms of vertices index (relatively to the ``V`` array we
just defined)::

  I = [0,1,2, 0,2,3,  0,3,4, 0,4,5,  0,5,6, 0,6,1,
       1,6,7, 1,7,2,  7,4,3, 7,3,2,  4,7,6, 4,6,5]

We now need to upload these data to the GPU. Using gloo, the easiest way is to use a VertexBuffer for vertices data and an IndexBuffer for indices data::

  vertices = gloo.VertexBuffer(V)
  indices = gloo.IndexBuffer(I)



Building matrices
-----------------

.. Note::

   Note that the view matrix is a translation along z. We actually move away
   from the center while looking into the (positive) z direction.


All the common matrix operations can be found in the `transforms.py
<scripts/transforms.py>`_ script which define ortho, frustum and perspective
matrices as well as rotation, translation and scaling operations. We won't say
much more about these and you might want to read a book about geometry to
understand how this work, especially when compositing rotation, translation and
scaling (order is important)::

  view = np.eye(4,dtype=np.float32)
  model = np.eye(4,dtype=np.float32)
  projection = np.eye(4,dtype=np.float32)
  translate(view, 0,0,-5)
  program['model'] = model
  program['view'] = view
  program['projection'] = projection
  phi, theta = 0,0



It is now important to update the projection matrix whenever the window is
resized (because aspect ratio may have changed)::

  def reshape(width,height):
      gl.glViewport(0, 0, width, height)
      projection = perspective( 45.0, width/float(height), 2.0, 10.0 )
      program['projection'] = projection


Rendering
---------

.. image:: images/rotating-cube.png
   :target: scripts/rotating-cube.py
   :align: right
   :width: 20%

Rotating the cube means computing a model matrix such that the cube rotate
around its center. We'll do that in the timer function and rotate the cube
around the z axis (theta), then around the y axis (phi)::

  def timer(fps):
      global theta, phi
      theta += .5
      phi += .5
      model = np.eye(4, dtype=np.float32)
      rotate(model, theta, 0,0,1)
      rotate(model, phi, 0,1,0)
      program['model'] = model
      glut.glutTimerFunc(1000/fps, timer, fps)
      glut.glutPostRedisplay()


We're now alsmost ready to render the whole scene but we need first to modify
the GLUT initialization a little bit. Previously, we used::

  glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA)

But now, we're explicity dealing with 3D, meaning some rendered triangles may
be behind some others and we don't want to handle rendering order to deal with
that. OpenGL will take care of that provided we declared we'll use a depth
buffer. We thus need to modify glut initialization as and to tell OpenGL to use
the depth buffer::

  glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH)
  gl.glEnable(gl.GL_DEPTH_TEST)


and when clear the scene, we have to take care of clearing the depth buffer as well::

    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

Finally, to render the cube using the specified triangles, we write::

    program.draw(gl.GL_TRIANGLES, indices)

Click on the image on the right to get the source.

|
|
|

*But is't ugly !* Yes, of course !

We have no color (but red), no texture and no light. What did you expect ?



A step further
==============

I feel you're a bit frustated so let's build a nice colored, outlined, lighted
rotating cube.


Colored cube
------------

.. image:: images/colored-cube.png
   :target: scripts/colored-cube.py
   :align: right
   :width: 20%

Now we'll discover why **gloo** is so useful. To add color per vertex to the
cube, we simply define the vertex structure as::

  V = np.zeros(8, [("position", np.float32, 3),
                   ("color",    np.float32, 4)])
  V["position"] = [[ 1, 1, 1], [-1, 1, 1], [-1,-1, 1], [ 1,-1, 1],
                   [ 1,-1,-1], [ 1, 1,-1], [-1, 1,-1], [-1,-1,-1]]
  V["color"]    = [[0, 1, 1, 1], [0, 0, 1, 1], [0, 0, 0, 1], [0, 1, 0, 1],
                   [1, 1, 0, 1], [1, 1, 1, 1], [1, 0, 1, 1], [1, 0, 0, 1]]

And we're done ! Well, actually, we also need to slightly modify the vertex
shader since ``color`` is now an attribute and not a uniform.

Click on the image on the right to get the source.


Outlined cube
-------------

.. note::

   From now on, we'll use prefixes to distinguish uniforms (u\_), attributes
   (a\_) and varyings (v\_) in shader sources and buffers fields.

.. image:: images/outlined-cube.png
   :target: scripts/outlined-cube.py
   :align: right
   :width: 20%

To outline the cube, we need to draw lines between couple of vertices on each
face. 4 lines for the back and front face and 2 lines for the top and bottom
faces. Why only 2 lines for top and bottom ? Because lines are shared between
the faces. So overall we need 12 lines and we need to compute the corresponding
indices (I did it for your)::

  O = [0,1, 1,2, 2,3, 3,0,
       4,7, 7,6, 6,5, 5,4,
       0,5, 1,6, 2,7, 3,4 ]
  outline = IndexBuffer(O)

Then we draw the cube twice. One time using triangles and the indices index
buffer and one time using lines with the outline index buffer.  We need also to
add some OpenGL black magic to make things nice. It's not very important to
understand it at this point. The main it solves it to make sure line is "above"
the cube because we paint a line on a surface.

Click on the image on the right to get the source.


Textured cube
-------------

To be written.


Lighted cube
------------

.. image:: images/lighted-cube.png
   :target: scripts/lighted-cube.py
   :align: right
   :width: 20%

To have a lighted cube we need two things: a light source and surface
normals. Then we can apply light equation on each fragment depending on the
amount of light it receives. This is computed using the suface normal.

But we have a problem to solve. We need to compute normals for each surfaces,
which is rather easy but we need to give this information to the GPU via the
vertex structure. Since our vertices are shared between all the surfaces, it is
a problem. If you look at any vertex, you'll see it is shared between 3
distinct faces, each having a different normal. This means we'll have to
duplicate our vertices and to attach the right normal vector depending on the
face they belong. Hence, we now need 4 distinct vertices for each faces for a
total of 24 vertices.

The actual building of this new cube data is rather boring and I won't
detailed it here. The whole code is available from `cube.py <scripts/cube.py>`_
that has a single ``cube`` function that return cube vertices, faces and
outlines as 3 numpy arrays.

We can now define a light using a position and an intensity (color). This is
called a positional point light which send light in any direction (as opposed
for example to adirectional light such as a spotlight). There exist many
different light models and this one is probably the simplest. I won't explain
everything here (it would require a full tutorial only for this topic), but
here is the resulting fragment shader which is pretty self-explanatory::

  uniform mat4 u_model;
  uniform mat4 u_view;
  uniform mat4 u_normal;

  uniform vec3 u_light_intensity;
  uniform vec3 u_light_position;

  varying vec3 v_position;
  varying vec3 v_normal;
  varying vec4 v_color;

  void main()
  {
    // Calculate normal in world coordinates
    vec3 normal = normalize(u_normal * vec4(v_normal,1.0)).xyz;

    // Calculate the location of this fragment (pixel) in world coordinates
    vec3 position = vec3(u_view*u_model * vec4(v_position, 1));

    // Calculate the vector from this pixels surface to the light source
    vec3 surfaceToLight = u_light_position - position;

    // Calculate the cosine of the angle of incidence (brightness)
    float brightness = dot(normal, surfaceToLight) / (length(surfaceToLight) * length(normal));
    brightness = max(min(brightness,1.0),0.0);

    // Calculate final color of the pixel, based on:
    // 1. The angle of incidence: brightness
    // 2. The color/intensities of the light: light.intensities
    // 3. The texture and texture coord: texture(tex, fragTexCoord)

    gl_FragColor = v_color * brightness * vec4(u_light_intensity, 1);
  }


Click on the image on the right to get the source.



Gloo API
========

Vertex Buffer
-------------

A VertexBuffer represents vertex data that can be uploaded to GPU memory. They
can have a local (CPU) copy or not such that in the former case, the buffer is
read-write while in the latter case, the buffer is write-only.

The (internal) shape of a vertex buffer is always one-dimensional.

The (internal) dtype of a vertex buffer is always structured.

Elementary allowed dtype are:
np.uint8, np.int8, np.uint16, np.int16, np.float32, np.float16

All GPU operations are deferred and executed just-in time (automatic).


Default parameter
+++++++++++++++++
store = True, copy = False, resizeable = True


Creation from existing data
+++++++++++++++++++++++++++

Use given data as CPU storage::

  V = VertexBuffer(data=data, store=True, copy=False)

Use a copy of given data as CPU storage::

  V = VertexBuffer(data=data, store=True, copy=True)

Do not use CPU storage::

  V = VertexBuffer(data=data, store=False)


Creation from dtype and size
++++++++++++++++++++++++++++

Create a CPU storage with given size::

  V = VertexBuffer(dtype=dtype, size=size, store=True)

Do not use CPU storage::

  V = VertexBuffer(dtype=dtype, size=size, store=False)



Setting data (set_data)
+++++++++++++++++++++++

Any contiguous block of data can be set using the ``set_data`` method. This
method can also be used to resize the buffer. When setting data, it is possible
to specify whether to store a copy of given data hence freezing the state of
the data. It is important because the actual upload is deferred and data can be
changed before the actual upload occurs.

This example results in 2 pending operations but only the "2" value will be
uploaded (2 in data[:10] and 2 in data[10:])::

  V = VertexBuffer(...)
  data[...] = 1
  V.set_data(data[:10], copy=False)
  data[...] = 2
  V.set_data(data[10:], copy=False)

This example results in 2 pending operations and the "1" and "2" values will
actually be uploaded (1 in data[:10] and 2 in data[10:])::

  V = VertexBuffer(...)
  data[...] = 1
  V.set_data(data[:10], copy=True)
  data[...] = 2
  V.set_data(data[10:], copy=True)



Setting data (setitem)
++++++++++++++++++++++

If buffer has CPU storage, any numpy operations is allowed since the operation
is performed on CPU data and modified part are registered for uploading::

  V = VertexBuffer(...)
  V[:10] = data # ok
  V[::2] = data # ok

If buffer has no CPU storage, only numpy operations that affect a contiguous
block of data are allowed. This restriction is necessary because we cannot
upload strided data::

  V = VertexBuffer(...)
  V[:10] = data # ok
  V[::2] = data # error


Getting data (getitem)
++++++++++++++++++++++

Accessing data from a VertexBuffer (base) returns a VertexBuffer (view) that is
linked to the base buffer. Accessing data from a buffer view is not allowed::

  V = VertexBuffer(...)
  Z1 = V[:10] # ok
  V[...] = 1  # ok
  Z2 = Z1[:5] # error


Resizing the buffer
+++++++++++++++++++

Whenever a buffer is resized, all pending operations are cleared and any existing
view on the buffer becomes invalid.



Index Buffer
------------
A IndexBuffer represents indices data that can be uploaded to GPU memory. They
can have a local (CPU) copy or not such that in the former case, the buffer is
read-write while in the latter case, the buffer is write-only.

The shape of an index buffer is always one-dimensional.

The dtype of an index buffer is one of: np.uint8, np.uint16, np.uint32

All GPU operations are deferred and executed just-in time (automatic).

All vertex buffer methods and properties apply.



Program
-------
A program is an object to which shaders can be attached and linked to create
the program. It gives access to attributes and uniform through the
getitem/setitem.


First version (implicit buffer)
+++++++++++++++++++++++++++++++

If a vertex count is given at creation, a unique associated vertex buffer is
created automatically::

  program = Program(vertex, fragment, count=4)
  program['a_color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
  program['a_position'] = [ (-1,-1),   (-1,+1),   (+1,-1),   (+1,+1)   ]



Second version (direct upload)
++++++++++++++++++++++++++++++

If one wants to directly upload data (without intermediary vertex buffer), one
has to explicitly set the direct upload flag at creation::

  program = Program(vertex, fragment, direct=True)
  program['a_color']    = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
  program['a_position'] = [ (-1,-1),   (-1,+1),   (+1,-1),   (+1,+1)   ]


Third version (explicit grouped binding)
++++++++++++++++++++++++++++++++++++++++

It is also possible to create vertex buffer and bind it automatically to the
program, provided buffer field names and attributes match::

  program = Program(vertex, fragment)
  vertices = np.zeros(4, [('a_position', np.float32, 2),
                          ('a_color',    np.float32, 4)])
  program.bind(VertexBuffer(vertices)
  program['a_color'] = [ (1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1) ]
  program['a_position'] = [ (-1,-1),   (-1,+1),   (+1,-1),   (+1,+1)   ]


Fourth version (explicit binding)
+++++++++++++++++++++++++++++++++

Finally, for finer grain control, one can explicitly set each attribute or
uniform individually::

  program = Program(vertex, fragment)
  position = VertexBuffer(np.zeros((4,2), np.float32))
  position[:] = [((-1,-1),), ((-1,+1),), ((+1,-1),), ((+1,+1),)]
  program['a_position'] = position
  color = VertexBuffer(np.zeros((4,4), np.float32))
  color[:] = [((1,0,0,1),), ((0,1,0,1),), ((0,0,1,1),), ((1,1,0,1),)]
  program['a_color'] = color



Texture
-------

Textures represent texture data that can be uploaded to GPU memory. They
can have a local (CPU) copy or not such that in the former case, the texture is
read-write while in the latter case, the texture is write-only.

The (internal) shape of a texture is the size of the class +1:

  * Texture1D -> shape is two-dimensional (width, 1/2/3/4)
  * Texture2D -> shape is three-dimensional (height, width, 1/2/3/4)

|

The (internal) dtype of a texture is one of: ``np.int8``, ``np.uint8``,
``np.int16``, ``np.uint16``, ``np.int32``, ``np.uint32``, ``np.float32``


Creation from existing data
+++++++++++++++++++++++++++

When creating a texture, the GPU format (RGB, RGBA,etc) of the texture is
deduced from the data dtype and shape.

  1 : gl.GL_LUMINANCE

  2 : gl.GL_LUMINANCE_ALPHA

  3 : gl.GL_RGB

  4 : gl.GL_RGBA


Use given data as CPU storage::

  T = Texture2D(data=data, store=True, copy=False)

Use a copy of given data as CPU storage::

  V = Texture2D(data=data, store=True, copy=True)

Do not use CPU storage::

  V = Texture2D(data=data, store=False)



Creation from dtype and size
++++++++++++++++++++++++++++

When creating a texture, the GPU format (RGB, RGBA,etc) of the texture is
deduced from the dtype and the shape:

Create a CPU storage with given size::

  V = Texture2D(dtype=dtype, shape=shape, store=True)

Do not use CPU storage::

  V = Texture2D(dtype=dtype, shape=shape, store=False)



Setting data (setitem)
++++++++++++++++++++++

If texture has CPU storage, any numpy operations is allowed since the operation
is performed on CPU data and modified part are registered for uploading::

  V = Texture2D(...)
  V[:10] = data # ok
  V[::2] = data # ok

If texture has no CPU storage, only numpy operations that affect a contiguous
block of data are allowed. This restriction is necessary because we cannot
upload strided data::

  V = Texture2D(...)
  V[:10] = data # ok
  V[::2] = data # error


Getting data (getitem)
++++++++++++++++++++++

Accessing data from a Texture (base) returns a Texture (view) that is linked to
the base texture. Accessing data from a texture view is not allowed::

  V = Texture2D(...)
  Z1 = V[:10] # ok
  V[...] = 1  # ok
  Z2 = Z1[:5] # error


Resizing the texture
++++++++++++++++++++

Whenever a texture is resized, all pending operations are cleared and any
existing view on the texture becomes invalid.





Beyond this tutorial
====================

There exist a lot of resources on the web related to OpenGL. I only mention
here a few of them that deals with the dynamic rendering pipeline. If you've
found other resources, make sure they deal with the dynamic rendering pipeline
and not the fixed one.

Tutorials / Books
-----------------

**An intro to modern OpenGL** by Joe Groff.

OpenGL has been around a long time, and from reading all the accumulated layers
of documentation out there on the Internet, it's not always clear what parts
are historic and what parts are still useful and supported on modern graphics
hardware. It's about time for a new OpenGL `introduction that <http://duriansoftware.com/joe/An-intro-to-modern-OpenGL.-Table-of-Contents.html>`_ walks through the parts that are still relevant today.

|

**Learning Modern 3D Graphics Programming** by Jason L. McKesson

This `book <http://www.arcsynthesis.org/gltut/>`_ is intended to teach you how
to be a graphics programmer. It is not aimed at any particular graphics field;
it is designed to cover most of the basics of 3D rendering. So if you want to
be a game developer, a CAD program designer, do some computer visualization, or
any number of things, this book can still be an asset for you. This does not
mean that it covers everything there is about 3D graphics. Hardly. It tries to
provide a sound foundation for your further exploration in whatever field of 3D
graphics you are interested in.

|

**An Introduction to OpenGL Programming**

This `introduction
<https://www.youtube.com/watch?v=T8gjVbn8VBk&feature=player_embedded>`_
provides an accelerated introduction to programming OpenGL, emphasizing the
most modern methods for using the library. In recent years, OpenGL has
undergone numerous updates, which have fundamentally changed how programmers
interact with the application programming interface (API) and the skills
required for being an effective OpenGL programmer. The most notable of these
changes, the introduction of shader-based rendering, has expanded to subsume
almost all functionality in OpenGL. This course is presented by Edward Angel of
the University of New Mexico and Dave Shreiner of ARM, Inc..

|

**OpenGL ES 2.0 documentation**

`OpenGL ES 2.0 <https://www.khronos.org/opengles/2_X/>`_ is defined relative to
the OpenGL 2.0 specification and emphasizes a programmable 3D graphics pipeline
with the ability to create shader and program objects and the ability to write
vertex and fragment shaders in the OpenGL ES Shading Language. Vispy is based
on OpenGL ES 2.0 because it give access to the programmable pipeline while
keeping overall complexity tractable.


Vispy documentation
-------------------

The vispy `documentation <http://vispy.readthedocs.org/en/v0.2.1/>`_ is also a
good source of information.


Mailing lists
-------------

There is a `user mailing list
<https://groups.google.com/forum/#!forum/vispy>`_ where you can ask for help on
vispy and a `developers mailing list
<https://groups.google.com/forum/#!forum/vispy-dev>`_ that is more technical.
