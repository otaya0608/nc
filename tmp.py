#!/usr/bin/env python3
# cell.py - SIR/Epidemic 完全対応・STAT出力付き

from dtnsim.monitor.null import Null
import sys

def safe_print(s):
    try:
        print(s)
    except BrokenPipeError:
        sys.exit(0)

def float2str(v, fmt='9.3f'):
    astr = ('%' + fmt) % v
    return astr.replace(' ', '__')

def to_geometry(v):
    return v / 1000


class Cell(Null):

    def open(self):
        self.defined_agents = set()

        # ---- palette 定義 ----
        safe_print('palette c_edge   heat10 .2')
        safe_print('palette c_vertex heat20 .9')

        # S: 健康（青）
        safe_print('palette c_sus_range heat20 .3')
        safe_print('palette c_sus        heat20 .9')

        # I: 感染（赤）
        safe_print('palette c_inf_range red .3')
        safe_print('palette c_inf        red .9')

        # R: 免疫（緑）
        safe_print('palette c_rec_range green .3')
        safe_print('palette c_rec        green .9')

        # wait 中
        safe_print('palette c_wait_sus_range heat20 .3')
        safe_print('palette c_wait_sus        heat20 .9')

    def close(self):
        pass

    def display_path(self, path):
        graph = path.graph
        if not graph:
            return
        for v in sorted(graph.vertices()):
            p = graph.get_vertex_attribute(v, 'xy')
            x, y = to_geometry(p[0]), to_geometry(p[1])
            safe_print(f'define v{v} ellipse 2 2 c_vertex {x} {y}')
        for u, v in graph.edges():
            safe_print(f'define - link v{u} v{v} 1 c_edge')
        safe_print('fix /./')

    def change_agent_status(self, agent):
        id_ = agent.id_

        if id_ not in self.defined_agents:
            return

        color = 'c_sus'

        if agent.mobility.wait:
            color = 'c_wait_sus'

        if hasattr(agent, 'state'):
            if agent.state == 'I':
                color = 'c_inf'
            elif agent.state == 'R':
                color = 'c_rec'
            elif agent.state == 'S':
                color = 'c_sus'

        safe_print(f'color agent{id_} {color}')
        safe_print(f'color agentr{id_} {color}_range')

    def display_agents(self):
        for agent in self.scheduler.agents:
            id_ = agent.id_
            p = agent.mobility.current
            x, y = to_geometry(p[0]), to_geometry(p[1])
            r = to_geometry(agent.range_)

            safe_print(f'define agent{id_} ellipse 4 4 white {x} {y}')
            safe_print(f'define agentr{id_} ellipse {r} {r} white {x} {y}')

            self.defined_agents.add(id_)
            self.change_agent_status(agent)

    def move_agent(self, agent):
        id_ = agent.id_

        if id_ not in self.defined_agents:
            return

        p = agent.mobility.current
        x, y = to_geometry(p[0]), to_geometry(p[1])

        safe_print(f'move agent{id_} {x} {y}')
        safe_print(f'move agentr{id_} {x} {y}')

        self.change_agent_status(agent)

    def display_status(self):
        time = float2str(self.scheduler.time, '10.2f')
        safe_print(f'define status_l text Time:{time} 14 white 0.5 0.05')

    def update(self):
        # ===== ここが追加部分 =====
        # 各時刻における感染者数を数える
        num_infected = 0
        for agent in self.scheduler.agents:
            if hasattr(agent, 'state') and agent.state == 'I':
                num_infected += 1

        # CSV 用出力（リダイレクト前提）
        print(f"STAT {self.scheduler.time} {num_infected}")
        # ==========================

        safe_print('display')
