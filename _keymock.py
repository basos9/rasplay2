## 
## BUTTON

#from gpiozero import Button
import threading
import sys
import select
import time
from controller import ControllerBase
BTN_BOUNCE_TIME = 0.05

class keymock():

    def __init__(self, state: ControllerBase):
        self.state = state
        self.mock()

    def key_available(self):
        """Check if a key is waiting in stdin (non-blocking)."""
        return select.select([sys.stdin], [], [], 0)[0]

    def get_key_nonblock(self):
        """Read key if available, return None otherwise."""
        if self.key_available():
            return sys.stdin.read(1)
        return None

    def on_key(self, key):
        """Handle PC keyboard events with callbacks"""
        try:
            #print(f'Mock Key pressed: {key}')
            if key ==  '8':
                self.state.onEvent("up")
            elif key == '2':
                self.state.onEvent("down")
            elif key == '4':
                self.state.onEvent("left")
            elif key == '6':
                self.state.onEvent("right")
            elif key == '5':
                self.state.onEvent("mid")
            elif key  == '0':
                self.state.onEvent("set")
            elif key == '.':
                self.state.onEvent("rst")
            else:
                print(f"Unknown key: {key}")
               
        except AttributeError:
            pass

    def th_keyboard(self):
      """Start listening for PC keyboard events"""
      while True:
          key = self.get_key_nonblock()
          self.on_key(key) if key else None
          time.sleep(0.1)
    
    def mock(self):
        """Start keyboard listener in background thread"""
        kb_thread = threading.Thread(target=self.th_keyboard, daemon=True)
        kb_thread.start()





