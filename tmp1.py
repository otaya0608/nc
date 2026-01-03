#!/usr/bin/env python3
# statnull.py - SIRS用：S/I/Rを一定間隔でstderrに出す（可視化なし）
import os
import sys
from dtnsim.monitor.null import Null

class StatNull(Null):
    def __init__(self, scheduler=None):
        super().__init__(scheduler=scheduler)
        # 何ステップ(時間)ごとにSTATを出すか（環境変数で上書き可）
        self.stat_interval = int(os.getenv("STAT_INTERVAL", "50"))
        self._last_stat_t = None

    def _count_sir(self):
        S = I = R = 0
        for a in self.scheduler.agents:
            st = getattr(a, "state", None)
            if st == "S": S += 1
            elif st == "I": I += 1
            elif st == "R": R += 1
        return S, I, R

    def update(self):
        # scheduler.time は float のことが多いので int で丸めて間引く
        t = int(self.scheduler.time)
        if self._last_stat_t == t:
            return
        self._last_stat_t = t

        if t % self.stat_interval != 0:
            return

        S, I, R = self._count_sir()
        try:
            sys.stderr.write(f"STAT {t} {S} {I} {R}\n")
            sys.stderr.flush()
        except BrokenPipeError:
            sys.exit(0)
