import os
import numpy as np
import tables
import tables as tb
import galry.pyplot as plt
from galry import Visual, process_coordinates, get_next_color, get_color
from qtools import inthread

MAXSIZE = 5000
CHANNEL_HEIGHT = .25


class MultiChannelVisual(Visual):
    def initialize(self, x=None, y=None, color=None, point_size=1.0,
            position=None, nprimitives=None, index=None,
            color_array_index=None, channel_height=CHANNEL_HEIGHT,
            options=None, autocolor=None):
            
        position, shape = process_coordinates(x=x, y=y)
        
        # register the size of the data
        self.size = np.prod(shape)
        
        # there is one plot per row
        if not nprimitives:
            nprimitives = shape[0]
            nsamples = shape[1]
        else:
            nsamples = self.size // nprimitives
        
        # register the bounds
        if nsamples <= 1:
            self.bounds = [0, self.size]
        else:
            self.bounds = np.arange(0, self.size + 1, nsamples)
        
        # automatic color with color map
        if autocolor is not None:
            if nprimitives <= 1:
                color = get_next_color(autocolor)
            else:
                color = np.array([get_next_color(i + autocolor) for i in xrange(nprimitives)])
            
        # set position attribute
        self.add_attribute("position0", ndim=2, data=position, autonormalizable=True)
        
        index = np.array(index)
        self.add_index("index", data=index)
    
        if color_array_index is None:
            color_array_index = np.repeat(np.arange(nprimitives), nsamples)
        color_array_index = np.array(color_array_index)
            
        ncolors = color.shape[0]
        ncomponents = color.shape[1]
        color = color.reshape((1, ncolors, ncomponents))
        
        dx = 1. / ncolors
        offset = dx / 2.
        
        self.add_texture('colormap', ncomponents=ncomponents, ndim=1, data=color)
        self.add_attribute('index', ndim=1, vartype='int', data=color_array_index)
        self.add_varying('vindex', vartype='int', ndim=1)
        self.add_uniform('nchannels', vartype='float', ndim=1, data=float(nprimitives))
        self.add_uniform('channel_height', vartype='float', ndim=1, data=channel_height)
        
        self.add_vertex_main("""
        vec2 position = position0;
        position.y = channel_height * position.y + .9 * (2 * index - (nchannels - 1)) / (nchannels - 1);
        vindex = index;
        """)
        
        self.add_fragment_main("""
        float coord = %.5f + vindex * %.5f;
        vec4 color = texture1D(colormap, coord);
        out_color = color;
        """ % (offset, dx))

        # add point size uniform (when it's not specified, there might be some
        # bugs where its value is obtained from other datasets...)
        self.add_uniform("point_size", data=point_size)
        self.add_vertex_main("""gl_PointSize = point_size;""")
        
def get_view(total_size, xlim, freq):
    """Return the slice of the data.
    
    Arguments:
      
      * xlim: (x0, x1) of the window currently displayed.
    
    """
    # Viewport.
    x0, x1 = xlim
    d = x1 - x0
    dmax = duration
    zoom = max(dmax / d, 1)
    view_size = total_size / zoom
    step = int(np.ceil(view_size / MAXSIZE))
    # Extended viewport for data.
    x0ex = np.clip(x0 - 3 * d, 0, dmax)
    x1ex = np.clip(x1 + 3 * d, 0, dmax)
    i0 = np.clip(int(np.round(x0ex * freq)), 0, total_size)
    i1 = np.clip(int(np.round(x1ex * freq)), 0, total_size)
    return (x0ex, x1ex), slice(i0, i1, step)

