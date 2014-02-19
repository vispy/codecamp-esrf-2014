import numpy as np
from pylab import *

n = 50000
x = np.linspace(0.0, 100.0, n)
y = lambda : np.random.randn(n)

figure()
plot(x, y())
show()
