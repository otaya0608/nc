import random
# ▼▼▼ システムに入っているオリジナルのCarryOnlyを使う ▼▼▼
from dtnsim.agent.carryonly import CarryOnly

class Zombie(CarryOnly):
    # パラメータ設定
    INFECTION_RATE = 0.8
    RECOVERY_TIME = 100.0

    # ▼▼▼ 重要: 親に頼らず、自分で変数を初期化する ▼▼▼
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ここで定義すれば、親クラス(CarryOnly)を書き換えなくて済む！
        self.state = 'S'
        self.color = 'blue'
        self.time_infected = None
        self.time_recovered = None

    def update_color(self):
        """色を変える"""
        if self.state == 'S': self.color = 'blue'
        elif self.state == 'I': self.color = 'red'
        elif self.state == 'R': self.color = 'black'

    def check_recovery(self):
        """治癒判定"""
        if self.state == 'I':
            if self.time_infected and (self.scheduler.time - self.time_infected) > self.RECOVERY_TIME:
                self.state = 'R'
                self.time_recovered = self.scheduler.time
                self.received.clear()
                self.update_color()
                self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        """受信時の処理"""
        super().recvmsg(agent, msg)
        # Sなら感染する
        if self.state == 'S':
            self.state = 'I'
            self.time_infected = self.scheduler.time
            self.update_color()
            self.monitor.change_agent_status(self)

    def forward(self):
        """拡散ロジック"""
        self.check_recovery()
        if self.state != 'I': return

        encounters = self.encounters()
        viruses = self.pending_messages()
        if not viruses: return

        for agent in encounters:
            # 相手にstate属性がない場合は無視(安全策)、Rなら無視
            if hasattr(agent, 'state') and agent.state == 'R': continue
            
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    self.sendmsg(agent, msg)

    def advance(self):
        """時間進行"""
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        self.forward()