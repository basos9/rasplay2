from luma.core.interface.serial import i2c, spi, pcf8574
from luma.oled.device import ssd1306, ssd1309, ssd1325, ssd1331, sh1106, ws0010
from luma.core.render import canvas
from PIL import Image, ImageDraw, ImageFont
import time
from _maths import RunningAverage
## LCD
## 

class disp_oled():
  pass


class disp_ssd1306(disp_oled):
  def __init__(self, LCD_I2C_PORT=1, LDC_I2C_ADDR=0x3C):
        # rev.1 users set port=0
    # substitute spi(device=0, port=0) below if using that interface
    # substitute bitbang_6800(RS=7, E=8, PINS=[25,24,23,27]) below if using that interface
    serial = i2c(port=LCD_I2C_PORT, address=LDC_I2C_ADDR)

    # substitute ssd1331(...) or sh1106(...) below if using that device
    self.device = ssd1306(serial)
    self.do_renderbuffer = True
    self.renderbuffer = None
    self.inflight = False
    self.skipped = 0
    self.prevSkipped = 0 
    self.renderStats = RunningAverage(60)

      # Load default font.

    self.font = ImageFont.load_default()
    self.xfonts = {
      "l":  ImageFont.load_default(16),
      "ll": ImageFont.load_default(20)
    }

  ## painting
  def lShow(self, strin: str|list, dprint: bool =False, sz: str = ""):
    start = time.process_time() 
    if strin is None:
        strin = ""
    if isinstance(strin, (list, tuple)):
        strin = "\n".join(strin)
    if self.do_renderbuffer :
      if self.renderbuffer == strin:
        return True
      self.renderbuffer = strin
    if self.inflight:
      print ("lShow(): In flight, skipping "+strin)
      prevSkipped = self.prevSkipped
      self.skipped+=1
      self.prevSkipped = self.skipped
      if prevSkipped != self.skipped:
        strin+=f"\nFrames Skipped: {self.skipped}"
      return False
    self.inflight = True
    if (dprint and (strin != "")):
      print("---\n" + strin)
    font = self.font
    if sz and self.xfonts[sz] is not None:
      font = self.xfonts[sz]
    try:
      with canvas(self.device) as draw:
        draw.text((0,0), strin, fill="white", font=font)
    except Exception as e:
        print ("ERROR: LCD draw exception "+str(e))
    elapsed = time.process_time() - start
    self.renderStats.add(elapsed)
    if (elapsed > 0.05):
      print(f"lShow(): Render time {elapsed:.3f} s")
    self.inflight = False
    return True

  def getRenderStats(self):
    return f"~ {self.renderStats.get_avg():.3f}"

  # Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
  # Some other nice fonts to try: http://www.dafont.com/bitmap.php
  # font = ImageFont.truetype('Minecraftia.ttf', 12)
  def lShowL(self, lines, dprint=False):
    if (dprint):
      print("---L: ",lines)
    x = 0
    lineHeight = 12
    y = -2
    i = 0
    with canvas(self.device) as draw:
      for line in lines:
        draw.text((x, y+i*lineHeight), str(line),  font=font, fill=255)
        i=i+1
    