import subprocess
import psutil
import copy
import time
import threading
from _maths import RunningAverage

MNTREG = '^/'
MAVG_SIZELOOPS = 20
TRACKSLEEP = 1

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
    cmd = """vcgencmd measure_temp | awk '{gsub(/temp=/,""); printf "te %s",$0;}'"""
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
    self.prevNetStats = {}
    self.prevTime = 0

  def getCurCpuPCt():
     cpu_percent = psutil.cpu_percent(interval=1)
     return cpu_percent
  
  def getLoad3():
     return psutil.getloadavg()
  
  def  getLoad():
    la = psutil.getloadavg()
    return f"{la[0]:.1f} ~ {la[1]:.1f}"
  
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

  def getAvgCpuPct(self):
     return self.avgcpu.get_avg()

  def getAvgNetRXTX(self):
      return f"{self.avgnet_rcv.get_avg():.01f} / {self.avgnet_snd.get_avg():.1f} MB/s"

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




# class AvgCPU(RunningAverage):
#    def track(self):
#         super().add(sysInfo.getCurCpuPCt())

## INIT

class SysInfo():
  def  __init__(self, mntreg = MNTREG):
    print(f"Sysinfo init mntreg {mntreg}")
    self.CM = sysCmdInfo()
    self.CI = sysPyInfo()
    self.CI.trackingStart()
    self.mntreg = mntreg

  def getAvgCpuPct(self):
      return self.CI.getAvgCpuPct()

  def showNetInfo(self):
      lines = list()
      lines.append("Net R/T: " + self.CI.getAvgNetRXTX())
      return lines

  def track(self,diffTime):
    self.CI.track(diffTime)

  def showInfo(self):
    lines=list()
    UPnLOAD = f'{sysPyInfo.getUptime()} {sysPyInfo.getNUsers()}, ld {sysPyInfo.getLoad()}'
    lines.append(UPnLOAD)
    CPUN = f'CPU: {sysPyInfo.getCurCpuPCt():.0f}% ~ {self.CI.getAvgCpuPct():.0f}%, {sysCmdInfo.getCpuTemp()}'
    lines.append(CPUN)
    #lines.append(str(CPU,'utf-8'))
    MemUsage = f'Mem: {sysCmdInfo.getMemUsage()}'
    lines.append(MemUsage)
    Disk = f'{sysCmdInfo.getDiskUsage(self.mntreg)}'
    lines.append(Disk)
    #lines.append("IPs: " + IP)

    return lines

  def shutDown(self):
    return sysCmdInfo.shutdown()

  def reboot(self):
    return sysCmdInfo.reboot()

  def restartUPNP(self):
    return sysCmdInfo.restartUPNP()


