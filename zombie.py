#!/usr/bin/env python3
# epidemic.py - SIRS（再感染可能・感染が止まらない完全版）

import random
from dtnsim.agent.carryonly import CarryOnly


class Epidemic(CarryOnly):
    INFECTION_RATE = 1.0   # 接触したら必ず感染

    INFECT_TIME = 1000.0   # 赤(I) → 緑(R)
    IMMUNE_TIME = 5000.0   # 緑(R) → 青(S)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.state = 'S'
        self.time_state_changed = None

        # =========================
        # 最初の1人を感染者にする
        # =========================
        if self.id_ == 1:
            self.enter_infected()


    # -------------------------
    # 状態遷移ヘルパ
    # -------------------------
    def enter_infected(self):
        """
        I 状態に入るときは必ずウイルスを持たせる
        """
        self.state = 'I'
        self.time_state_changed = self.scheduler.time

        # ★ 必須：ウイルスを生成
        dummy = f"{self.id_}-0-9999"
        self.received[dummy] += 1

        self.monitor.change_agent_status(self)


    def update_state(self, new_state):
        self.state = new_state
        self.time_state_changed = self.scheduler.time

        # 免疫 → 健康 に戻るときは履歴を消す
        if new_state == 'S':
            self.received.clear()

        self.monitor.change_agent_status(self)


    # -------------------------
    # 感染イベント
    # -------------------------
    def recvmsg(self, agent, msg):
        super().recvmsg(agent, msg)

        if self.state == 'S':
            # ★ S → I のときも必ずウイルスを持たせる
            self.enter_infected()


    def get_all_neighbors(self):
        neighbors = []
        p = self.mobility.current

        for agent in self.scheduler.agents:
            if agent.id_ == self.id_:
                continue

            q = agent.mobility.current
            if (p[0] - q[0])**2 + (p[1] - q[1])**2 <= self.range_**2:
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

        # 念のための保険（基本は不要だが安全）
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
