#!/usr/bin/env python3
# statnull.py - 可視化なしでSTATをstderrに吐くMonitor

import os
import sys
from dtnsim.monitor.null import Null

class StatNull(Null):
    def update(self):
        # 環境変数でON/OFF（デフォルトは出さない）
        if os.getenv("STAT_LOG", "0") != "1":
            return

        I = 0
        for a in self.scheduler.agents:
            if hasattr(a, "state") and a.state == "I":
                I += 1

        try:
            sys.stderr.write(f"STAT {self.scheduler.time} {I}\n")
            sys.stderr.flush()
        except BrokenPipeError:
            sys.exit(0)
