import numpy as np
from glplot import *

n = 1000000
x = np.linspace(0.0, 100.0, n)
y = lambda : np.random.randn(n)

clear()
figure()
plot(x, y())
show()
