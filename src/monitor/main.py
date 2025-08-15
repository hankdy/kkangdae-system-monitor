#!/usr/bin/env python3
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
import psutil
from typing import Optional; import yaml
from typing import List, Dict


def get_top_processes(n: int = 5, by: str = "cpu") -> List[Dict]: 
    procs : List[Dict] = [] 
    for p in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent"]): 
        info = p.info 
        procs.append({ "pid": int(info.get("pid", 0)),
                        "name": (info.get("name") or "unknown"),
                        "cpu": float(info.get("cpu_percent") or 0.0), 
                        "mem": float(info.get("memory_percent") or 0.0),
                        }) 
        key = "cpu" if by.lower() == "cpu" else "mem"
    
        procs.sort(key=lambda x: x[key], reverse=True) 
        return procs[:n]


def collect_metrics(top_n: int = 5, top_by: str = "cpu") -> dict:
    return {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "cpu_percent": psutil.cpu_percent(interval=None),
        "mem_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "processes": get_top_processes(n=top_n,by=top_by),
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
    top_n: int = 5,
    top_by: str = "cpu",
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    date = datetime.utcnow().strftime("%Y%m%d")
    out_path = out_dir / f"metrics-{date}.jsonl"

    end_ts = time.time() + duration
    while time.time() < end_ts:
        m = collect_metrics(top_n=top_n, top_by=top_by)

# with ~ as ~ 오픈된 파일을 자동으로 닫아줄때 사용
        with out_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

# alert(경고) 라는 변수에 상단 def run() 값보다 percent 값이 클 경우 경고 표시가 날수 있게 지정
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

# 설정값 변경시 사용
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="간단 시스템 모니터링 에이전트")
    p.add_argument("--config", type=Path, default=Path("config.yaml"),help="설정 파일 경로")
    p.add_argument("--interval", type=int, default=5, help="수집 주기(초)")
    p.add_argument("--duration", type=int, default=30, help="총 실행 시간(초)")
    p.add_argument("--out-dir", type=Path, default=Path("output"), help="출력 폴더 경로")
    p.add_argument("--top-n", type=int, default=5, help="수집할 상위 프로세스 개수")
    p.add_argument("--top-by", choices=["cpu", "mem"], default="cpu", help="상위 선별 기준(cpu|mem)")
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

    run(args.interval, args.duration, args.out_dir, top_n=args.top_n, top_by=args.top_by)


if __name__ == "__main__":
    main()

