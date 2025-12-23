#!/usr/bin/env python3
# cell.py - きれいな表示 + ゾンビ対応版
from dtnsim.monitor.null import Null

def float2str(v, fmt='9.3f'):
    astr = ('%' + fmt) % v
    astr = astr.replace(' ', '__')
    return astr

def to_geometry(v):
    return v / 1000

class Cell(Null):
    def open(self):
        """Initialize the color palette."""
        # --- ここで「きれいな色」を定義しています ---
        # heatXX は数字が大きいほど赤、小さいほど青になります
        print('palette c_edge   heat10 .2')
        print('palette c_vertex heat20 .9')
        
        # 人間(S)用の青っぽいパレット
        print('palette c_sus_range heat20 .3') # 薄い青(範囲)
        print('palette c_sus        heat20 .9') # 濃い青(本体)
        
        # 既存の感染(Inf)用パレット（黄色っぽい）
        print('palette c_inf_range heat80 .3')
        print('palette c_inf        heat80 .9')
        
        # 待機中用
        print('palette c_wait_sus_range heat20 .3')
        print('palette c_wait_sus        heat20 .9')

        # ★追加: ゾンビ専用の「きれいな赤」パレット
        # red .9 = 赤色の不透明度90%, red .3 = 赤色の不透明度30%
        print('palette c_zombie       red .9') 
        print('palette c_zombie_range red .3') 

    def close(self):
        pass

    def display_path(self, path):
        graph = path.graph
        if not graph: return
        for v in sorted(graph.vertices()):
            p = graph.get_vertex_attribute(v, 'xy')
            x, y = to_geometry(p[0]), to_geometry(p[1])
            print('define v{} ellipse 2 2 c_vertex {} {}'.format(v, x, y))
        for u, v in graph.edges():
            print('define - link v{} v{} 1 c_edge'.format(u, v))
        print('fix /./')

    def change_agent_status(self, agent):
        """エージェントの状態を見て、きれいなパレット色を割り当てる"""
        id_ = agent.id_
        
        # 1. デフォルトの色（人間は c_sus = 青）
        color = 'c_sus'
        if agent.mobility.wait:
            color = 'c_wait_sus'
        if agent.received or agent.receive_queue:
            color = 'c_inf' # メッセージ持ちは黄色

        # 2. ★ゾンビ優先ロジック★
        if hasattr(agent, 'state'):
            if agent.state == 'I':
                color = 'c_zombie'  # さっき定義した「きれいな赤」を使う
            elif agent.state == 'R':
                color = 'c_edge'    # 回復者はグレーっぽく
            elif agent.state == 'S':
                color = 'c_sus'     # 未感染は青

        # 3. 本体と範囲(_range)の色を出力
        print('color agent{} {}'.format(id_, color))
        # パレット名の場合は _range をつけることで、半透明の円を描画させる
        if '_sus' in color or '_inf' in color or '_zombie' in color:
            print('color agentr{} {}_range'.format(id_, color))
        else:
            # 万が一パレット以外の色が来てもエラーにならないように
            print('color agentr{} {}'.format(id_, color))

    def display_agents(self):
        for agent in self.scheduler.agents:
            id_ = agent.id_
            p = agent.mobility.current
            x, y = to_geometry(p[0]), to_geometry(p[1])
            r = to_geometry(agent.range_)
            # ここで円の定義
            print('define agent{} ellipse 4 4 white {} {}'.format(id_, x, y))
            print('define agentr{0} ellipse {1} {1} white {2} {3}'.format(id_, r, x, y))
            self.change_agent_status(agent)

    def move_agent(self, agent):
        id_ = agent.id_
        p = agent.mobility.current
        x, y = to_geometry(p[0]), to_geometry(p[1])
        print('move agent{} {} {}'.format(id_, x, y))
        print('move agentr{} {} {}'.format(id_, x, y))
        # 移動時にも色チェックを行う（感染した瞬間に色を変えるため）
        self.change_agent_status(agent)

    def display_status(self):
        time = float2str(self.scheduler.time, '10.2f')
        tx = float2str(self.tx_total, '10g')
        rx = float2str(self.rx_total, '10g')
        dup = float2str(self.dup_total, '10g')
        uniq_total = float2str(self.uniq_total, '10g')
        delivered_total = float2str(self.delivered_total, '10g')
        uniq_delivered_total = float2str(self.uniq_delivered_total, '10g')
        print(
            'define status_l text Time:{},____TX:{},____RX:{},____DUP:{},____Delivered:{}__/__{},____Arrived:{} 14 white 0.5 0.05'
            .format(time, tx, rx, dup, uniq_delivered_total, uniq_total, delivered_total))

    def update(self):
        print('display')