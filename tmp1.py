#!/usr/bin/env python3
# epidemic.py - SIRS（初期感染あり・完全版）
import os
import random
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    # 環境変数 INFECTION_RATE があればそれを採用（なければデフォルト1.0）
    INFECTION_RATE = float(os.getenv("INFECTION_RATE", "1.0"))

    INFECT_TIME = 1000.0     # I -> R
    IMMUNE_TIME = 18000.0    # R -> S

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.state = 'S'
        self.time_state_changed = None

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

        # 状態遷移
        if self.state == 'I' and now - self.time_state_changed >= self.INFECT_TIME:
            self.update_state('R')
            return

        if self.state == 'R' and now - self.time_state_changed >= self.IMMUNE_TIME:
            self.update_state('S')
            return

        # 感染行動（Iのみ）
        if self.state != 'I':
            return

        viruses = self.messages()
        if not viruses:
            dummy = f"{self.id_}-0-9999"
            self.received[dummy] += 1
            viruses = [dummy]

        # CarryOnly の近傍検知を使う
        for other in self.neighbors():
            if hasattr(other, 'state') and other.state != 'S':
                continue
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    if msg not in other.received:
                        self.sendmsg(other, msg)

    def advance(self):
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        self.forward()
