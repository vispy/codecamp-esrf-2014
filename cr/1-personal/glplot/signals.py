
from PyQt4 import QtCore

class Signals(QtCore.QObject):
        navigateSignal = QtCore.pyqtSignal()
        windowCloseSignal = QtCore.pyqtSignal(int)
SIGNALS = Signals()

