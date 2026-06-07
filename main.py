
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
from radioCatalog import RadioCatalogPresets

version = "2.3.0"

## CONFIG
##
## Load runtime configuration from config.py
from config import MPD, TRANS, BUTTONS, SYS, DISP, RADIO

## Init
##

if DISP.type == "ssd1306":
    disp = disp_ssd1306(DISP.screen_lines)
else:
    raise ValueError(f"Unsupported display type {DISP.type}")

mpd = MPDC(MPD.host, MPD.port, MPD.password)
sysInfo = SysInfo(SYS.mntreg)

ctrl = Controller(mpd, disp, sysInfo, version)

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

try:
  tra = TRA(TRANS.host, TRANS.port, TRANS.user, TRANS.password)
  ctrl.setTransmission(tra)
except Exception as e:
   print("Error init transmission "+str(e))

try:
    radioCatalogPresets = RadioCatalogPresets(RADIO.presets)
    ctrl.setRadioCatalog(radioCatalogPresets)
except ValueError as e:
    print(f"Error initializing radio, skipping: {e}")
    radioCatalogPresets = None

mpd.printDebug()
print(sysInfo.showInfo())

if BUTTONS.keymock:
    print("Keymock enabled ...")
    keymock(ctrl)

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

