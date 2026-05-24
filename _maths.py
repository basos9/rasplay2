import numpy

class RunningAverage():
    def __init__(self, stack_size):
        self.stack = [0 for _ in range(stack_size)]
        self.ptr = 0
        self.full_cycle = False
    def add(self, value):
        self.stack[self.ptr] = value
        self.ptr += 1
        if self.ptr == len(self.stack):
            self.full_cycle = True
            self.ptr = 0
    def get_avg(self):
        if self.full_cycle:
            return numpy.mean(self.stack)
        else:
            if self.ptr > 0:
              return numpy.mean(self.stack[:self.ptr])
            return 0