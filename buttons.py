## 
## BUTTON

from gpiozero import Button

#BTN_BOUNCE_TIME = 0.01
#BTN_HOLD_TIME = 2
#RST_HOLD_TIME = 5

class buttonsCtrl():

    def __init__(self, state, bUp, bDown, bLeft, bRight, bMid, bSet, bRst, debounce = None):
        #if bSet:
        self.state = state
        self.btn_set = Button(bSet, pull_up=True, bounce_time=debounce   )
        self.btn_set.when_pressed = lambda: state.onEvent("set")
        #self.btn_set.when_held = lambda: state.btn_setHeld()
        #if bRst:
        self.btn_rst = Button(bRst, pull_up=True, bounce_time=debounce   )
        self.btn_rst.when_pressed = lambda: state.onEvent("rst")
        #self.btn_rst.when_held = lambda: state.btn_rstHeld()
    #if bUp:
        self.btn_up = Button(bUp, pull_up=True)
        self.btn_up.when_pressed = lambda: state.onEvent("up")
    #if bDown:
        self.btn_down = Button(bDown, pull_up=True, bounce_time=debounce   )
        self.btn_down.when_pressed = lambda: state.onEvent("down")
    #if bRight:
        self.btn_right = Button(bRight, pull_up=True, bounce_time=debounce   )
        self.btn_right.when_pressed = lambda: state.onEvent("right")
    #if bLeft:
        self.btn_left = Button(bLeft, pull_up=True)
        self.btn_left.when_pressed = lambda: state.onEvent("left")
    #if bMid:
        self.btn_mid = Button(bMid, pull_up=True, bounce_time=debounce   )
        self.btn_mid.when_pressed = lambda: state.onEvent("mid")


   