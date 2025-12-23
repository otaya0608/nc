#!/usr/bin/env python3
# epidemic.py - ゾンビ感染ロジックの完全版
import random
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    # 設定：感染しやすさと回復時間
    INFECTION_RATE = 1.0   # 1.0 = 100% 確実に感染（テスト用）
    RECOVERY_TIME = 2000.0 # なかなか治らないように長く設定

    def __init__(self, *args, **kwargs):
        # 親クラス(CarryOnly)の初期化
        super().__init__(*args, **kwargs)
        
        # ゾンビ用ステータス初期化
        self.state = 'S'      # S:未感染, I:感染, R:回復
        self.color = 'blue'   # 初期色は青
        self.time_infected = None
        
        # 自分のIDを表示してデバッグしやすくする
        # print(f"Agent {self.id_} initialized.")

    def update_color(self):
        """ステータスに合わせて色を決める"""
        if self.state == 'S': self.color = 'blue'
        elif self.state == 'I': self.color = 'red'
        elif self.state == 'R': self.color = 'black'

    def recvmsg(self, agent, msg):
        """メッセージを受信＝感染処理"""
        super().recvmsg(agent, msg) # 親クラスの受信処理（カウントなど）
        
        # 未感染(S)なら感染(I)させる
        if self.state == 'S':
            print(f"!!! 感染 !!! Agent {self.id_} が赤くなりました (from Agent {agent.id_})")
            self.state = 'I'
            self.time_infected = self.scheduler.time
            self.update_color()
            self.monitor.change_agent_status(self) # 画面更新通知

    def forward(self):
        """周囲への感染拡大処理"""
        
        # 1. 回復判定
        if self.state == 'I' and self.time_infected:
            if (self.scheduler.time - self.time_infected) > self.RECOVERY_TIME:
                self.state = 'R'
                self.update_color()
                self.monitor.change_agent_status(self)
                return

        # 2. 自分が感染者(I)でなければ何もしない
        if self.state != 'I': return

        # 3. ウイルスの準備（持っていなければ偽造する）
        viruses = self.pending_messages()
        if not viruses:
            # 感染力を持たせるためにダミーメッセージを作成
            dummy_virus = f"{self.id_}-0-9999" 
            self.received[dummy_virus] += 1
            viruses = [dummy_virus]

        # 4. 「neighbors(近くにいる全員)」を取得する
        # encounters()だと新入りしか見ないので、neighbors()を使うのが正解
        targets = self.neighbors()

        # 5. 全員にウイルスを投げる
        for agent in targets:
            # 相手が回復済みならスキップ
            if hasattr(agent, 'state') and agent.state == 'R': continue
            
            # 感染確率判定
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    # 相手に送りつける
                    self.sendmsg(agent, msg)

    # advanceは親クラスのものを使うので記述不要（forwardがオーバーライドされているため）