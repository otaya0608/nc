#!/usr/bin/env python3
# carryonly.py (基本機能版)
from collections import defaultdict
import math
from perlcompat import die

MAX_RANGE = 50

class CarryOnly():
    def __init__(self, id_=None, scheduler=None, mobility=None, monitor=None, range_=50):
        if id_ is None: id_ = len(scheduler.agents) + 1
        if not scheduler: die("Scheduler class must be specified.")
        if not mobility: die("Mobility class must be specified.")
        if not monitor: die("Monitor class must be specified.")
        if range_ > MAX_RANGE: die(f"range cannot exceed MAX_RANGE ({MAX_RANGE})")
        self.id_ = id_
        self.scheduler = scheduler
        self.mobility = mobility
        self.monitor = monitor
        self.range_ = range_

        self.last_neighbors = []
        self.received = defaultdict(int)
        self.receive_queue = defaultdict(int)
        self.delivered = defaultdict(int)
        self.tx_count = 0
        self.rx_count = 0
        self.dup_count = 0

        self.scheduler.add_agent(self)

    # ゾンビ機能で上書きするための空メソッド
    def update_color(self):
        pass

    def msg_src(self, msg): return int(msg.split('-')[0])
    def msg_dst(self, msg): return int(msg.split('-')[1])
    def msg_id(self, msg): return int(msg.split('-')[2])

    def zone(self, x=None, y=None):
        if x is None: x = self.mobility.current[0]
        if y is None: y = self.mobility.current[1]
        i = max(0, int(x / MAX_RANGE))
        j = max(0, int(y / MAX_RANGE))
        return i, j

    def cache_zone(self):
        i, j = self.zone()
        self.scheduler.zone_cache.setdefault(j, {}).setdefault(i, []).append(self)

    # 確実に周囲を検知できるように修正した neighbors
    def neighbors(self):
        cache = self.scheduler.zone_cache
        if not cache: die("update_zone() must have been called for zone caching.")
        p = self.mobility.current
        i, j = self.zone()
        neighbors = []
        for dj in [-1, 0, 1]:
            if j + dj < 0: continue
            for di in [-1, 0, 1]:
                if i + di < 0: continue
                if not cache.get(j + dj, None): continue
                if not cache[j + dj].get(i + di, None): continue
                for agent in self.scheduler.zone_cache[j + dj][i + di]:
                    if agent == self: continue
                    q = agent.mobility.current
                    if (p[0]-q[0])**2 + (p[1]-q[1])**2 <= self.range_**2:
                        neighbors.append(agent)
        return neighbors

    def encounters(self):
        neighbors = self.neighbors()
        encounters = {agent.id_: agent for agent in neighbors}
        for agent in self.last_neighbors:
            if agent.id_ in encounters:
                del encounters[agent.id_]
        self.last_neighbors = neighbors
        return list(encounters.values())

    def sendmsg(self, agent, msg):
        agent.recvmsg(self, msg)
        self.tx_count += 1
        self.monitor.display_forward(self, agent, msg)
        self.monitor.change_agent_status(self)

    def recvmsg(self, agent, msg):
        self.receive_queue[msg] += 1
        self.rx_count += 1
        if msg in self.received: self.dup_count += 1
        self.monitor.change_agent_status(self)
        self.update_color() # 色更新フック

    def messages(self): return [msg for msg in self.received if self.received[msg] > 0]
    def pending_messages(self): return [msg for msg in self.messages() if self.msg_dst(msg) != self.id_ and msg not in self.delivered]

    def forward(self):
        # 標準的なCarryOnlyの動作（Epidemic側で完全に上書きする）
        encounters = self.encounters()
        for agent in encounters:
            for msg in self.pending_messages():
                if agent.id_ == self.msg_dst(msg):
                    self.sendmsg(agent, msg)
                    del self.received[msg]
                    self.delivered[msg] += 1

    def advance(self):
        self.mobility.move(self.scheduler.delta)
        self.monitor.move_agent(self)
        self.forward()

    def flush(self):
        for msg in list(self.receive_queue.keys()):
            self.received[msg] += self.receive_queue[msg]
            del self.receive_queue[msg]