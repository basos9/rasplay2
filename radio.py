
from menu import MenuController
from mpdc import MPDC
from _threads import LogicException
from radioCatalog import RadioCatalog, PresetsRadioCatalog


# eventDef = (
#     "down",
#     "up",
# )

SHOWPLAYER_INSECS = 5

class Radio():
    def __init__(self, mpdc: MPDC, screen_lines, onReturnControl, radioCatalog: RadioCatalog):
        self.memory = radioCatalog.getDef()
        self.menuController = MenuController(radioCatalog.getMenuDef(), screen_lines)
        self.mpd = mpdc
        self.onReturnControl = onReturnControl
        self.current_screenmode = "menu"
        self.prev_screenmode = ""
        self.showPlayerIn = -1
    
    def setScreenMode(self, mode):
        self.current_screenmode = mode

    def onEvent(self, event, *args):
        if event == "down":
            return self.btnDown()
        elif event == "up":
            return self.btnUp()
        elif event == "mid":
            return self.btnMid()
        elif event == "left":
            return self.btnLeft()
        elif event == "right":
            return self.btnRight()
        elif event == "clock":
            return self.clock(*args)
        elif event == "open":
            return self.selectStation()
    
    def btnUp(self):
        action = ""
        if self.current_screenmode == "menu" :
            action = "menu NAV up"
            self.setScreenMode("menu")
            self.menuController.menu_up()
            self.selectStation()
        elif self.current_screenmode == "player" :
            action = "vol down"
            self.mpd.tunevol(1)
        return action
    
    def btnDown(self):
        action = ""
        if self.current_screenmode == "menu" :
            action = "menu NAV down"
            self.setScreenMode("menu")
            self.menuController.menu_down()
            self.selectStation()
        elif self.current_screenmode == "player" :
            action = "vol down"
            self.mpd.tunevol(-1)
        return action

    def btnMid(self):
        action=""
        if self.current_screenmode == "menu":
            action = "menu NAV select"
            if not self.menuController.menu_select():
                pass
            #elif self.menuController.get_menu() == "catalog":
            #    self.setScreenMode("catalog")
            elif self.selectStation(False):
                self.setScreenMode("player")
        elif self.current_screenmode == "player":
            action="menu open"
            self.setScreenMode("menu")
            self.showPlayerIn = SHOWPLAYER_INSECS *2
        return action

    def btnLeft(self):
        action=""
        if (self.current_screenmode == "menu"):
            action="menu nav prev"
            if not self.menuController.menu_prev():
                #self.setScreenMode("_back")
                action+=" exit"
                self.mpd.stop()
                self.onReturnControl()
            #self.display()
        elif self.current_screenmode == "player" :
             action="player exiting"
             self.mpd.stop()
             self.onReturnControl()
        #     self.setScreenMode("menu")
        #     self.showPlayerIn = SHOWPLAYER_INSECS *2
        #     #self.display()
        return action

    def btnRight(self):
        action=""
        return action

    def clock(self, diffTime):
        if self.showPlayerIn > 0:
            self.showPlayerIn = self.showPlayerIn - diffTime
            if self.showPlayerIn < 0 and self.current_screenmode == "menu":
                self.setScreenMode("player")
        if not self.isRadioPlaying():
            self.onReturnControl()

    def selectStation(self, schedPlayer = True):
        sta = self.menuController.get_menu()
        if sta in self.memory:
            print(f"Select station {sta}, SchedDhowPlayer {schedPlayer}")
            url = self.memory[sta]
            name = f"RADIO: {sta}"
            if self.mpd.isPlaying() and self.mpd.getCurrent("file") == url and self.mpd.getCtxF(url).get("slug") == name:
                print(f"Already playing station {name}")
            else:
                print(f"Switching station to {name} from {self.mpd.getCurrent("file")}")
                self.mpd.playStream(url)
                ctx = {"slug": name, "station": sta}
                self.mpd.setCtxF(ctx, url)
            if (schedPlayer):
                self.showPlayerIn = SHOWPLAYER_INSECS
            else:
                self.showPlayerIn = -1
            return True
        return False

    def isRadioPlaying(self):
        if self.mpd.isPlaying() or self.mpd.isPaused():
            item = self.mpd.getCurrent()
            if item is None:
                print("isRadioPlaying could not get current item")
                return False
            #sta = self.menuController.get_menu()
            sta = self.mpd.getCtx(item).get("station")
            if sta is not None:
                return True
        return False

    #def isExited(self):
    #    return self.current_screenmode == "_back"
    
    def showCatalog(self):
         return ("NOTIMPL")

    def showD(self):
        prevScreen = self.prev_screenmode
        self.prev_screenmode = self.current_screenmode
        dispChanged = self.current_screenmode != prevScreen
        if self.current_screenmode == "catalog":
             return (self.showCatalog(),True)
        elif self.current_screenmode == "menu":
            return (self.menuController.show_menu(), True)
        elif self.current_screenmode == "player":
            return (self.mpd.showStatus(), dispChanged or self.mpd.statusHasChanged())
        #elif self.current_screenmode == "_back":
        #    return None
        else:
            raise LogicException ('radio: Invalid screenmode.')