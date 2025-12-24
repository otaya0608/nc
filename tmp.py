#!/usr/bin/env python3
# cell.py - きれいな表示 + ゾンビ対応 + BrokenPipe完全対策版

from dtnsim.monitor.null import Null
import sys

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except BrokenPipeError:
        sys.exit(0)

def float2str(v, fmt='9.3f'):
    astr = ('%' + fmt) % v
    astr = astr.replace(' ', '__')
    return astr

def to_geometry(v):
    return v / 1000

class Cell(Null):
    def open(self):
        # --- カラーパレット定義 ---
        safe_print('palette c_edge   heat10 .2')
        safe_print('palette c_vertex heat20 .9')

        safe_print('palette c_sus_range heat20 .3')
        safe_print('palette c_sus        heat20 .9')

        safe_print('palette c_inf_range heat80 .3')
        safe_print('palette c_inf        heat80 .9')

        safe_print('palette c_wait_sus_range heat20 .3')
        safe_print('palette c_wait_sus        heat20 .9')

        safe_print('palette c_zombie       red .9')
        safe_print('palette c_zombie_range red .3')

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

        # デフォルト（人間）
        color = 'c_sus'
        if agent.mobility.wait:
            color = 'c_wait_sus'
        if agent.received or agent.receive_queue:
            color = 'c_inf'

        # ゾンビ状態優先
        if hasattr(agent, 'state'):
            if agent.state == 'I':
                color = 'c_zombie'
            elif agent.state == 'R':
                color = 'c_edge'
            elif agent.state == 'S':
                color = 'c_sus'

        safe_print(f'color agent{id_} {color}')
        if '_sus' in color or '_inf' in color or '_zombie' in color:
            safe_print(f'color agentr{id_} {color}_range')
        else:
            safe_print(f'color agentr{id_} {color}')

    def display_agents(self):
        for agent in self.scheduler.agents:
            id_ = agent.id_
            p = agent.mobility.current
            x, y = to_geometry(p[0]), to_geometry(p[1])
            r = to_geometry(agent.range_)
            safe_print(f'define agent{id_} ellipse 4 4 white {x} {y}')
            safe_print(f'define agentr{id_} ellipse {r} {r} white {x} {y}')
            self.change_agent_status(agent)

    def move_agent(self, agent):
        id_ = agent.id_
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
            'define status_l text Time:{},____TX:{},____RX:{},____DUP:{},____Delivered:{}__/__{},____Arrived:{} 14 white 0.5 0.05'
            .format(time, tx, rx, dup, uniq_delivered_total, uniq_total, delivered_total)
        )

    def update(self):
        safe_print('display')
