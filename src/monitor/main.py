#!/usr/bin/env python3
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
import psutil
from typing import Optional; import yaml

def collect_metrics() -> dict:
    return {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "cpu_percent": psutil.cpu_percent(interval=None),
        "mem_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
    }

def load_config(path: Path) -> dict:
    """지정한 경로의 YAML 설정 파일을 로드하여 dict로 반환"""
    if not path.exists():
        return {}
    
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


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
    p.add_argument("--config", type=Path, default=Path("config.yaml"),help="설정 파일 경로")
    p.add_argument("--interval", type=int, default=5, help="수집 주기(초)")
    p.add_argument("--duration", type=int, default=30, help="총 실행 시간(초)")
    p.add_argument("--out-dir", type=Path, default=Path("output"), help="출력 폴더 경로")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    interval = int(cfg.get("interval", args.interval)) 
    duration = int(cfg.get("duration", args.duration)) 
    out_dir = Path(cfg.get("out_dir", args.out_dir)) 
    cpu_thr = float(cfg.get("cpu_threshold", 85.0)) 
    mem_thr = float(cfg.get("mem_threshold", 85.0)) 
    disk_thr = float(cfg.get("disk_threshold", 90.0))

    run(interval=interval, duration=duration, out_dir=out_dir, cpu_thr=cpu_thr, mem_thr=mem_thr, disk_thr=disk_thr)


if __name__ == "__main__":
    main()

