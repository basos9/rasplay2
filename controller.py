
#from symtable import Class
#from time import time
#import threading

import _threads
from _base import LogicException

from menu import MenuController
from _sysinfo import SysInfo
import time

from mpdc import MPDC
from disp import disp_oled
from transstats import TRA
from radio import RadioController
from radioCatalog import RadioCatalog
import config
from _base import ControllerBase, UnknownEventException

# from psutil import cpu_percent
# import psutil



SHUTDOWN_DELAY = 30
MPD_SHOWPAUSEDFORSECS = 100
ERRSHOW_FORSECS = 3
SYSSHOW_FORSECS = 60
SYSDISP_CPU_THRES = 20
SHOWCLOCK_FORSECS = 60
SYSPRINT_EVERYSECS = 10
CP = 0.5 #clock pulse


menudef = {
    "radio": "Radio",
    "player": "Player",
    "stats": "System Stats",
    "transmission": "Transmission",
    "System": { "upnpres": "UPNP Restart",
               "reboot": "Reboot", 
               "shutdown": "Shutdown" },
    "clock": "Clock"
}
#"top": "Top Processes"
screens = {
    "main": "Press SET for menu",
    "menu": "Press Set for menu",
    "stats": "System Stats",
    "top": "Top Processes",
    "player": "Player",
    "radio": "Radio",
    "transmission": "Transmission",
    "shutdown": "",
    "clock": ""
}


