#!/usr/bin/env python3
# epidemic.py (ゾンビ・強制感染版)
import random
import sys
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    # 感染設定
    INFECTION_RATE = 1.0   # 100%感染（テスト用）
    RECOVERY_TIME = 2000.0 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = 'S'      # S:人, I:ゾンビ, R:免疫
        self.color = 'blue'
        self.time_infected = None

    def update_color(self):
        """状態に合わせて色を変え、強制的に画面へコマンドを送る"""
        if self.state == 'S': self.color = 'blue'
        elif self.state == 'I': self.color = 'red'
        elif self.state == 'R': self.color = 'black'
        
        # システムの標準出力に色変更コマンドをねじ込む
        # これで黄色になるのを防ぎます
        print(f"config agent{self.id_} color {self.color}", flush=True)

    def recvmsg(self, agent, msg):
        """受信＝感染"""
        super().recvmsg(agent, msg)
        if self.state == 'S':
            self.state = 'I'
            self.time_infected = self.scheduler.time
            self.update_color()

    def forward(self):
        """周囲への感染拡大"""
        # 1. 治癒判定
        if self.state == 'I' and self.time_infected:
            if (self.scheduler.time - self.time_infected) > self.RECOVERY_TIME:
                self.state = 'R'
                self.update_color()
                return

        # 2. 自分がゾンビ(I)でなければ何もしない
        if self.state != 'I': return

        # 3. ウイルスを持っているか確認（なければ作る）
        viruses = self.messages() # pendingではなくmessages全体を見る
        if not viruses:
            # 最初の1匹目のためにウイルスを偽造
            dummy = f"{self.id_}-0-9999"
            self.received[dummy] += 1
            viruses = [dummy]

        # 4. 近くにいる「全員」を取得
        # encounters(新しい出会い)ではなく neighbors(近傍全員)を使う
        targets = self.neighbors()

        # 5. 全員にばら撒く
        for agent in targets:
            if hasattr(agent, 'state') and agent.state == 'R': continue
            
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    # 相手がまだ持っていない場合のみ送る
                    if msg not in agent.received:
                         self.sendmsg(agent, msg)

    def advance(self):
        """毎フレーム呼ばれる処理"""
        # 親クラスの移動処理
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        
        # ★ここが重要★
        # 毎フレーム、自分がゾンビなら「俺は赤だ！」と主張する
        # これで黄色に戻されるのを防ぐ
        if self.state == 'I':
            print(f"config agent{self.id_} color red", flush=True)
            
        self.forward()