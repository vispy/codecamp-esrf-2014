import os
import tables as tb
import numpy as np
from glplot import *
from glplot.glwidgetbuffered import *

if not os.path.exists('test.h5'):
    with tb.openFile('test.h5', 'w') as f:
        f.createArray('/', 'data', np.random.randn(100000,1))

with tb.openFile('test.h5', 'r') as f:
    data = f.root.data

    app = QtGui.QApplication(sys.argv)
    glplot = GLPlot(False, 0, GLWidgetBuffered)
    glplot.glWidget.load_data(data, freq=10000.)
    glplot.show()
    sys.exit(app.exec_())
