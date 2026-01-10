#!/usr/bin/env python3
# epidemic.py - SIRS（初期感染あり・完全版 + 確率env反映(毎回) + DBG）
import os
import sys
import random
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    INFECTION_RATE = 1.0      # デフォルト（envが無い時）
    INFECT_TIME = 1000.0      # I -> R
    IMMUNE_TIME = 18000.0     # R -> S

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.state = 'S'
        self.time_state_changed = None

        # DBGを出しすぎないため（患者0だけ）
        self._dbg_last_t = -1

        # 初期感染者
        if self.id_ == 1:
            self.state = 'I'
            self.time_state_changed = self.scheduler.time
            dummy = f"{self.id_}-0-9999"
            self.received[dummy] += 1

    def update_state(self, new_state):
        self.state = new_state
        self.time_state_changed = self.scheduler.time

        # Sに戻ったらウイルスを消す（再感染可能にする）
        if new_state == 'S':
            self.received.clear()

        self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        super().recvmsg(agent, msg)
        if self.state == 'S':
            self.update_state('I')

    def forward(self):
        now = self.scheduler.time

        # --- 状態遷移 ---
        if self.state == 'I' and now - self.time_state_changed >= self.INFECT_TIME:
            self.update_state('R')
            return

        if self.state == 'R' and now - self.time_state_changed >= self.IMMUNE_TIME:
            self.update_state('S')
            return

        # --- 感染行動（Iのみ） ---
        if self.state != 'I':
            return

        # ★ここで毎回 env から感染確率を読む（確実に反映）
        try:
            rate = float(os.getenv("INFECTION_RATE", str(self.INFECTION_RATE)))
        except ValueError:
            rate = self.INFECTION_RATE

        viruses = self.messages()
        if not viruses:
            dummy = f"{self.id_}-0-9999"
            self.received[dummy] += 1
            viruses = [dummy]

        # 近傍取得
        neis = self.neighbors()

        # --- DBG（患者0だけ、50刻みで出す）---
        if self.id_ == 1:
            t_int = int(now)
            if t_int % 50 == 0 and t_int != self._dbg_last_t:
                self._dbg_last_t = t_int
                try:
                    sys.stderr.write(f"DBG t={now} neis={len(neis)} rate={rate}\n")
                    sys.stderr.flush()
                except BrokenPipeError:
                    sys.exit(0)

        # --- 感染ばらまき ---
        for other in neis:
            if hasattr(other, 'state') and other.state != 'S':
                continue

            if random.random() < rate:
                for msg in viruses:
                    if msg not in other.received:
                        if self.id_ == 1:
                            try:
                                sys.stderr.write(f"DBG infected other={other.id_} t={now}\n")
                                sys.stderr.flush()
                            except BrokenPipeError:
                                sys.exit(0)

                        self.sendmsg(other, msg)

    def advance(self):
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        self.forward()
