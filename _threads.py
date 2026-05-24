from threading import Thread

class LogicException(Exception):
    pass

class PropagatingThread(Thread):
    def run(self):
        self.exc = None
        try:
            super(PropagatingThread, self).run()
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super(PropagatingThread, self).join(timeout)
        if self.exc:
            raise self.exc
        return self.ret