#!/usr/bin/env python3
# epidemic.py - SIR（時間付き）版
import random
import sys
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    INFECTION_RATE = 1.0

    INFECT_TIME = 3.0   # 赤(I) → 緑(R) まで（秒）
    IMMUNE_TIME = 5.0   # 緑(R) → 青(S) まで（秒）

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.state = 'S'
        self.time_state_changed = None

        # 最初の感染者
        if self.id_ == 1:
            self.state = 'I'
            self.time_state_changed = self.scheduler.time

    def update_state(self, new_state):
        self.state = new_state
        self.time_state_changed = self.scheduler.time
        self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        super().recvmsg(agent, msg)
        if self.state == 'S':
            self.update_state('I')

    def get_all_neighbors(self):
        neighbors = []
        p = self.mobility.current
        for agent in self.scheduler.agents:
            if agent.id_ == self.id_: 
                continue
            q = agent.mobility.current
            if (p[0]-q[0])**2 + (p[1]-q[1])**2 <= self.range_**2:
                neighbors.append(agent)
        return neighbors

    def forward(self):
        now = self.scheduler.time

        # ---------- 状態遷移 ----------
        if self.state == 'I':
            if now - self.time_state_changed >= self.INFECT_TIME:
                self.update_state('R')
                return

        if self.state == 'R':
            if now - self.time_state_changed >= self.IMMUNE_TIME:
                self.update_state('S')
                return

        # ---------- 感染行動 ----------
        if self.state != 'I':
            return

        viruses = self.messages()
        if not viruses:
            dummy = f"{self.id_}-0-9999"
            self.received[dummy] += 1
            viruses = [dummy]

        for agent in self.get_all_neighbors():
            if hasattr(agent, 'state') and agent.state != 'S':
                continue
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    if msg not in agent.received:
                        self.sendmsg(agent, msg)

    def advance(self):
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        self.forward()
