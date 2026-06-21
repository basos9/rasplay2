import subprocess
import psutil
import copy
import time
import threading
from _maths import RunningAverage
import board
import adafruit_dht
MNTREG = '^/'
MAVG_SIZELOOPS = 20
TRACKSLEEP = 5

class sysCmdInfo():

  def calcUptimeUsersLoad(self):
    cmd = """w | head -1 | awk -F ',' '{gsub(/.*up /,"",$1); gsub(/^ *| users/,"",$3); gsub(/^.*: /,"",$4); gsub(/ /,"",$5); printf "%s\\n\\n%s\\n%s\\n%s",$1, $3, $4, $5}'"""
    UPnLOAD = subprocess.check_output(cmd, shell = True, text=True )
    lines = UPnLOAD.splitlines()
    print(lines)
    self.uptime = lines[0]
    self.users = lines[1]
    self.load1 = lines[2]
    self.load5 = lines[3]

  def getUptime(self):
    return self.uptime
  
  def getUsers(self):
    return self.users
  
  def getLoad(self):
    return self.load1 + " ~ " + self.load5
  
  def getHostname(self):
    cmd = "hostname -I"
    IP = subprocess.check_output(cmd, shell = True, text=True )
    return IP

  def getCurCpuPCt():
      cmd = """top -bn1 | awk -F ',' '/%Cpu/{gsub(/^ | id/,"",$4); printf "%d", 100-$4}'"""
      CPU = subprocess.check_output(cmd, shell = True, text =True)
      return float(CPU)
  
  def getMemUsage():
    cmd = """free -m | awk 'NR==2{printf "%.2f%% %s/%sMB", $3*100/$2, $3,$2 }'"""
    MemUsage = subprocess.check_output(cmd, shell = True, text = True )
    return MemUsage
     
  def getDiskUsage(mntreg):
    cmd = """df -h | awk '$NF~"("""+mntreg+""")$"{gsub(/\\/media\\//,"",$6); printf "%s: %s ", $6,$5}'"""
    Disk = subprocess.check_output(cmd, shell = True, text = True )
    return Disk
  
  def getCpuTemp():
    cmd = """vcgencmd measure_temp | awk '{gsub(/temp=/,""); printf "%s",$0;}'"""
    Temp = subprocess.check_output(cmd, shell = True, text=True )
    return Temp
  
  def shutdown():
      print ("Shutting down")
      subprocess.check_output("sleep 2", shell = True, text=True )
      subprocess.check_output("sudo -n poweroff", shell = True, text=True )

  def reboot():
      print ("Rebooting")
      subprocess.check_output("sleep 2", shell = True, text=True )
      subprocess.check_output("sudo -n reboot", shell = True, text=True )
  
  def restartUPNP():
     print ("Restart upmpdcli")
     return subprocess.check_output("sudo -n systemctl restart upmpdcli", shell= True, text = True)

class sysPyInfo():
  def __init__(self):
    self.avgcpu = RunningAverage(MAVG_SIZELOOPS)
    self.avgnet_rcv = RunningAverage(MAVG_SIZELOOPS)
    self.avgnet_snd = RunningAverage(MAVG_SIZELOOPS)
    self.avgdisk_read = RunningAverage(MAVG_SIZELOOPS)
    self.avgdisk_write = RunningAverage(MAVG_SIZELOOPS)
    self.prevNetStats = {}
    self.prevDiskStats = None
    self.prevTime = 0

  def getCurCpuPCt():
     cpu_percent = psutil.cpu_percent(interval=1)
     return cpu_percent
  
  def getLoad3():
     return psutil.getloadavg()
  
  def  getLoad():
    la = psutil.getloadavg()
    return f"{la[0]:.1f} ~ {la[1]:.1f}"
  
  def getMemUsage():
    mem = psutil.virtual_memory()
    used_mb = mem.used / (1024 * 1024 * 1024)
    total_mb = mem.total / (1024 * 1024 * 1024)
    return f"{mem.percent:.0f}% {used_mb:.1f}G"

  def getNUsers():
     u = psutil.users()
     return f"{len(u):.0f}u"
     
  def getUptimeSecs():
     b = psutil.boot_time()
     e = time.time()
     return e - b

  def getUptime():
     s = sysPyInfo.getUptimeSecs()
     s = s / 3600
     d = s / 24
     h = s % 24
     return f"{d:.0f}d:{h:.0f}h"

  def track(self, diffTime):
    self.avgcpu.add(sysPyInfo.getCurCpuPCt())
    prevNetStats = self.prevNetStats
    netstatis = psutil.net_io_counters()
    self.prevNetStats = copy.deepcopy(netstatis)
    if diffTime > 0 and prevNetStats.bytes_recv is not None and prevNetStats.bytes_sent is not None :
      self.avgnet_rcv.add((netstatis.bytes_recv - prevNetStats.bytes_recv) / (1024 *1024 ) / diffTime)
      self.avgnet_snd.add((netstatis.bytes_sent - prevNetStats.bytes_sent)/ (1024* 1024 ) / diffTime)

    prevDiskStats = self.prevDiskStats
    diskstats = psutil.disk_io_counters()
    self.prevDiskStats = copy.deepcopy(diskstats)
    if diffTime > 0 and prevDiskStats is not None:
      self.avgdisk_read.add((diskstats.read_bytes - prevDiskStats.read_bytes) / (1024 * 1024) / diffTime)
      self.avgdisk_write.add((diskstats.write_bytes - prevDiskStats.write_bytes) / (1024 * 1024) / diffTime)

  def getAvgCpuPct(self):
     return self.avgcpu.get_avg()

  def getAvgDiskIO(self):
     return f"{self.avgdisk_read.get_avg():.1f} {self.avgdisk_write.get_avg():.1f}"

  def getAvgNetRXTX(self):
      return f"{self.avgnet_rcv.get_avg():.01f} {self.avgnet_snd.get_avg():.1f}"

  def th_loop(self):
     while True:
        timex = time.monotonic()
        diffTime = timex - self.prevTime if self.prevTime > 0 else 0
        self.prevTime = timex
        self.track(diffTime)
        time.sleep(TRACKSLEEP)

  def trackingStart(self):
      kb_thread = threading.Thread(target=self.th_loop, daemon=True)
      kb_thread.start()
      print("tracking(): thead started")

  def showTopProcesses(self, top_n=4):
      lines = list()
      #lines.append("TOP PROCESSES")
      try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
          try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'cpu_percent', 'memory_percent'])
            processes.append(pinfo)
          except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        
        # Sort by CPU percent
        sorted_by_cpu = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:top_n]
        
        for proc in sorted_by_cpu:
          name = proc['name'][:12] if proc['name'] else 'unknown'
          cpu = proc['cpu_percent'] if proc['cpu_percent'] else 0
          mem = proc['memory_percent'] if proc['memory_percent'] else 0
          lines.append(f"{name:12} {cpu:4.1f}% {mem:4.1f}%")
      except Exception as e:
        lines.append(f"Error: {str(e)}")
      return lines

