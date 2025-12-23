#!/usr/bin/env python3
# cell.py - SIR対応 完全版
from dtnsim.monitor.null import Null

def float2str(v, fmt='9.3f'):
    astr = ('%' + fmt) % v
    astr = astr.replace(' ', '__')
    return astr

def to_geometry(v):
    return v / 1000

class Cell(Null):
    def open(self):
        # --- 基本 ---
        print('palette c_edge   heat10 .2')
        print('palette c_vertex heat20 .9')

        # S（健康）青
        print('palette c_sus_range heat20 .3')
        print('palette c_sus       heat20 .9')

        # メッセージ保持（黄色）
        print('palette c_inf_range heat80 .3')
        print('palette c_inf       heat80 .9')

        # 待機
        print('palette c_wait_sus_range heat20 .3')
        print('palette c_wait_sus       heat20 .9')

        # I（感染）赤
        print('palette c_zombie       red .9')
        print('palette c_zombie_range red .3')

        # R（免疫）緑
        print('palette c_rec       green .9')
        print('palette c_rec_range green .3')

    def close(self):
        pass

    def display_path(self, path):
        graph = path.graph
        if not graph:
            return
        for v in sorted(graph.vertices()):
            p = graph.get_vertex_attribute(v, 'xy')
            x, y = to_geometry(p[0]), to_geometry(p[1])
            print(f'define v{v} ellipse 2 2 c_vertex {x} {y}')
        for u, v in graph.edges():
            print(f'define - link v{u} v{v} 1 c_edge')
        print('fix /./')

    def change_agent_status(self, agent):
        id_ = agent.id_

        # デフォルト（青）
        color = 'c_sus'
        if agent.mobility.wait:
            color = 'c_wait_sus'
        if agent.received or agent.receive_queue:
            color = 'c_inf'

        # ---- SIR 優先 ----
        if hasattr(agent, 'state'):
            if agent.state == 'I':
                color = 'c_zombie'   # 赤
            elif agent.state == 'R':
                color = 'c_rec'      # 緑
            elif agent.state == 'S':
                color = 'c_sus'      # 青

        print(f'color agent{id_} {color}')

        if '_sus' in color or '_inf' in color or '_zombie' in color or '_rec' in color:
            print(f'color agentr{id_} {color}_range')
        else:
            print(f'color agentr{id_} {color}')

    def display_agents(self):
        for agent in self.scheduler.agents:
            id_ = agent.id_
            p = agent.mobility.current
            x, y = to_geometry(p[0]), to_geometry(p[1])
            r = to_geometry(agent.range_)
            print(f'define agent{id_} ellipse 4 4 white {x} {y}')
            print(f'define agentr{id_} ellipse {r} {r} white {x} {y}')
            self.change_agent_status(agent)

    def move_agent(self, agent):
        id_ = agent.id_
        p = agent.mobility.current
        x, y = to_geometry(p[0]), to_geometry(p[1])
        print(f'move agent{id_} {x} {y}')
        print(f'move agentr{id_} {x} {y}')
        self.change_agent_status(agent)

    def display_status(self):
        time = float2str(self.scheduler.time, '10.2f')
        print(f'define status_l text Time:{time} 14 white 0.5 0.05')

    def update(self):
        print('display')
