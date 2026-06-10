from mpd import MPDClient
import copy

SHOW_VOLUME_LOOPS = 5
MPD_VOLSTEP = 5

class MPDC:
  def __init__(self, HOST, PORT, PASSWORD=""):
    print(f"MPDC: init {HOST}:{PORT}")
    self.mpd = MPDClient()
    self.HOST = HOST
    self.PORT = PORT
    self.PASSWORD = PASSWORD
    self.status = None
    self.currentCtx = {}
    self.prevStatus = {}
    self.showVolumeForLoops = -1
    self.prevPrintState = ""
    self.printState = ""
    try:
      self.connect()
    except Exception as e:
      print("Error connecting to MPD: "+str(e))
    self.blinkPause = 0 

  def connect(self):
    self.mpd.connect(self.HOST, self.PORT)
    if (self.PASSWORD != "" ):
      self.mpd.password(self.PASSWORD)

  def reconn(self):
    try:
      self.mpd.ping()
    except Exception as e:
      print("Reconnecting: MPD not responding: "+str(e))
      try:
        self.close()
        self.connect()
        return True
      except Exception as e:
        print("Error reconnecting to MPD: "+str(e))
        return False
    return True

  def getStatus(self, getStatus=True):
    try:
      if getStatus or self.status is None:
        self.status = self.mpd.status()
      if self.status is None:
        return {}
      return self.status
    except Exception as e:
      print("Error getting MPD status: "+str(e))
      self.reconn()
      return {}

  def getState(self, getStatus=True):
    return self.getStatus(getStatus).get("state")

  def isPlaying(self,getStatus=True):
    return self.getState(getStatus) == "play"

  def isPaused(self,getStatus=True):
    return self.getState(getStatus) == "pause"
  
  def setCtxF(self, ctx, file: str):
    items = self.mpd.playlistfind("file", file)
    if len(items) > 0:
      item = items[0]
      self.setCtx(ctx, item)

  def setCtx(self, ctx, item: dict =None):
    if item is None:
       item = self.mpd.currentsong()
    id = item.get("id")
    if id is None:
      print ("MPDC: setctx by item.  Could not find currentsong's id")
      return
    print(f"MPDC: setCtx setting ctx for item {id} {ctx}")
    if ctx is not None:
      ctx["id"] = id
    self.currentCtx = ctx

  def getCtxF(self, file:str):
    items = self.mpd.playlistfind("file", file)
    if len(items) > 0:
      item = items[0]
    else:
      return {}
    return self.getCtx(item)

  def getCtx(self, item=None):
    if item is None:
      item = self.mpd.currentsong()
    if item is None:
      print("MPDC: getCtx could not get currentsong")
      return {}
    id = item.get("id")
    if id is None:
      print ("MPDC: getCtx Could not find currentsong's id")
      return {}
    ctx = self.currentCtx
    if ctx.get("id") == id:
     return ctx
    #else:
    #  print(f"MPDC: getctx not context for id {id}")
    return {}

  def playStream(self, url, addToQueue=False):
    try:
      print(f"MPDC: Playstream: playing {url}, with add {addToQueue}")
      if not addToQueue:
        self.mpd.clear()
      self.mpd.add(url)
      self.mpd.play()
      if self.isPaused():
        self.mpd.pause(0)
    except Exception as e:
      print("Error playing stream: "+str(e))
      self.reconn()

  # def isStopped(self, getStatus=True):
  #   return self.getState(getStatus) == "stopped"

  #def getVolume(self, getStatus=True):
  #  return int(self.getStatus(getStatus).get("volume",-1))

  def playPause(self):
    try:
      if self.isPlaying(True):
          self.mpd.pause(1)
      elif self.isPaused(True):
          self.mpd.pause(0)
          self.blinkPause = 0
      else:
          self.mpd.play()
    except Exception as e:
      print("Error toggling play/pause: "+str(e))
      self.reconn()

  def stop(self):
    try:
      self.mpd.stop()
    except Exception as e:
      print("Error stopping MPD: "+str(e))
      self.reconn()

  def clearQueue(self):
    try:
      self.mpd.clear()
    except Exception as e:
      print("Error clearing MPD queue: "+str(e))
      self.reconn()

  def go(self,i):
    try:
      if i == 1:
          self.mpd.next()
      elif i == -1:
          self.mpd.previous()
    except Exception as e:
      print("Error going to next/previous: "+str(e))
      self.reconn()

  def tunevol(self, diff=1):
    if (diff == 1):
      diff = MPD_VOLSTEP
    elif diff == -1:
      diff = -MPD_VOLSTEP
    diff = max(-100, min(100, diff))
    try:
      self.mpd.volume(diff)
    except Exception as e:
      print("Error changing volume: "+str(e))
      self.reconn()
        
  def fmtSecs(secs, none=""):
    if secs is None:
      return none
    secs = float(secs)
    min, sec = divmod(secs, 60)
    hour, min = divmod(min, 60)
    if (hour > 0):
        return '%d:%02d:%02d' % (hour, min, sec)
    else:
        return '%d:%02d' % (min, sec);

  def paintPct(pct: float, maxchars: int, char: str="-", delim=""):
    nchar = int(float(pct)/100*maxchars)
    return delim + char * nchar + " " * (maxchars - nchar) + delim

