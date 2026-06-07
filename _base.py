class LogicException(Exception):
    pass

class UnknownEventException(Exception):
    pass

class ControllerBase:
    def onEvent(self, event, *args):
        if event == "down":
            return self.onDown()
        elif event == "up":
            return self.onUp()
        elif event == "mid":
            return self.onMid()
        elif event == "left":
            return self.onLeft()
        elif event == "right":
            return self.onRight()
        elif event == "set":
            return self.onSet()
        elif event == "rst":
            return self.onRst()
        elif event == "rstHeld":
            return self.onRstHeld()
        else:
            raise UnknownEventException(f"Unknown event: {event}")


## extending events
    # ## EVENT handlers
    # def onEvent(self, event, *args):
    #     try:
    #         return super().onEvent(event, *args)
    #     except UnknownEventException as e:
    #         if event == "clock":
    #             return self.clock(*args)
    #         elif event == "open":
    #             return self.selectStation()
    #         else:
    #             #print(f"Unknown event: {event}")
    #             raise e