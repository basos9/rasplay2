from luma.core.interface.serial import i2c, spi, pcf8574
from luma.oled.device import ssd1306, ssd1309, ssd1325, ssd1331, sh1106, ws0010
from luma.core.render import canvas
from PIL import Image, ImageDraw, ImageFont
import time
from _maths import RunningAverage
from functools import reduce

## LCD
## 


SCROLL_PXPSEC = 10 # pixels per second for sliding text
SCROLL_OFFSET_LOOP = 10 # per loop imaginary starting position
SCROLL_OFFSET_START = 20 # imaginary starting position
RENDER_STATS_LOOPS = 60  # number of loops to average render time over
SCROLL_WIDTH_ADJUST = 5 # correct detection for scrolling

class disp_oled():
  pass


class disp_ssd1306(disp_oled):
  def __init__(self, LCD_I2C_PORT=1, LDC_I2C_ADDR=0x3C, fontfile: str =None):
        # rev.1 users set port=0
    # substitute spi(device=0, port=0) below if using that interface
    # substitute bitbang_6800(RS=7, E=8, PINS=[25,24,23,27]) below if using that interface
    serial = i2c(port=LCD_I2C_PORT, address=LDC_I2C_ADDR)

    # substitute ssd1331(...) or sh1106(...) below if using that device
    self.device = ssd1306(serial)
    self.height = self.device.height
    self.width = self.device.width
    self.do_renderbuffer = True
    self.renderbuffer = None
    self.inflight = False
    self.skipped = 0
    self.prevSkipped = 0 
    self.renderStats = RunningAverage(RENDER_STATS_LOOPS)
    self.scroll_states = {}
    self.scroll_stamp = ""
    self.scroll_speed = SCROLL_PXPSEC  # pixels per second for sliding text
    # Load default font.

    loaded = False
    while fontfile and not loaded:
      try:
        self.font = ImageFont.truetype(fontfile, 10)
        self.xfonts = {
          "l":  ImageFont.truetype(fontfile, 16),
          "ll": ImageFont.truetype(fontfile, 20)
        }
        loaded = True
      except Exception as e:
        print(f"Error loading font {fontfile}: {e}")
        if not fontfile.startswith("fonts/"):
          fontfile = "fonts/" + fontfile
          continue
        fontfile = None
  
    if fontfile is None or not fontfile:
      self.font = ImageFont.load_default()
      self.xfonts = {
        "l":  ImageFont.load_default(16),
        "ll": ImageFont.load_default(20)
      }
      fontfile = "default"

    screen_lines = self.getScreenLines()
  
    print(f"disp_ssd1306: Initialized with {screen_lines:1f} lines, size {self.width}x{self.height}, {fontfile} font size {self.font.size}")

  def getScreenLines(self, font=None):
    if font is None:
      font = self.font
    return self.height / self._get_line_height(font)

  def _get_text_width(self, text, font):
    #try:
      #bbox = font.getbbox(text)
      #return bbox[2] - bbox[0]
    return font.getlength(text)
    #except Exception:
    #  return font.getsize(text)[0]

  def _get_line_height(self, font):
    #try:0
      ascent, descent = font.getmetrics()
      return ascent + descent
    #except Exception:
    #  return font.getsize("A")[1]

  def _get_slide_offset(self, line, font, i):
    # get or init state
    state = self.scroll_states.get(i)
    now = time.monotonic()
    leng = len(line)
    if state is None or state.get("length", 0) != len(line):
        width = self._get_text_width(line, font)
        chpx = leng / width if width > 0 else 0
        max_offset = max(self.width/4, width - self.width/7 )
        state = {
                "offset": -SCROLL_OFFSET_START, 
                "last_time": now, 
                "width": width, 
                "length": leng,
                "chpx": chpx,
                "max_offset": max_offset,
                "line": line }
    else:
        chpx = state.get("chpx")
        width = state.get("width")
        max_offset = state.get("max_offset")
    if width < self.width - SCROLL_WIDTH_ADJUST:
        return 0
      # self.scroll_states[i] = state
    elapsed = now - state["last_time"]
    # update state
    state["last_time"] = now
    state["offset"] += self.scroll_speed * elapsed
    # reset offset
    if state["offset"] > max_offset:
      state["offset"] = -SCROLL_OFFSET_LOOP
    self.scroll_states[i] = state
    # last calcs
    offset = state["offset"] if state["offset"] > 0 else 0
    charoff = offset * chpx
    #print(f" slide {i} choff {charoff:1f} tw {width} maxpxoff {max_offset} pxoff {state["offset"]:1f} l {len(line)} chpx {chpx:1f} :{line}")
    # offset in pixels, convert to chars
    return int(charoff)

  def _reset_scroll_states(self, stamp=None):
    if stamp != self.scroll_stamp:
      print("_reset_scroll_states")
      self.scroll_states = {}
      self.scroll_stamp = stamp

  def _slide_lines(self, lines, font, slidelist=None):
    #line_height = self._get_line_height(font) + 1
    olines = list()
    for i, line in enumerate(lines):
      slide = slidelist[i] if slidelist is not None else True
      if not slide:
        #print(f" skip slide {i} :{line}")
        olines.append(line)
        continue
      x = self._get_slide_offset(line, font, i)
      line = line[x:]
      olines.append(line)
    return olines
      #draw.text((x, i * line_height), line, fill="white", font=font)


  ## painting
  def lShow(self, strin: str|list, dprint: bool =False, sz: str = "", slide: bool|list = False, slideStamp = ""):
    start = time.process_time() 
    if strin is None:
        strin = ""
    if isinstance(strin, (list, tuple)):
        lines = [str(x) for x in strin]
        #strin = "\n".join(lines)
    else: # string
        lines = str(strin).splitlines()
        #strin = "\n".join(lines)

    font = self.font
    if sz and self.xfonts[sz] is not None:
      font = self.xfonts[sz]

    slidelist = None
    if isinstance(slide, (list, tuple)):
      slidelist = slide
      slide = reduce(lambda x, y: x or y, slidelist)
      #print(f"lShow(): slide list {slidelist} => {slide}")
    if slide:
      if slideStamp == "":
        slideStamp = lines[0]
      self._reset_scroll_states(slideStamp)
      lines = self._slide_lines(list(lines), font, slidelist)
    else:
      self._reset_scroll_states()

    strin = "\n".join(lines)
    #needs_slide = slide and any(self._get_text_width(line, font) > self.width for line in lines)

    if self.do_renderbuffer :
      if self.renderbuffer == strin:
        return True
      self.renderbuffer = strin

    if self.inflight:
      print ("lShow(): In flight, skipping "+strin)
      prevSkipped = self.prevSkipped
      self.skipped += 1
      self.prevSkipped = self.skipped
      if prevSkipped != self.skipped:
        strin+=f"\nFrames Skipped: {self.skipped}"
      return False
    self.inflight = True
    if (dprint and (strin != "")):
      print("---\n" + strin)
    try:
      with canvas(self.device) as draw:
        self.draw_lines(draw, lines, font)
          #draw.text((0,0), strin, fill="white", font=font)
    except Exception as e:
        print ("ERROR: LCD draw exception "+str(e))
    elapsed = time.process_time() - start
    self.renderStats.add(elapsed)
    if (elapsed > 0.05):
      print(f"lShow(): Render time {elapsed:.3f} s")
    self.inflight = False
    return True

  def draw_lines(self, draw, lines, font):
    line_height = self._get_line_height(font) + 1
    for i, line in enumerate(lines):
      #x = 0
      #if slide:
      #  width = self._get_text_width(line, font)
      #  if width > self.width:
      #    x = -self._get_slide_offset(line, font, i)
      draw.text((0, i * line_height), line, fill="white", font=font)
  

  def getRenderStats(self):
    return f"~ {self.renderStats.get_avg():.3f}"

  ## Probably will delete
  # Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
  # Some other nice fonts to try: http://www.dafont.com/bitmap.php
  # font = ImageFont.truetype('Minecraftia.ttf', 12)
  # def lShowL(self, lines, dprint=False):
  #   if (dprint):
  #     print("---L: ",lines)
  #   x = 0
  #   lineHeight = 12
  #   y = -2
  #   i = 0
  #   font = self.font
  #   with canvas(self.device) as draw:
  #     for line in lines:
  #       draw.text((x, y+i*lineHeight), str(line),  font=font, fill=255)
  #       i=i+1
    