# class AvgCPU(RunningAverage):
#    def track(self):
#         super().add(sysInfo.getCurCpuPCt())

## INIT

class SysInfo():
  def  __init__(self, mntreg = MNTREG, dht_pin = None):
    print(f"Sysinfo init mntreg {mntreg}")
    self.CM = sysCmdInfo()
    self.CI = sysPyInfo()
    self.CI.trackingStart()
    self.mntreg = mntreg
    self.sensor = None
    if dht_pin is not None:

      pin = getattr(board, dht_pin)
      print(f"Sysinfo init temp sensor with pin {dht_pin} {pin}")
      self.sensor = adafruit_dht.DHT22(pin)
 
  def getAvgCpuPct(self):
      return self.CI.getAvgCpuPct()

  # def showNetInfo(self):
  #     return "Net R/T: " + self.CI.getAvgNetRXTX()

  def track(self,diffTime):
    self.CI.track(diffTime)

  def getAmbientTempHumid(self):
    if self.sensor is None:
      return None, None

    #try:
    #import adafruit_dht

    try:
      temperature = self.sensor.temperature
      humidity = self.sensor.humidity
      if temperature is not None and humidity is not None:
        return temperature, humidity
      #except RuntimeError:
      #  _time.sleep(2)
    except Exception:
      print("Failed to retrieve data from humidity sensor")
      return None, None
    #except Exception:
    #  raise Exception("Failed to import lib adafruit_dht")
    
  def showAmbientTempHumid(self):
    temperature, humidity = self.getAmbientTempHumid()
    if temperature is not None and humidity is not None:
        return f"{temperature:.1f}C {humidity:.1f}%"
    else:
        return ""

  def showInfo(self):
    lines=list()
    UPnLOAD = f'{sysPyInfo.getUptime()} {sysPyInfo.getNUsers()}, ld {sysPyInfo.getLoad()}'
    lines.append(UPnLOAD)
    CPUN = f'C {sysPyInfo.getCurCpuPCt():.0f} ~ {self.CI.getAvgCpuPct():.0f}%, {sysCmdInfo.getCpuTemp()}'
    lines.append(CPUN)
    #lines.append(str(CPU,'utf-8'))
    diskio = self.CI.getAvgDiskIO()
    th=""
    if self.sensor is not None:
        th=f", th {self.showAmbientTempHumid()}"
    MemUsage = f'M {sysPyInfo.getMemUsage()}{th}'
    lines.append(MemUsage)
    netio = self.CI.getAvgNetRXTX()
    #lines.append(net)
    lines.append(f'D {diskio} N {netio} M/s')
    #lines.append(diskio)
    Disk = f'{sysCmdInfo.getDiskUsage(self.mntreg)}'
    lines.append(Disk)

    #lines.append("IPs: " + IP)

    return lines
  
  def showTopProcesses(self):
    return self.CI.showTopProcesses()

  def shutDown(self):
    return sysCmdInfo.shutdown()

  def reboot(self):
    return sysCmdInfo.reboot()

  def restartUPNP(self):
    return sysCmdInfo.restartUPNP()

 


