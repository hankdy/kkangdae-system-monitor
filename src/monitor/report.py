# !/usr/bin/env python3 
import json
from datetime import datetime
from pathlib import Path
from statistics import mean
import argparse
import matplotlib.pyplot as plt


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def summarize(path: Path) -> dict:
    rows = list(load_jsonl(path))
    if not rows:
        return {}

    cpu = [r["cpu_percent"] for r in rows]
    mem = [r["mem_percent"] for r in rows]
    disk = [r["disk_percent"] for r in rows]

    return {
        "count": len(rows),
        "cpu_avg": round(mean(cpu), 2),
        "cpu_max": max(cpu),
        "mem_avg": round(mean(mem), 2),
        "mem_max": max(mem),
        "disk_avg": round(mean(disk), 2),
        "disk_max": max(disk),
    }


def plot(path: Path, out_dir: Path):
    rows = list(load_jsonl(path))
    if not rows:
        return None

    ts = [datetime.fromisoformat(r["timestamp"].replace("Z", "")) for r in rows]
    cpu = [r["cpu_percent"] for r in rows]
    mem = [r["mem_percent"] for r in rows]
    disk = [r["disk_percent"] for r in rows]

    out_dir.mkdir(parents=True, exist_ok=True)
    fig_path = out_dir / (path.stem + ".png")

    plt.figure(figsize=(9, 4))
    plt.plot(ts, cpu, label="CPU %")
    plt.plot(ts, mem, label="MEM %")
    plt.plot(ts, disk, label="DISK %")
    plt.legend()
    plt.title("System Metrics Over Time")
    plt.tight_layout()
    plt.savefig(fig_path)
    plt.close()

    return fig_path


def main():
    ap = argparse.ArgumentParser(description="일일 요약 리포트 생성")
    ap.add_argument("--date", help="YYYYMMDD (기본: 오늘)", default=datetime.utcnow().strftime("%Y%m%d"))
    ap.add_argument("--in-dir", type=Path, default=Path("output"))
    ap.add_argument("--out-dir", type=Path, default=Path("reports"))
    args = ap.parse_args()

    in_path = args.in_dir / f"metrics-{args.date}.jsonl"
    if not in_path.exists():
        print(f"[정보] 입력 파일이 없습니다: {in_path}")
        return

    summary = summarize(in_path)
    if not summary:
        print("[정보] 데이터가 없습니다.")
        return

    print("[요약]", summary)
    fig = plot(in_path, args.out_dir)
    if fig:
        print(f"[정보] 그래프 저장: {fig}")


if __name__ == "__main__":
    main()
