#!/usr/bin/env python3
# epidemic.py
import random
import sys
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    # --- 設定（秒数） ---
    INFECTION_RATE = 1.0       # 感染確率
    DURATION_INFECTED = 3.0    # 感染(赤)している時間
    DURATION_IMMUNE = 5.0      # 免疫(緑)でいる時間

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 変数の初期化だけを行う（ここでは self.monitor を呼ばない！）
        self.time_state_changed = 0
        
        # IDが1番のエージェントは最初から感染状態（赤）に設定しておく
        if self.id_ == 1:
            self.state = 'I'
            self.color = 'red'
            self.time_state_changed = 0
        else:
            self.state = 'S'
            self.color = 'blue' # 背景が黒なら cyan 推奨だが、一旦 blue
            
    def update_visual(self):
        """色を決めてモニターに通知する安全なメソッド"""
        # 状態に合わせて色変数をセット
        if self.state == 'S':
            self.color = 'cyan'    # 健康：シアン（青）
        elif self.state == 'I':
            self.color = 'red'     # 感染：赤
        elif self.state == 'R':
            self.color = 'lime'    # 免疫：緑（ライム）

        # モニターが存在する場合のみ通知（エラー落ち防止）
        if hasattr(self, 'monitor') and self.monitor:
            try:
                self.monitor.change_agent_status(self)
            except:
                pass # 描画エラーで止まるのを防ぐ

    def recvmsg(self, agent, msg):
        super().recvmsg(agent, msg)
        
        # 健康(S)のときだけ感染する
        if self.state == 'S':
            self.state = 'I'
            self.time_state_changed = self.scheduler.time
            self.update_visual() # 即座に色を変える

    def get_all_neighbors(self):
        neighbors = []
        p = self.mobility.current
        # scheduler.agents が存在するか確認
        if not hasattr(self.scheduler, 'agents'):
            return []
            
        for agent in self.scheduler.agents:
            if agent.id_ == self.id_: continue
            q = agent.mobility.current
            dist_sq = (p[0]-q[0])**2 + (p[1]-q[1])**2
            if dist_sq <= self.range_**2:
                neighbors.append(agent)
        return neighbors

    def forward(self):
        current_time = self.scheduler.time

        # --- 0. 初回フレームの同期（重要） ---
        # シミュレーション開始直後に一度だけ色を確定させる処理
        # これがないと最初の感染者が青色のままになる可能性がある
        if current_time <= self.scheduler.delta and self.state == 'I':
            self.update_visual()

        # --- 1. 時間経過による状態変化 ---
        if self.state == 'I':
            # 感染して3秒経ったら -> 免疫(R)
            if (current_time - self.time_state_changed) >= self.DURATION_INFECTED:
                self.state = 'R'
                self.time_state_changed = current_time
                self.update_visual()
                return 

        elif self.state == 'R':
            # 免疫になって5秒経ったら -> 健康(S)
            if (current_time - self.time_state_changed) >= self.DURATION_IMMUNE:
                self.state = 'S'
                self.time_state_changed = current_time
                self.update_visual()
                return

        # --- 2. 感染活動 ---
        # 自分が感染者(I)でなければ何もしない
        if self.state != 'I':
            return

        viruses = self.messages()
        if not viruses:
            # ウイルス生成
            dummy = f"{self.id_}-virus"
            self.received[dummy] += 1
            viruses = [dummy]

        # 近くの人を探して感染させる
        targets = self.get_all_neighbors()
        for agent in targets:
            # 相手が免疫(R)ならスキップ
            if hasattr(agent, 'state') and agent.state == 'R':
                continue
            
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    if msg not in agent.received:
                        self.sendmsg(agent, msg)

    def advance(self):
        self.mobility.move(self.scheduler.delta)
        
        # 移動描画
        if hasattr(self, 'monitor') and self.monitor:
            try:
                self.monitor.move_agent(self)
            except:
                pass
                
        self.forward()