class Controller(ControllerBase):
    def __init__(self, mpd: MPDC, disp: disp_oled, sysInfo: SysInfo, version):
        print(f"Controller Init")
        self.screen_lines = disp.getScreenLines()
        self.menuController = MenuController(menudef, self.screen_lines)
        self.mpd = mpd
        self.disp = disp
        self.lShow = disp.lShow
        self.radio = None
        self.version = version
        self.tra = None
        self.sysinfo = sysInfo
        # interval vars
        self.current_screen = "main"
        self.current_screenmode = "main"
        self.prev_screemmode = "main"
        self.current_controller = None
        self.shutDownCount = -1
        self.shutDownCmd = None
        self.wallTimePrev = -1
        self.showPauseFor = -2
        self.showScreenFor = -1
        self.showScreen = None
        self.last_error = None
        self.showErrorFor = -1
        self.blinkTimeDot = 1
        self.showGreetFor = 10
        self.showClockFor = SHOWCLOCK_FORSECS
        self.prev_screen = ""
        self.lastWallPrint = -1

    def fin(self):
        print("Controller shutting down...")
        self.mpd.close()

    def setTransmission(self, tra: TRA):
        if tra is None:
            raise ValueError("Transmission client cannot be None")
        print("Transmission client set for Controller")
        self.tra = tra

    def setRadioCatalog(self, radioCatalog: RadioCatalog):
        if radioCatalog is None:
            raise ValueError("radioCatalog cannot be None")
        print("Radio Controller initialized with radioCatalog")
        self.radio = RadioController(self.mpd, self.screen_lines, self, radioCatalog)

    ## Interupts
    #   if source=Button && Button=Status
    #     showStatusFor = 4
    #   if source=Button && Button=Play
    #     MPD::play_toggle
    #   if source=Button && Button=Left
    #     MPD::prev
    #   if source=Button && Button=Right
    #     MPD::next
    #     

    ## EVENT handlers
    def onEvent(self, event, *args):
        try:
            return super().onEvent(event, *args)
        except UnknownEventException as e:
            if event == "returnControl":
                self.onReturnControl(*args)
            else:
                #print(f"Unknown event: {event}")
                raise e
        
    def onSet(self):
        action=""
        if (self.current_screenmode != "menu"):
            action="open menu"
            self.setScreenMode("menu")
            #self.menuController.menu_reset()
            self.display()
        elif (self.current_screenmode == "menu"):
            action="close menu"
            self.setScreenMode(self.prev_screemmode)
            self.display()
        print(f"EVENT: Btn SET pressed, {action}, on " + self.current_screenmode)
    # def btn_setHeld(self):
    #   if self.current_screenmode == "main" or self.current_screenmode == "menu":
    #     print("EVENT: Btn SET held, toggle sys stats, on "+ self.current_screenmode)
    #     self.schedStatsM()
    #     self.display()
    #   else:
    #     print("EVENT: Btn SET held, on " + self.current_screenmode)

    def onRst(self):
        action=""
        #if (self.current_screenmode == "shutdown"):
        if self.shutDownCount > 0:
            action="cancel shutdown"
            self.cancelShutdownM()
            self.display()
        #elif (self.current_screenmode == "menu"):
        #     print("EVENT: Btn RST presed, close menu, on " + self.current_screenmode)
        #     self.setScreenMode("main")
        #     self.display()
        elif self.current_screenmode == "radio":
            action="exiting radio player"
            self.radio.close()
            #self.setScreenMode("main")
            self.display()
        else:
            action="show main"
            if (self.current_screenmode == "menu"):
                self.menuController.menu_reset()
            self.setScreenMode("main")
            #self.resetMain()
            self.handleMain()
            self.display()
        print(f"EVENT: Btn RST pressed, {action}, on " + self.current_screenmode)

    def onRstHeld(self):
        print(f"EVENT: Btn RST held pressed, init shutdown sequence")
        self.schedShutdownM(self.cmdShutdown)
        self.display()
  
    def onUp(self):
        action=""
        if self.current_screenmode == "menu":
            action="menu nav up"
            self.menuController.menu_up()
            self.display()
        elif self.current_screenmode == "player" or self.current_screenmode == "main":
            action="MPD vol up"
            # self.mpd.onEvent("up")
            self.mpd.tunevol(1)
            if self.current_screenmode == "main":
              self.setScreen("player")
            self.display()
        elif (self.current_screenmode == "radio"):
            #print("EVENT: Btn UP pressed, radio, on " + self.current_screenmode)
            action = self.radio.onEvent("up")
            self.display()
        print(f"EVENT: Btn UP pressed, {action}, on " + self.current_screenmode)

    def onDown(self):
        action=""
        if self.current_screenmode == "menu":
            action="menu NAV down"
            self.menuController.menu_down()
            self.display()
        elif self.current_screenmode == "player" or self.current_screenmode == "main":
            action = "MPD vol down"
            self.mpd.tunevol(-1)
            if self.current_screenmode == "main":
                self.setScreen("player")
            self.display()
        elif (self.current_screenmode == "radio"):
            #print("EVENT: Btn DOWN pressed, radio, on " + self.current_screenmode)
            action = self.radio.onEvent("down")
            self.display()
        print(f"EVENT: Btn DOWN pressed, {action}, on " + self.current_screenmode)

    def onMid(self):
        action=""
        if ("menu" == self.current_screenmode):
            action = "menu NAV "+ self.menuController.get_menu() 
            self.menuNav()
            self.display()
        elif self.current_screenmode == "player" or self.current_screenmode == "main":
            action="MPD play/pause"
            self.mpd.playPause()
            if self.current_screenmode == "main":
                self.setScreen("player")
            self.display()
            # controller()
        elif (self.current_screenmode == "radio"):
            action = self.radio.onEvent("mid")
            self.display()
        print(f"EVENT: Btn MID pressed, {action}, on" + self.current_screenmode)
    
    def onLeft(self):
        if (self.current_screenmode == "menu"):
            action="menu NAV back"
            if not self.menuController.menu_prev():
                self.setScreenMode("main")
            self.display()
        elif self.current_screenmode == "player" or self.current_screenmode == "main":
            action="MPD prev"
            self.mpd.go(-1)
            # controller()
            if self.current_screenmode == "main":
                self.setScreen("player")
            self.display()
        elif self.current_screenmode == "stats" or self.current_screenmode == "transmission":
            action="show main"
            self.setScreenMode("main")
            #self.resetMain()
            self.handleMain()
            self.display()
        elif (self.current_screenmode == "radio"):
            #print("EVENT: Btn MID pressed, radio, on " + self.current_screenmode)
            action = self.radio.onEvent("left")
            self.display()
        print(f"EVENT: Btn LEFT pressed, {action}, on " + self.current_screenmode)

    def onRight(self):
        action=""
        if (self.current_screenmode == "menu"):
            action="menu select"
            #self.menuController.menu_select()
            self.menuNav()
            self.display()
        elif self.current_screenmode == "player" or self.current_screenmode == "main":
            action="MPD next"
            self.mpd.go(1)
            if self.current_screenmode == "main":
                self.setScreen("player")
            self.display()
            # controller()
        elif (self.current_screenmode == "radio"):
            action = self.radio.onEvent("right")
            self.display()
        print(f"EVENT: Btn RIGHT pressed, {action}, on " + self.current_screenmode)

    def onReturnControl(self):
        # did they give us control
        if self.current_screenmode == "radio":
            print(f"onReturnControl on {self.current_screenmode}, going back")
            self.setScreenMode("main")

    def schedShutdownM(self, shutdownCmd ):
        print("Scheduling shutdown in " + str(SHUTDOWN_DELAY) + " seconds...")
        #if self.shutDownCount < 0:
        self.shutDownCount = SHUTDOWN_DELAY
        self.shutDownCmd = shutdownCmd
        self.setScreenMode("shutdown")
    
    def cancelShutdownM(self):
        print("Cancel scheduled shutdown...")
        self.shutDownCount = -1
        self.shutDownCmd = None
        self.setScreenMode("main")
        
    def schedScreenMain(self, screen, showForSecs):
        #if self.showScreenFor < 0:
          print(f"Schedule {screen} display for {showForSecs} seconds...")
          self.showScreenFor = showForSecs
          self.showScreen = screen
          self.setScreen(screen)
        # else:
        #   print("Cancel scheduled system stats display...")
        #   self.showSysFor = -1
        #   self.resetScreen()
  
    def setScreenMode(self, screen):
        print(f"Screen mode change: {self.current_screenmode} -> {screen}")
        screen = self.setScreen(screen)
        self.prev_screemmode = self.current_screenmode
        self.current_screenmode = screen
        if screen == "main":
            self.resetMain()

    def setScreen(self, screen):
        if screen in screens:
            if screen == "transmission" and self.tra is None:
                print("No transmission client set, cannot show transmission stats")
                self.last_error = "* Transmission Unavailable"
                self.current_screen = "main"
            elif screen == "radio" and self.radio is None:
                print("No radio client set, cannot show radio")
                self.last_error = "* Radio Unavailable"
                self.current_screen = "main"
            else:
                self.current_screen = screen
        else:
            raise Exception("Sceen not defined (set) "+ screen)
        return self.current_screen
    
    def resetScreen(self):
        self.current_screen = self.current_screenmode

    def menuNav(self):
      if not self.menuController.menu_select():
          pass
      elif self.menuController.get_menu() == "stats":
          self.setScreenMode("main")
          self.schedScreenMain("stats", SYSSHOW_FORSECS)
      elif self.menuController.get_menu() == "top":
          self.setScreenMode("main")
          self.schedScreenMain("top", SYSSHOW_FORSECS)
      elif self.menuController.get_menu() == "player":
          if self.radio.isRadioPlaying:
                self.radio.close()
          self.setScreenMode("player")
      elif self.menuController.get_menu() == "transmission":
          self.setScreenMode("main")
          self.schedScreenMain("transmission", SYSSHOW_FORSECS)
      elif self.menuController.get_menu() == "reboot":
          self.schedShutdownM(self.cmdReboot)
      elif self.menuController.get_menu() == "shutdown":
          self.schedShutdownM(self.cmdShutdown)
      elif self.menuController.get_menu() == "clock":
          self.setScreenMode("clock")
      elif self.menuController.get_menu() == "upnpres":
          self.setScreenMode("main")
          self.cmdRestartUPNP()
      elif self.menuController.get_menu() == "radio":
          self.setScreenMode("radio")
          self.radio.onEvent("open")
  
    def resetMain(self):
        self.showPauseFor = -2
        self.showScreenFor = -1
        self.showErrorFor = -1
        self.showClockFor = SHOWCLOCK_FORSECS
        self.last_error = None
        self.showGreetFor = -1
        
    def diffTime(self):
        wallTime = time.monotonic()
        #print (f"diffTime() monotime {wallTime}")
        diffTime = 0.00000
        if (self.wallTimePrev > 0):
            diffTime = (wallTime - self.wallTimePrev)
        self.wallTimePrev = wallTime
        return diffTime
    
    def mprint(self, reset1, *args):
        wallTime = time.monotonic()
        if self.lastWallPrint < 0:
            reset1 = True
        if reset1 or (wallTime - self.lastWallPrint >= SYSPRINT_EVERYSECS):
            print(*args)
            self.lastWallPrint = wallTime

    def handleMain(self, diffTime = 0):
          ## trigger error event
            if self.last_error is not None and self.showErrorFor < 0:
                self.showErrorFor = ERRSHOW_FORSECS
                self.mprint(True, f"main: trigger show error for {self.showErrorFor:.0f} secs")
                self.setScreen("main")
            elif self.showErrorFor > 0:
                self.showErrorFor = self.showErrorFor - diffTime
                if self.showErrorFor < 0:
                    self.last_error = None
                    self.showErrorFor = -1
                    self.resetScreen()
                else:
                  self.mprint(False, f"main: show error for {self.showErrorFor:.0f} more secs")
                  self.setScreen("main")
            elif self.showGreetFor > 0:
                self.showGreetFor = self.showGreetFor - diffTime
                self.mprint(self.prev_screen != "main", f"main: show gret for {self.showGreetFor:.0f} more secs")
                #
            elif self.mainScreenFence(diffTime):
                self.setScreen(self.showScreen)
            elif self.radio.isRadioPlaying():
                print(f"main: trigger, show radio player (we returned from a menu maybe)")
                self.setScreenMode("radio")
            elif self.mainPlayerFence(diffTime):
                self.setScreen("player")
            elif self.sysinfo.getAvgCpuPct() > SYSDISP_CPU_THRES :
                print(f"main: trigger, show sys stats cpu avg { self.sysinfo.getAvgCpuPct()}")
                self.setScreen("stats")
            elif self.mainClockFence(diffTime):
                self.setScreen("clock")
            else:
                self.resetScreen()

    def mainScreenFence(self, diffTime):
        if self.showScreenFor > 0:
            self.showScreenFor = self.showScreenFor - diffTime
            if (self.showScreenFor < 0):
                self.showScreenFor = -1
                return False
            else:
                self.mprint(False, f"main: show {self.showScreen} for {self.showScreenFor:.0f} more secs")
                return True
        return False

    def mainPlayerFence(self, diffTime):
        if self.mpd.isPlaying():
            # print(f"main: show player, playing")
            return True
        elif self.mpd.isPaused(False) and self.showPauseFor == -2:
            ## trigger showPausedFor
            self.showPauseFor = MPD_SHOWPAUSEDFORSECS
            self.mprint(self.prev_screen != "player", f"main: trigger, show player, paused for {self.showPauseFor:.0f} secs")
            return True
        elif not self.mpd.isPlaying(False) and self.showPauseFor > 0:
            self.showPauseFor = self.showPauseFor - diffTime
            if self.showPauseFor < 0:
                self.showPauseFor = -1
                return False
            else:
                self.mprint(self.prev_screen != "player",f"main: show player, paused for {self.showPauseFor:.0f} more secs")
                return True
        return False
    
    def mainClockFence(self, diffTime):
        now = time.localtime()
        start = (18, 0)
        end = (23, 0)
        current = (now.tm_hour, now.tm_min)
        inside = start <= current <= end

        if (inside):
            self.showClockFor = -1
            return True
        elif self.showClockFor > 0:
            self.showClockFor = self.showClockFor - diffTime
            if (self.showClockFor < 0):
                self.showClockFor = -1
                return False
            else:
                self.mprint(False, f"main: show clock for {self.showClockFor:.0f} more secs")
                return True
        return False

    def clock(self):
        diffTime= self.diffTime()
        #print(f'Tick passed {diffTime}')
        if (self.shutDownCount > 0):
            self.setScreen("shutdown")
            self.shutDownCount = self.shutDownCount - diffTime
            if self.shutDownCount <= 0:
                try:
                    self.shutDownCmd()
                except Exception as e:
                    self.last_error = "* Error shutting down\n"+ str(e)
        elif self.current_screenmode == "main":
            self.handleMain(diffTime)
        elif self.current_screenmode == "radio":
            #if self.radio.isExited():
            #    self.setScreenMode("main")
            #else:
                self.radio.onEvent("clock", diffTime)
        else:
            self.resetScreen()
        self.display()
        #self.resetScreen()
        
    def th_loop(self):
        while True:
            start = time.monotonic()
            self.clock()
            elapsed = time.monotonic() - start
            sleep = CP - elapsed
            if sleep < 0:
                if sleep<-CP:
                    print(f"th_loop(): *** Missed 2 intervals by {sleep:.3f}, skipping")
                    sleep = CP
                else:
                    print(f"th_loop(): ** Missed an interval by {sleep:.3f}, scheduling now")
                    sleep = 0.001
            elif CP - sleep > 0.1:
                print(f"th_loop() * adjusted sleep time to {sleep:.3f}" )
            time.sleep(sleep)

    def loopStart(self, aasync=False):
        kb_thread = _threads.PropagatingThread(target=self.th_loop, daemon=True)
        self.kb_thread = kb_thread
        print("Controller loop started...")
        kb_thread.start()
        if not aasync:
            kb_thread.join()

    def loopJoin(self, *args):
        return self.kb_thread.join(*args)

    def showMain(self):
        lines = list()
        if self.last_error is not None:
            lines.append(self.last_error)
        if self.showGreetFor > 0:
            lines.append("")
            lines.append("R A S P L A Y")
            lines.append(f" v{self.version}     _")
        return lines
    
    def showClock(self):
        lines = list()
        lines.append("")
        dot = " : " if self.blinkTimeDot else "   "
        lines.append("  "+time.strftime(f"%H{dot}%M", time.localtime() ) )
        self.blinkTimeDot = 0 if self.blinkTimeDot == 1 else 1
        return lines


    def display(self):
        try:
            prevScreen = self.prev_screen
            self.prev_screen = self.current_screen
            dispChanged = self.current_screen != prevScreen
            if self.current_screen == "shutdown":
                self.displayShutdown()
            elif self.current_screen == "main":
                self.lShow( self.showMain(), True )
            elif self.current_screen == "clock":
                self.lShow ( self.showClock(), dispChanged, "ll")
            elif self.current_screen == "menu":
                self.lShow( self.menuController.show_menu(), True)
            elif self.current_screen == "player":
                self.lShow( self.mpd.showStatus(), dispChanged or self.mpd.statusHasChanged() )
            elif self.current_screen == "stats":
                self.lShow(self.sysinfo.showInfo(), dispChanged)
            elif self.current_screen == "top":
                self.lShow(self.sysinfo.showTopProcesses(), dispChanged)
            elif self.current_screen == "transmission":
                self.lShow(self.tra.getStats(), dispChanged)
            elif self.current_screen == "radio":
                self.lShow( *self.radio.showD() )
            else:
                raise LogicException(f'Invalid screen (display {self.current_screen }) '+self.current_screen)
        except LogicException as e:
            raise e
        except Exception as e:
            print(f"Exception (display {self.current_screen }): {str(e)}")
            self.last_error = str(e)

    def displayShutdown(self):
        if self.shutDownCount > 0:
            if self.shutDownCmd == self.cmdReboot:
                self.lShow (f'Rebooting in {abs(self.shutDownCount)}...', True)
            else:
              self.lShow (f'Shutting Down in {abs(self.shutDownCount)}...', True)
        elif self.shutDownCount == 0:
            self.lShow (f'Goodbye...', True)

    # def displayMain(self):
    #     cpu_percent = psutil.cpu_percent(interval=1)
    #     print(f"CPU Usage: {cpu_percent}%")

    def cmdShutdown(self):
        self.lShow(f'Goodbye....')
        self.sysinfo.shutdown()

    def cmdReboot(self):
        self.lShow(f'I\'ll be back...')
        self.sysinfo.reboot() 
        
    def cmdRestartUPNP(self):
        text = self.sysinfo.restartUPNP()
        self.last_error = text
        self.lShow(text, True)

# def draw_menu(draw, state):
#     for i, item in enumerate(menu_items):
#         prefix = ">" if i == state.menu_index else " "
#         draw.text((0, i * 10), f"{prefix} {item}", fill=255)


