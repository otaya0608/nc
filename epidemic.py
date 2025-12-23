#!/usr/bin/env python3
# epidemic.py - 循環型感染モデル (S -> I -> R -> S)
import random
import sys
from dtnsim.agent.carryonly import CarryOnly

class Epidemic(CarryOnly):
    # --- 設定（秒数） ---
    INFECTION_RATE = 1.0       # 感染確率
    DURATION_INFECTED = 3.0    # 感染(赤)している時間 (3秒)
    DURATION_IMMUNE = 5.0      # 免疫(緑)でいる時間 (5秒)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 初期状態: 健康(S), 青色
        self.state = 'S'
        self.color = 'blue'
        self.time_state_changed = 0  # 状態が変わった時刻を記録

        # ★ IDが1番のエージェントを「最初の感染者」にする
        if self.id_ == 1:
            self.update_state('I', 0) # 時刻0で感染
            # print(f"DEBUG: Agent {self.id_} starts as INFECTED", file=sys.stderr)

    def update_state(self, new_state, current_time):
        """状態を更新し、色を変更してモニターに通知する"""
        self.state = new_state
        self.time_state_changed = current_time
        
        # --- 色の設定（黒背景用） ---
        if new_state == 'S':
            self.color = 'blue'    # 健康：青
        elif new_state == 'I':
            self.color = 'red'     # 感染：赤
        elif new_state == 'R':
            self.color = 'lime'    # 免疫：緑（limeの方が黒背景で見やすい）

        # モニターに通知（色が即座に変わる）
        if hasattr(self, 'monitor'):
            self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        """他者からメッセージ（ウイルス）を受け取った時の処理"""
        super().recvmsg(agent, msg)
        
        # 健康(S)のときだけ感染する
        # 免疫(R)や既に感染(I)のときは無視する
        if self.state == 'S':
            self.update_state('I', self.scheduler.time)

    def get_all_neighbors(self):
        """通信範囲内にいる他のエージェントを取得"""
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
        """毎ステップ実行されるメインロジック"""
        current_time = self.scheduler.time

        # --- 1. 時間経過による状態変化 ---
        
        # 感染(I) -> 3秒経過 -> 免疫(R)
        if self.state == 'I':
            if (current_time - self.time_state_changed) >= self.DURATION_INFECTED:
                self.update_state('R', current_time)
                return # 変化したターンは感染活動しない

        # 免疫(R) -> 5秒経過 -> 健康(S)
        elif self.state == 'R':
            if (current_time - self.time_state_changed) >= self.DURATION_IMMUNE:
                self.update_state('S', current_time)
                return

        # --- 2. 感染活動（自分が感染者の場合のみ） ---
        if self.state != 'I':
            return

        # ウイルス（メッセージ）の準備
        viruses = self.messages()
        if not viruses:
            # ウイルスを持っていない場合（最初の感染者など）は生成
            dummy = f"{self.id_}-virus"
            self.received[dummy] += 1
            viruses = [dummy]

        # 近くにいる人を探す
        targets = self.get_all_neighbors()

        # ばら撒く
        for agent in targets:
            # 相手が免疫(R)ならスキップ（感染しない）
            if hasattr(agent, 'state') and agent.state == 'R':
                continue
            
            # 確率で感染させる
            if random.random() < self.INFECTION_RATE:
                for msg in viruses:
                    if msg not in agent.received:
                        self.sendmsg(agent, msg)

    def advance(self):
        """時間の進行"""
        self.mobility.move(self.scheduler.delta)
        # 移動をモニターに通知
        if hasattr(self, 'monitor'):
            self.monitor.move_agent(self)
        self.forward()