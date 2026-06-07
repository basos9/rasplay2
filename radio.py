

from menu import MenuController
from mpdc import MPDC
from _base import LogicException
from radioCatalog import RadioCatalog, RadioCatalogPresets
from _base import ControllerBase, UnknownEventException


SHOWPLAYER_INSECS = 5

class RadioController(ControllerBase):
    ## memory { "station name": {"url": "stream url", ... }
    ## menudef { "menu name": "display name", submenu: { "menu_name": "display name", ... }... }

    def __init__(self, mpdc: MPDC, screen_lines, eventBus: ControllerBase, radioCatalog: RadioCatalog):
        self.memory = radioCatalog.getDef()
        self.menuController = MenuController(radioCatalog.getMenuDef(), screen_lines)
        self.mpdc = mpdc
        self.eventBus = eventBus
        self.current_screenmode = "menu"
        self.prev_screenmode = ""
        self.showPlayerIn = -1
    
    def setScreenMode(self, mode):
        self.current_screenmode = mode

    ## EVENT handlers
    def onEvent(self, event, *args):
        try:
            return super().onEvent(event, *args)
        except UnknownEventException as e:
            if event == "clock":
                return self.clock(*args)
            elif event == "open":
                return self.selectStation()
            else:
                #print(f"Unknown event: {event}")
                raise e
            

    def onUp(self):
        action = ""
        if self.current_screenmode == "menu" :
            action = "menu NAV up"
            self.setScreenMode("menu")
            self.menuController.menu_up()
            self.selectStation()
        elif self.current_screenmode == "player" :
            action = "vol down"
            self.mpdc.tunevol(1)
        return action
    
    def onDown(self):
        action = ""
        if self.current_screenmode == "menu" :
            action = "menu NAV down"
            self.setScreenMode("menu")
            self.menuController.menu_down()
            self.selectStation()
        elif self.current_screenmode == "player" :
            action = "vol down"
            self.mpdc.tunevol(-1)
        return action

    def onMid(self):
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

    def onLeft(self):
        action=""
        if (self.current_screenmode == "menu"):
            action="menu nav prev"
            if not self.menuController.menu_prev():
                #self.setScreenMode("_back")
                action+=" exit"
                self.close()
            #self.display()
        elif self.current_screenmode == "player" :
             action="player exiting"
             self.close()
        #     self.setScreenMode("menu")
        #     self.showPlayerIn = SHOWPLAYER_INSECS *2
        #     #self.display()
        return action

    def onRight(self):
        action=""
        return action

    def clock(self, diffTime):
        if self.showPlayerIn > 0:
            self.showPlayerIn = self.showPlayerIn - diffTime
            if self.showPlayerIn < 0 and self.current_screenmode == "menu":
                self.setScreenMode("player")
        if not self.isRadioPlaying():
            self.eventBus.onEvent("returnControl")

    def close(self, stop=True):
        print("Closing radio player, stopping MPD, clearing queue")
        if stop:
         self.mpdc.stop()
        self.mpdc.setCtx(None)
        self.mpdc.clearQueue()
        self.eventBus.onEvent("returnControl")

    def selectStation(self, schedPlayer = True):
        sta = self.menuController.get_menu()
        if sta in self.memory:
            print(f"Select station {sta}, SchedDhowPlayer {schedPlayer}")
            ent = self.memory[sta]
            url = ent.get("url")
            name = f"RADIO: {sta}"
            if self.mpdc.isPlaying() and self.mpdc.getCurrent("file") == url and self.mpdc.getCtxF(url).get("slug") == name:
                print(f"Already playing station {name}")
            else:
                print(f"Switching station to {name} from {self.mpdc.getCurrent("file")}")
                self.mpdc.playStream(url)
                ctx = {"slug": name, "station": sta}
                self.mpdc.setCtxF(ctx, url)
            if (schedPlayer):
                self.showPlayerIn = SHOWPLAYER_INSECS
            else:
                self.showPlayerIn = -1
            return True
        return False

    def isRadioPlaying(self):
        if self.mpdc.isPlaying() or self.mpdc.isPaused():
            item = self.mpdc.getCurrent()
            if item is None:
                print("isRadioPlaying could not get current item")
                return False
            #sta = self.menuController.get_menu()
            sta = self.mpdc.getCtx(item).get("station")
            if sta is not None:
                return True
        return False

    #def isExited(self):
    #    return self.current_screenmode == "_back"
    
    # def showCatalog(self):
    #      return ("NOTIMPL")

    def showD(self):
        prevScreen = self.prev_screenmode
        self.prev_screenmode = self.current_screenmode
        dispChanged = self.current_screenmode != prevScreen
        # if self.current_screenmode == "catalog":
        #      return (self.showCatalog(),True)
        if self.current_screenmode == "menu":
            return (self.menuController.show_menu(), True)
        elif self.current_screenmode == "player":
            return (self.mpdc.showStatus(), dispChanged or self.mpdc.statusHasChanged())
        #elif self.current_screenmode == "_back":
        #    return None
        else:
            raise LogicException ('radio: Invalid screenmode.')