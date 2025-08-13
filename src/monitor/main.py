#!/usr/bin/env python3
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
import psutil


def collect_metrics() -> dict:
    return {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "cpu_percent": psutil.cpu_percent(interval=None),
        "mem_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
    }


def run(
    interval: int,
    duration: int,
    out_dir: Path,
    cpu_thr: float = 85.0,
    mem_thr: float = 85.0,
    disk_thr: float = 90.0,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    date = datetime.utcnow().strftime("%Y%m%d")
    out_path = out_dir / f"metrics-{date}.jsonl"

    end_ts = time.time() + duration
    while time.time() < end_ts:
        m = collect_metrics()

        with out_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

        alert = (
            m["cpu_percent"] > cpu_thr
            or m["mem_percent"] > mem_thr
            or m["disk_percent"] > disk_thr
        )

        if alert:
            print(f"[경고] 임계치 초과: {m}")
        else:
            print(f"[정보] 수집 완료: {m}")

        time.sleep(interval)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="간단 시스템 모니터링 에이전트")
    p.add_argument("--interval", type=int, default=5, help="수집 주기(초)")
    p.add_argument("--duration", type=int, default=30, help="총 실행 시간(초)")
    p.add_argument("--out-dir", type=Path, default=Path("output"), help="출력 폴더 경로")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    run(args.interval, args.duration, args.out_dir)


if __name__ == "__main__":
    main()

