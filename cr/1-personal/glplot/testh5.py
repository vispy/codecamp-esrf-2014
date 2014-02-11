import numpy as np
from glplotwin import *
from glwidgetbuffered import GLWidgetBuffered
from h5 import *

# freq = 20000
# data = randn(freq*60,10)

freq = None
data = load_hdf5("test.h5")

# app = QtGui.QApplication(sys.argv)
glplot = GLPlot(False, 0, GLWidgetBuffered)
glplot.glWidget.load_data(data, freq=freq)
glplot.show()
# sys.exit(app.exec_())

