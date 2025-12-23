#!/usr/bin/env python3
import random
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    # パラメータ設定
    INFECTION_RATE = 0.8   # 感染確率 (0.8 = 80%)
    RECOVERY_TIME = 1000.0 # 回復までの時間(長めに設定)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = 'S'      # 初期状態
        self.color = 'blue'   # 通常色
        self.time_infected = None
        self.time_recovered = None

    def update_color(self):
        if self.state == 'S': self.color = 'blue'
        elif self.state == 'I': self.color = 'red'
        elif self.state == 'R': self.color = 'black'

    def check_recovery(self):
        if self.state == 'I':
            if self.time_infected and (self.scheduler.time - self.time_infected) > self.RECOVERY_TIME:
                self.state = 'R'
                self.time_recovered = self.scheduler.time
                self.received.clear()
                self.update_color()
                self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        """メッセージを受け取ったら感染する"""
        super().recvmsg(agent, msg)
        if self.state == 'S':
            print(f"!!! 感染発生 !!! Agent {self.id_} が Agent {agent.id_} から感染しました！")
            self.state = 'I'
            self.time_infected = self.scheduler.time
            self.update_color()
            self.monitor.change_agent_status(self)

    def forward(self):
        """ウイルスをばら撒く処理"""
        self.check_recovery()
        
        # 自分が感染(I)していなければ何もしない
        if self.state != 'I': return

        # 1. ウイルスの確認（ここが重要！）
        viruses = self.pending_messages()
        
        # 【修正点】感染者なのにウイルス(メッセージ)を持っていない場合、強制的に生み出す
        if not viruses:
            # "送信元ID-宛先ID-メッセージID" の形式でダミーウイルスを作成
            dummy_virus = f"{self.id_}-0-9999" 
            self.received[dummy_virus] += 1
            viruses = [dummy_virus]
            # print(f"DEBUG: Agent {self.id_} はウイルスを自己生成しました")

        # 2. 近くにいる全員を取得
        neighbors = self.neighbors()
        if not neighbors: return # 誰もいなければ終了

        # 3. 全員にウイルスを試行
        for agent in neighbors:
            # 相手が回復済み(R)なら無視
            if hasattr(agent, 'state') and agent.state == 'R': continue
            
            # 相手がすでに感染者(I)なら無視（ログがうるさくなるので）
            if hasattr(agent, 'state') and agent.state == 'I': continue

            # 感染確率の判定
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    # print(f"DEBUG: Agent {self.id_} -> Agent {agent.id_} へウイルス送信試行")
                    self.sendmsg(agent, msg)

    def advance(self):
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        self.forward()