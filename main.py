
#from mpd_control.mpd_control import MPDController
#from mpd_control import MPDController
# req python-mpd2

#import time

from mpdc import MPDC
from transstats import TRA
from _sysinfo import SysInfo
from disp import disp_ssd1306
from buttons import buttonsCtrl
from controller import Controller
from _keymock import keymock

version = "2.3.0"

## CONFIG
##
## Load runtime configuration from config.py
from config import MPD, TRANS, BUTTONS, SYS

## Init
##

disp = disp_ssd1306()
mpd = MPDC(MPD.host, MPD.port, MPD.password)
sysInfo = SysInfo(SYS.mntreg)

ctrl = Controller(mpd, disp, sysInfo, version)

try:
  tra = TRA(TRANS.host, TRANS.port, TRANS.user, TRANS.password)
  ctrl.setTransmission(tra)
except Exception as e:
   print("Error init transmission "+str(e))

bat = buttonsCtrl(
  ctrl,
  bUp=BUTTONS.up,
  bDown=BUTTONS.down,
  bLeft=BUTTONS.left,
  bRight=BUTTONS.right,
  bMid=BUTTONS.mid,
  bSet=BUTTONS.btn_set,
  bRst=BUTTONS.rst,
)


mpd.printDebug()
print(sysInfo.showInfo())

kKM = keymock(ctrl)

##
## PROGRAME
ctrl.loopStart()

try:
  print("MPD + GPIO control ready...")
  # while True:
  #   ctrl.clock()
  #   ctrl.sleep()

except KeyboardInterrupt:
    ctrl.fin()
    print("Exiting.")