def get_undersampled_data(data, xlim, slice):
    """
    Arguments:
    
      * data: a HDF5 dataset of size Nsamples x Nchannels.
      * xlim: (x0, x1) of the current data view.
      
    """
    # total_size = data.shape[0]
    # Get the view slice.
    # x0ex, x1ex = xlim
    # x0d, x1d = x0ex / (duration_initial) * 2 - 1, x1ex / (duration_initial) * 2 - 1
    # Extract the samples from the data (HDD access).
    samples = data[slice, :]
    # Convert the data into floating points.
    samples = np.array(samples, dtype=np.float32)
    # Normalize the data.
    samples *= (1. / 32768)
    # samples *= .25
    # Size of the slice.
    nsamples, nchannels = samples.shape
    # Create the data array for the plot visual.
    M = np.empty((nsamples * nchannels, 2))
    samples = samples.T# + np.linspace(-1., 1., nchannels).reshape((-1, 1))
    M[:, 1] = samples.ravel()
    # Generate the x coordinates.
    x = np.arange(slice.start, slice.stop, slice.step) / float(total_size - 1)
    # [0, 1] -> [-1, 2*duration.duration_initial - 1]
    x = x * 2 * duration / duration_initial - 1
    M[:, 0] = np.tile(x, nchannels)
    # Update the bounds.
    bounds = np.arange(nchannels + 1) * nsamples
    size = bounds[-1]
    return M, bounds, size

@inthread
class DataUpdater(object):
    info = {}
    
    def update(self, data, xlimex, slice):
        samples, bounds, size = get_undersampled_data(data, xlimex, slice)
        nsamples = samples.shape[0]
        color_array_index = np.repeat(np.arange(nchannels), nsamples / nchannels)
        self.info = dict(position0=samples, bounds=bounds, size=size,
            index=color_array_index)

def create_trace(nsamples, nchannels):
    noise = np.array(np.random.randn(nsamples, nchannels)*1000,
                     dtype=np.int16)
    t = np.linspace(0., 1., nsamples)
    low = np.array(10000 * np.cos(2*np.pi*5*t), dtype=np.int16)
    return noise + low[:, np.newaxis]

if not os.path.exists('testm.h5'):
    with tb.openFile('testm.h5', 'w') as f:
        a = f.createEArray('/', 'data', tb.Int16Atom(), shape=(0,10),
            chunkshape=(10000, 10))
        for _ in range(10):
            a.append(create_trace(100000, 10))

with tb.openFile('testm.h5', 'r') as f:
    data = f.root.data
            
    nsamples, nchannels = data.shape
    total_size = nsamples
    freq = 10000.
    dt = 1. / freq
    duration = (data.shape[0] - 1) * dt

    duration_initial = 5.

    x = np.tile(np.linspace(0., duration, nsamples // MAXSIZE), (nchannels, 1))
    y = np.zeros_like(x)+ np.linspace(-.9, .9, nchannels).reshape((-1, 1))

    plt.figure(toolbar=False, show_grid=True)
    plt.visual(MultiChannelVisual, x=x, y=y)

    updater = DataUpdater(impatient=True)

    SLICE = None

    def change_channel_height(figure, parameter):
        global CHANNEL_HEIGHT
        CHANNEL_HEIGHT *= (1 + parameter)
        figure.set_data(channel_height=CHANNEL_HEIGHT)

    def pan(figure, parameter):
        figure.process_interaction('Pan', parameter)
        
    def anim(figure, parameter):
        # Constrain the zoom.
        nav = figure.get_processor('navigation')
        nav.constrain_navigation = True
        nav.xmin = -1
        nav.xmax = 2 * duration / duration_initial
        nav.sxmin = 1.
        
        zoom = nav.sx
        box = nav.get_viewbox()
        xlim = ((box[0] + 1) / 2. * (duration_initial), (box[2] + 1) / 2. * (duration_initial))
        xlimex, slice = get_view(data.shape[0], xlim, freq)
        
        # Paging system.
        dur = xlim[1] - xlim[0]
        index = int(np.floor(xlim[0] / dur))
        zoom_index = int(np.round(duration_initial / dur))
        i = (index, zoom_index)
        global SLICE
        if i != SLICE:
            SLICE = i
            updater.update(data, xlimex, slice)
        if updater.info:
            figure.set_data(**updater.info)
            updater.info.clear()
        
    plt.animate(anim, dt=.01)
    plt.action('Wheel', change_channel_height, key_modifier='Control',
               param_getter=lambda p: p['wheel'] * .001)
    plt.action('Wheel', pan, key_modifier='Shift',
               param_getter=lambda p: (p['wheel'] * .002, 0))
    plt.action('DoubleClick', 'ResetZoom')

    plt.xlim(0., duration_initial)

    plt.show()
    # f.close()
