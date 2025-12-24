#!/usr/bin/env python3
# cell.py - SIR/Epidemic 完全対応・BrokenPipe対策済み版

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
        # ★ define 済み agent 管理
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

        # ★ 未定義 agent は触らない
        if id_ not in self.defined_agents:
            return

        # --- デフォルト ---
        color = 'c_sus'

        if agent.mobility.wait:
            color = 'c_wait_sus'

        # --- epidemic state 優先 ---
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

            # ★ define を必ず最初に出す
            safe_print(f'define agent{id_} ellipse 4 4 white {x} {y}')
            safe_print(f'define agentr{id_} ellipse {r} {r} white {x} {y}')

            # ★ 定義済み登録
            self.defined_agents.add(id_)

            self.change_agent_status(agent)

    def move_agent(self, agent):
        id_ = agent.id_

        # ★ 未定義 agent を move / color しない
        if id_ not in self.defined_agents:
            return

        p = agent.mobility.current
        x, y = to_geometry(p[0]), to_geometry(p[1])

        safe_print(f'move agent{id_} {x} {y}')
        safe_print(f'move agentr{id_} {x} {y}')

        self.change_agent_status(agent)

    def display_status(self):
        time = float2str(self.scheduler.time, '10.2f')
        tx = float2str(self.tx_total, '10g')
        rx = float2str(self.rx_total, '10g')
        dup = float2str(self.dup_total, '10g')
        uniq_total = float2str(self.uniq_total, '10g')
        delivered_total = float2str(self.delivered_total, '10g')
        uniq_delivered_total = float2str(self.uniq_delivered_total, '10g')

        safe_print(
            f'define status_l text '
            f'Time:{time},____TX:{tx},____RX:{rx},____DUP:{dup},'
            f'____Delivered:{uniq_delivered_total}__/__{uniq_total},'
            f'____Arrived:{delivered_total} '
            f'14 white 0.5 0.05'
        )

    def update(self):
        safe_print('display')
