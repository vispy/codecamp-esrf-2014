KEY_UP = "up"
KEY_DOWN = "down"
KEY_LEFT = "left"
KEY_RIGHT = "right"

KEY_CTRL = "ctrl"
KEY_ALT = "alt"
KEY_SHIFT = "shift"

class NavigationInterface(object):

    # 0 = no mouse button, 1 = left, 2 = right
    mouseButton = 0
    mousePressX, mousePressY = 0, 0
    
    wheelCoefficient = .001
    keyboardCoefficient = .12
    
    keyButtonPressed = ""
    
    def __init__(self, navigation):
        # pass a navigation object
        self.nav = navigation

    def mousePress(self, x, y, button=1):
        """
        Mouse coordinates: x, y \in [0,1]
        button: 1 = left, 2 = right
        """
        self.mouseButton = button
        self.mousePressX, self.mousePressY = x, y
        self.x, self.y = x, y
        
    def mouseRelease(self):
        self.mouseButton = 0
        
    def mouseMove(self, x, y):
        if self.mouseButton:
            # compute x,y displacement since last call
            dx, dy = x - self.x, y - self.y
            self.x, self.y = x, y
        if self.mouseButton == 1:
            if self.keyButtonPressed != KEY_SHIFT:
                self.nav.translate_x(dx)
            if self.keyButtonPressed != KEY_CTRL:
                self.nav.translate_y(dy)
        if self.mouseButton == 2:
            if self.keyButtonPressed != KEY_SHIFT:
                self.nav.scale_x(dx, self.mousePressX)
            if self.keyButtonPressed != KEY_CTRL:
                self.nav.scale_y(dy, self.mousePressY)
            
    def mouseWheel(self, step):
        step *= self.wheelCoefficient
        if self.keyButtonPressed == KEY_CTRL:
            self.nav.scale_x(step)
        elif self.keyButtonPressed == KEY_SHIFT:
            self.nav.scale_y(-step)
        elif self.keyButtonPressed == KEY_ALT:
            self.nav.translate_y(step)
        else:
            self.nav.translate_x(step)
            
    def keyPress(self, key):
        self.keyButtonPressed = key
        if key == KEY_LEFT:
            self.nav.translate_x(self.keyboardCoefficient)
        if key == KEY_RIGHT:
            self.nav.translate_x(-self.keyboardCoefficient)
        if key == KEY_UP:
            self.nav.translate_y(self.keyboardCoefficient)
        if key == KEY_DOWN:
            self.nav.translate_y(-self.keyboardCoefficient)
        
    def keyRelease(self):
        self.keyButtonPressed = ""
        
