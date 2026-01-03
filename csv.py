#!/usr/bin/env python3
import os
import subprocess

# ====== まずは死なない設定（ここ重要） ======
P_VALUES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]  # まず粗く確認
TRIALS = 1                                 # まず1回で動作確認
TAIL_FRAC = 0.20                           # 後半20%で判定

# dtnsimを軽くする（ここを小さくするとSIGKILLしにくい）
N_AGENTS = 20
SEED_BASE = 1

BASE_CMD = [
    "dtnsim",
    "-s", "1",
    "-n", str(N_AGENTS),
    "-m", "RandomWaypoint",
    "-p", "NONE",
    "-a", "Epidemic",
    "-M", "StatNull",
]

def parse_stat(stderr_text: str):
    out = []
    for line in stderr_text.splitlines():
        if not line.startswith("STAT "):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        # STAT <time> <I>
        t = float(parts[1])
        I = int(parts[2])
        out.append((t, I))
    return out

def is_persistent(stats):
    if not stats:
        return False
    t_max = stats[-1][0]
    t_thr = t_max * (1.0 - TAIL_FRAC)
    for t, I in stats:
        if t >= t_thr and I > 0:
            return True
    return False

def run_one(p, seed):
    env = os.environ.copy()
    env["INFECTION_RATE"] = str(p)
    env["STAT_LOG"] = "1"

    # seedを変えるなら -s を差し替える（dtnsimの引数は配列なので安全）
    cmd = BASE_CMD.copy()
    cmd[cmd.index("-s") + 1] = str(seed)

    r = subprocess.run(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,  # ← ここ超重要：無限に重くなる前に止める
    )

    stats = parse_stat(r.stderr)
    return is_persistent(stats), stats

def main():
    print("P,trial,persist,last_t,last_I")

    for p in P_VALUES:
        for k in range(TRIALS):
            seed = SEED_BASE + k
            try:
                ok, stats = run_one(p, seed)
            except subprocess.TimeoutExpired:
                # 重くて終わらないときはこの試行は「不明」扱いにして表示
                print(f"{p},{k+1},TIMEOUT,NA,NA")
                continue

            if not stats:
                print(f"{p},{k+1},NO_STAT,NA,NA")
                continue

            last_t, last_I = stats[-1]
            persist = 1 if ok else 0
            print(f"{p},{k+1},{persist},{int(last_t)},{last_I}")

if __name__ == "__main__":
    main()
