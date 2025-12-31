#!/usr/bin/env python3
import csv
import numpy as np

from dtnsim.simulator import Simulator
from dtnsim.scheduler.simple import SimpleScheduler
from dtnsim.mobility.randomwalk import RandomWalk
from dtnsim.monitor.null import Null
from epidemic import Epidemic

# =====================
# 実験パラメータ
# =====================
P_LIST = np.arange(0.0, 1.01, 0.05)
N_TRIALS = 20
T_END = 200000

N_AGENT = 50
FIELD = 1000
RANGE = 50

# =====================
def run_once(P):
    Epidemic.INFECTION_RATE = P

    sim = Simulator()
    scheduler = SimpleScheduler(sim, delta=100)
    monitor = Null(sim)

    for i in range(N_AGENT):
        mob = RandomWalk(field=FIELD)
        Epidemic(
            scheduler=scheduler,
            mobility=mob,
            monitor=monitor,
            range_=RANGE
        )

    infected_persist = False

    while scheduler.time < T_END:
        scheduler.advance()

        # 後半10%で感染者が存在するか
        if scheduler.time > T_END * 0.9:
            I = sum(1 for a in scheduler.agents if getattr(a, 'state', None) == 'I')
            if I > 0:
                infected_persist = True
                break

    return infected_persist


def main():
    with open('threshold_result.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['P', 'persist_rate'])

        for P in P_LIST:
            count = 0
            for _ in range(N_TRIALS):
                if run_once(P):
                    count += 1

            rate = count / N_TRIALS
            print(f'P={P:.2f}  persist={rate:.2f}')
            writer.writerow([P, rate])


if __name__ == '__main__':
    main()
