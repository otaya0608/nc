#!/usr/bin/env python3
import csv
import subprocess
import statistics

# ==== 実験パラメータ ====
P_START = 0.0
P_END   = 1.0
P_STEP  = 0.05

TRIALS = 20

# dtnsim の時間（あなたの -L で止まる前提）
T_END = 200000

# 「最後の何割でI>0なら持続」と判定するか
TAIL_FRAC = 0.10

# dtnsim コマンド（あなたの実行形に合わせる）
BASE_CMD = [
    "dtnsim",
    "-s", "2",
    "-n", "20",
    "-m", "RandomWaypoint",
    "-p", "NONE",
    "-a", "Epidemic",
    "-c", "NONE",
    f"-L{T_END}",
]

def parse_stat(stderr_text: str):
    # (time, I) の配列にする
    out = []
    for line in stderr_text.splitlines():
        if not line.startswith("STAT "):
            continue
        _, t, I = line.split()
        out.append((float(t), int(I)))
    return out

def is_persistent(stats):
    if not stats:
        return False
    t_max = max(t for t, _ in stats)
    t_thr = t_max * (1.0 - TAIL_FRAC)
    # 後半区間でI>0が1回でもあれば「持続」
    for t, I in stats:
        if t >= t_thr and I > 0:
            return True
    return False

def frange(a, b, step):
    x = a
    # 浮動小数の誤差対策
    while x <= b + 1e-12:
        yield round(x, 10)
        x += step

def run_one(p):
    env = dict(**subprocess.os.environ)
    env["INFECTION_RATE"] = str(p)
    env["STAT_LOG"] = "1"

    r = subprocess.run(
        BASE_CMD,
        env=env,
        stdout=subprocess.DEVNULL,  # 出力不要
        stderr=subprocess.PIPE,      # STATはstderrに来る
        text=True
    )

    stats = parse_stat(r.stderr)
    return is_persistent(stats), stats

def main():
    with open("persist_rate.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["P", "persist_rate", "trials"])

        for p in frange(P_START, P_END, P_STEP):
            pers = 0
            for _ in range(TRIALS):
                ok, _stats = run_one(p)
                if ok:
                    pers += 1
            rate = pers / TRIALS
            print(f"P={p:.3f} persist_rate={rate:.3f} ({pers}/{TRIALS})")
            w.writerow([p, rate, TRIALS])

if __name__ == "__main__":
    main()