# mpc playlist -f '%name% -  %artist% -  %title% - %file%'
#  -  Walkabouts, The -  The Light Will Stay On - https:///Audio/73457/stream.mp3?static=true&dlnaheaders=true&api_key=a2ba92eedc8d4e429bdf09b3e1522cb8
#  -  Purple Overdose -  Blue Torture - https:///Audio/50461/stream.mp3?static=true&dlnaheaders=true&api_key=a2ba92eedc8d4e429bdf09b3e1522cb8
#  -  Pink Floyd -  Astronomy Domine - https://Audio/44438/stream.flac?static=true&dlnaheaders=true&api_key=a2ba92eedc8d4e429bdf09b3e1522cb8

    ## status
    #{'volume': '36', 'repeat': '0', 'random': '0', 'single': '0', 'consume': '0', 'partition': 'default', 'playlist': '1949', 'playlistlength': '3', 'mixrampdb': '0', 'state': 'play', 'lastloadedplaylist': '', 'song': '1', 'songid': '271', 'time': '206:457', 'elapsed': '205.876', 'bitrate': '1009', 'duration': '457.160', 'audio': '44100:16:2', 'nextsong': '2', 'nextsongid': '272'}
    # song
    #{'file': 'https:///Audio/45985/stream.flac?static=true&dlnaheaders=true&api_key=a2ba92eedc8d4e429bdf09b3e1522cb8', 'artist': 'Kyuss', 'title': 'Freedom Run', 'album': 'Blues for the Red Sun', 'date': '1992', 'track': '8', 'albumartist': 'Kyuss', 'disc': '1', 'pos': '1', 'id': '271'}
    #   - showMpdPlayStatus: Title Artist Album Year

    ## streaming online
#     MPD: {'volume': '29', 'repeat': '0', 'random': '0', 'single': '0', 'consume': '0', 'partition': 'default', 'playlist': '35', 'playlistlength': '
# 1', 'mixrampdb': '0', 'state': 'play', 'lastloadedplaylist': '', 'song': '0', 'songid': '14', 'time': '331:0', 'elapsed': '330.768', 'bitrate': 
# '128', 'audio': '44100:24:2'} 
# {'file': 'https://stream.radiojar.com/w47v0ekgzp5tv?1778684494=', 'title': 'Grey Gallows - 1982', 'name': 'w47v0ekgzp5tv', 'pos': '0', 'id': '14
# '}   
  def showStatus(self):
    try:
      prevStatus = self.prevStatus
      status = self.getStatus(True)
      self.prevStatus = copy.deepcopy(status)
      current = self.mpd.currentsong()
      #print("MPD: "+str(status)+"\n"+str(current))
      #out = f'{current["title"]}\n{current["artist"]}'

    except Exception as e:
      print("Error getting MPD status: "+str(e))
      self.reconn()
      return ("-","-","MPD Error")

    btr = f'{status.get("bitrate","-")}k'
    pm=("PAUSE",
        "P    ",
        " A   ",
        "  U  ",
        "   S ",
        "    E")
    statep=""
    vline= ""
    slug=""
    vstat=""
    if status.get("state",None) == "pause":
      statep = pm[self.blinkPause] + " "
      self.blinkPause = (self.blinkPause + 1) if self.blinkPause < len(pm)-1 else 0
    elif status.get("state",None) != "play":
      statep = "stopped"
    if statep != "stopped":
      #print("State: "+status.get("volume","-")+"% "+status.get("state","-")+", prev: "+str(prevStatus.get("volume","-")))
      if str(status.get("volume")) != str(prevStatus.get("volume")):
        print("Volume changed: "+status.get("volume","-") + " from " + prevStatus.get("volume","-"))
        self.showVolumeForLoops = SHOW_VOLUME_LOOPS+1
      slug = self.getCtx(current).get("slug")
    if self.showVolumeForLoops > 0:
      self.showVolumeForLoops -= 1
      vstat = "Vol: " + str(status.get("volume")) + "% "
      SCREEN_WIDTH=40
      vline = MPDC.paintPct(status.get("volume"),SCREEN_WIDTH, "-" , "|")
    duration = MPDC.fmtSecs(status.get("duration",None))
    timedel=""
    if duration != "":
      timedel = " - "
  
    self.prevPrintState = self.printState
    self.printState = f"{vline}{slug}"
    time = f'{statep}{MPDC.fmtSecs(status.get("elapsed",None),":")}{timedel}{duration}'
    sitems = [time,btr]
    if (vstat):
      sitems.insert(0,vstat)
    sline = " | ".join(sitems)
    ret = [current.get("title","-"), current.get("artist","-") ,sline, vline]
    if slug:
      ret.insert(0,slug)
    return ret

  def statusHasChanged(self):
    printChanged = self.printState != self.prevPrintState
    return printChanged or self.getStatus().get("state") != self.prevStatus.get("state")

  def getCurrent(self, tag=None):
    current = self.mpd.currentsong()
    if tag is not None:
      return current.get(tag)
    return current

  def printDebug(self):
      status = self.getStatus(True)
      current = self.mpd.currentsong()
      playlist = self.mpd.playlistid()
      print("MPD: "+str(status)+"\n CUR:"+str(current))
      print(" PLI:"+str(playlist))
      #print("TAG "+str(self.mpd.tagtypes()))
      print(self.mpd.playlistfind("file","willnotfind"))


  def close(self):
    self.mpd.close()
