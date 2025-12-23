#!/usr/bin/env python3
# epidemic.py - 最初の1人を感染させる版
import random
import sys
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    INFECTION_RATE = 1.0   # 100%感染
    RECOVERY_TIME = 2000.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = 'S'
        self.color = 'blue'
        self.time_infected = None

        # ★ここが重要: IDが1番のエージェントを「最初のゾンビ」にする
        if self.id_ == 1:
            self.state = 'I'
            self.time_infected = 0 # シミュレーション開始と同時に感染
            # print(f"DEBUG: Agent {self.id_} is PATIENT ZERO", file=sys.stderr)

    def update_state(self, new_state):
        self.state = new_state
        # 状態が変わったらモニターに即座に通知（これで色が即変わる）
        self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        super().recvmsg(agent, msg)
        if self.state == 'S':
            self.time_infected = self.scheduler.time
            self.update_state('I')

    def get_all_neighbors(self):
        neighbors = []
        p = self.mobility.current
        for agent in self.scheduler.agents:
            if agent.id_ == self.id_: continue
            q = agent.mobility.current
            dist_sq = (p[0]-q[0])**2 + (p[1]-q[1])**2
            if dist_sq <= self.range_**2:
                neighbors.append(agent)
        return neighbors

    def forward(self):
        # 1. 治癒判定
        if self.state == 'I' and self.time_infected:
            # 最初のゾンビ(time=0)の場合も考慮
            current_time = self.scheduler.time
            # time=0のときは初期設定直後なので治さない
            if current_time > 0 and (current_time - self.time_infected) > self.RECOVERY_TIME:
                self.update_state('R')
                return

        # 2. 自分がゾンビ(I)でなければ終了
        if self.state != 'I': return

        # 3. ウイルス弾込め
        viruses = self.messages()
        if not viruses:
            # まだ誰もウイルスを持っていないなら、ここで作る
            # (ID=1の最初のゾンビがこれを行う)
            dummy = f"{self.id_}-0-9999"
            self.received[dummy] += 1
            viruses = [dummy]

        # 4. 近くにいる人を探す
        targets = self.get_all_neighbors()

        # 5. ばら撒く
        for agent in targets:
            if hasattr(agent, 'state') and agent.state == 'R': continue
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    if msg not in agent.received:
                        self.sendmsg(agent, msg)

    def advance(self):
        self.mobility.move(self.scheduler.delta)
        # 移動直後にも描画更新を要求する（スムーズな色変化のため）
        self.monitor.move_agent(self)
        self.forward()