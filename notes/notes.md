Tasks
-----

### Core Vispy

* Review Nicolas' gloo changes
* Update gloo to avoid using the output of glGetUniforms in a loop (**need for WebGL**)
* Review Luke's shader composition system
* Visuals & scene graph
  * Review Luke and Almar's prototype code.
  * Implement examples with Luke's code
    * pannable & zoomable 2D plot
    * ...
  * Discuss how to integrate automated collections into all this
  * Refine the API ...
* Mechanism to use non ES-2.0 features (Exception if extension used is not available)
* WebGL
  * Implement online backend (or prototype)
  * test whether the scene graph pan & zoom example can accept a custom Python
    object instead of actual numbers for mouse position
* Discuss Almar's own OpenGL wrapper
* Tackle Github issues


### Examples/demos (gloo)
    
* 2D image, GPU-based color map, axes (AS?)
* Write CLBuffer & interop with OpenGL (at least interop API in gloo): JK?
* Implement demos/prototypes directly with gloo (and put them in the gallery)
* Implement some visuals (lines, shapes, meshes, graphs...)
* Ray traced sphere/cylinder in sprite in GLSL (molecules)
* Real-time high-perf rotating scope: static & dynamic buffers, x computed in GLSL
* ND viewer with arbitrary projections (ND data in texture)

### No need for OpenGL
    
* Implement trackball
* Code to compare images (unit tests)
* Script to bundle Vispy in a Debian package
* C/Cython code for specific geometric algorithms
* FPS counter
* Clean up the wiki
* Put the modern OpenGL tutorial online


