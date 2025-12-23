#!/usr/bin/env python3
import random
# システムのCarryOnlyを読み込む
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    # パラメータ設定
    INFECTION_RATE = 0.8   # 感染確率 (0.0 ~ 1.0)
    RECOVERY_TIME = 100.0  # 治るまでの時間

    # 自分で変数を初期化する
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = 'S'      # 初期状態は S (Susceptible: 未感染)
        self.color = 'blue'   # 色は青
        self.time_infected = None
        self.time_recovered = None

    def update_color(self):
        """状態に応じてエージェントの色を更新する"""
        if self.state == 'S': self.color = 'blue'
        elif self.state == 'I': self.color = 'red'
        elif self.state == 'R': self.color = 'black'

    def check_recovery(self):
        """時間が経過したら回復(R)させる"""
        if self.state == 'I':
            if self.time_infected and (self.scheduler.time - self.time_infected) > self.RECOVERY_TIME:
                self.state = 'R'
                self.time_recovered = self.scheduler.time
                self.received.clear()  # ウイルスを削除（あるいは保持したままにするかはルール次第）
                self.update_color()
                self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        """メッセージ(ウイルス)を受け取った時の処理"""
        super().recvmsg(agent, msg)
        # 未感染(S)なら感染(I)させる
        if self.state == 'S':
            self.state = 'I'
            self.time_infected = self.scheduler.time
            self.update_color()
            self.monitor.change_agent_status(self)

    def forward(self):
        """
        近くにいるエージェントにウイルスをばら撒く処理
        """
        self.check_recovery()
        
        # 自分が感染(I)していなければ何もしない
        if self.state != 'I': return

        # 【重要修正】encounters() ではなく neighbors() を使う
        # encounters: 「新しく範囲に入ってきた人」だけ (すり抜けの原因)
        # neighbors : 「今、範囲内にいる全員」 (これで並走しても感染する)
        neighbors = self.neighbors()
        
        viruses = self.pending_messages()
        if not viruses: return

        for agent in neighbors:
            # 相手がすでに回復(R)していたらスキップ
            if hasattr(agent, 'state') and agent.state == 'R': continue
            
            # 確率判定で感染させる
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    # 相手にメッセージ(ウイルス)を送る
                    self.sendmsg(agent, msg)

    def advance(self):
        """シミュレーションの1ステップを進める"""
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        self.forward()  # 移動した後に感染処理を行う