#!/usr/bin/env python3
# null.py - 可視化なし + 統計(STAT)出力用
import os
import sys

class Null:
    def __init__(self, scheduler=None):
        # dtnsim 側から scheduler が注入される前提
        self.scheduler = scheduler

    def open(self):
        pass

    def close(self):
        pass

    def display_path(self, path):
        pass

    def display_agents(self):
        pass

    def move_agent(self, agent):
        pass

    def display_forward(self, a, b, msg):
        pass

    def change_agent_status(self, agent):
        pass

    def display_status(self):
        pass

    def update(self):
        """
        dtnsim の各ステップで呼ばれる想定。
        STAT_LOG=1 のときだけ、感染者数を stderr に出す。
        stdout は汚さない（Illegal command 回避）。
        """
        if os.getenv("STAT_LOG", "0") != "1":
            return

        # scheduler が未セットなら何もしない
        if self.scheduler is None:
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
