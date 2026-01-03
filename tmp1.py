#!/usr/bin/env python3
import sys
from dtnsim.monitor.null import Null

class StatNull(Null):
    def __init__(self, scheduler=None):
        super().__init__(scheduler=scheduler)
        self.interval = 50
        self._last_t = -1

    def update(self):
        # ← これが無いと display_status が呼ばれない
        self.display_status()

    def display_status(self):
        t = int(self.scheduler.time)

        if t == self._last_t:
            return
        self._last_t = t

        if t % self.interval != 0:
            return

        S = I = R = 0
        for a in self.scheduler.agents:
            st = getattr(a, "state", None)
            if st == "S":
                S += 1
            elif st == "I":
                I += 1
            elif st == "R":
                R += 1

        try:
            sys.stderr.write(f"STAT {t} {S} {I} {R}\n")
            sys.stderr.flush()
        except BrokenPipeError:
            sys.exit(0)
