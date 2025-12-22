import random
from dtnsim.agent.carryonly import CarryOnly

# クラス名は必要に応じて 'Epidemic' に戻してください
class Zombie(CarryOnly):
    # ▼▼▼ パラメータ設定 ▼▼▼
    INFECTION_RATE = 0.8  # 感染確率 (80%)
    RECOVERY_TIME = 100.0 # 感染してから治るまでの時間
    # ▲▲▲ ▲▲▲ ▲▲▲

    def update_color(self):
        """状態に応じてエージェントの色(self.color)を変更する"""
        if self.state == 'S':
            self.color = 'blue'   # 健康
        elif self.state == 'I':
            self.color = 'red'    # ゾンビ
        elif self.state == 'R':
            self.color = 'black'  # 免疫/死亡

    def check_recovery(self):
        """時間経過による治癒(I -> R)の判定"""
        if self.state == 'I':
            current_time = self.scheduler.time
            # 感染時刻から一定時間経過したら R になる
            if self.time_infected is not None and \
               (current_time - self.time_infected) > self.RECOVERY_TIME:
                self.state = 'R'
                self.time_recovered = current_time
                self.received.clear() # ウイルスを消す
                self.update_color()
                self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        """メッセージ(ウイルス)を受け取った時の処理"""
        # 親クラスの受信処理を実行(カウントなど)
        super().recvmsg(agent, msg)

        # もし自分が健康(S)なら、感染(I)する
        if self.state == 'S':
            self.state = 'I'
            self.time_infected = self.scheduler.time
            self.update_color()

    def forward(self):
        """感染拡大ロジック"""
        # 1. 治癒判定を行う
        self.check_recovery()

        # 2. 自分が感染者(I)でなければ、拡散しない
        if self.state != 'I':
            return

        # 3. 周囲のエージェントに感染を試みる
        encounters = self.encounters()
        viruses = self.pending_messages()

        if not viruses:
            return

        for agent in encounters:
            # 相手が R (免疫) なら感染させない
            if agent.state == 'R':
                continue
            
            # 確率で感染させる
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    # 宛先チェックなしで送りつける(感染)
                    self.sendmsg(agent, msg)

    def advance(self):
        """時間経過処理のオーバーライド"""
        # 移動
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        
        # 感染・治癒処理 (forward内で check_recovery も呼ばれる)
        self.forward()