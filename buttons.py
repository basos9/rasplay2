## 
## BUTTON

from gpiozero import Button


#BTN_BOUNCE_TIME = 0.01
#BTN_HOLD_TIME = 2
#RST_HOLD_TIME = 5

class buttonsCtrl():

    def __init__(self, state, bUp, bDown, bLeft, bRight, bMid, bSet, bRst):
        #if bSet:
        self.state = state
        self.btn_set = Button(bSet, pull_up=True)
        self.btn_set.when_pressed = lambda: state.btn_set()
        #self.btn_set.when_held = lambda: state.btn_setHeld()
        #if bRst:
        self.btn_rst = Button(bRst, pull_up=True)
        self.btn_rst.when_pressed = lambda: state.btn_rst()
        #self.btn_rst.when_held = lambda: state.btn_rstHeld()
    #if bUp:
        self.btn_up = Button(bUp, pull_up=True)
        self.btn_up.when_pressed = lambda: state.btn_up()
    #if bDown:
        self.btn_down = Button(bDown, pull_up=True)
        self.btn_down.when_pressed = lambda: state.btn_down()
    #if bRight:
        self.btn_right = Button(bRight, pull_up=True)
        self.btn_right.when_pressed = lambda: state.btn_right()
    #if bLeft:
        self.btn_left = Button(bLeft, pull_up=True)
        self.btn_left.when_pressed = lambda: state.btn_left()
    #if bMid:
        self.btn_mid = Button(bMid, pull_up=True)
        self.btn_mid.when_pressed = lambda: state.btn_mid()


   