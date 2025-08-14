# !/usr/bin/env python3 
import json
from datetime import datetime
from pathlib import Path
from statistics import mean
import argparse
import matplotlib.pyplot as plt
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC") 
KST = ZoneInfo("Asia/Seoul")

def parse_timestamp_utc(ts: str) -> datetime:
    if ts.endswith("Z"): ts = ts[:-1] 
    return datetime.fromisoformat(ts).replace(tzinfo=UTC)

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
    ts_utc = [parse_timestamp_utc(r["timestamp"]) for r in rows]
    cpu_max = max(cpu)
    mem_max = max(mem)
    disk_max = max(disk)

    cpu_max_t_utc = ts_utc[cpu.index(cpu_max)]
    mem_max_t_utc = ts_utc[mem.index(mem_max)]
    disk_max_t_utc = ts_utc[disk.index(disk_max)]

# KST로 변환
    cpu_max_t_kst = cpu_max_t_utc.astimezone(KST)
    mem_max_t_kst = mem_max_t_utc.astimezone(KST)
    disk_max_t_kst = disk_max_t_utc.astimezone(KST)
    return {
    "count": len(rows),

    "cpu_avg": round(mean(cpu), 2),
    "cpu_max": cpu_max,
    "cpu_max_time_utc": cpu_max_t_utc.isoformat(timespec="seconds"),
    "cpu_max_time_kst": cpu_max_t_kst.isoformat(timespec="seconds"),

    "mem_avg": round(mean(mem), 2),
    "mem_max": mem_max,
    "mem_max_time_utc": mem_max_t_utc.isoformat(timespec="seconds"),
    "mem_max_time_kst": mem_max_t_kst.isoformat(timespec="seconds"),

    "disk_avg": round(mean(disk), 2),
    "disk_max": disk_max,
    "disk_max_time_utc": disk_max_t_utc.isoformat(timespec="seconds"),
    "disk_max_time_kst": disk_max_t_kst.isoformat(timespec="seconds"),
    }


def plot(path: Path, out_dir: Path, tz: str = "kst"):
    rows = list(load_jsonl(path))
    if not rows:
        return None

    ts_utc = [parse_timestamp_utc(r["timestamp"]) for r in rows]
    cpu = [r["cpu_percent"] for r in rows]
    mem = [r["mem_percent"] for r in rows]
    disk = [r["disk_percent"] for r in rows]
    
    if tz.lower() == "utc":
        ts = ts_utc
        tz_label = "UTC"
        suffix = "-utc"
    else:
        ts = [t.astimezone(KST) for t in ts_utc]
        tz_label = "KST (UTC+9)"
        suffix = "-kst"

    out_dir.mkdir(parents=True, exist_ok=True)
    fig_path = out_dir / (path.stem + f"{suffix}.png")

    plt.figure(figsize=(9, 4))
    plt.plot(ts, cpu, label="CPU %")
    plt.plot(ts, mem, label="MEM %")
    plt.plot(ts, disk, label="DISK %")
    plt.legend()
    plt.title(f"System Metrics Over Time [{tz_label}]")
    plt.xlabel(f"Time ({tz_label})")
    plt.tight_layout()
    plt.savefig(fig_path)
    plt.close()

    return fig_path


def main():
    ap = argparse.ArgumentParser(description="일일 요약 리포트 생성(UTC/KST 지원)")
    ap.add_argument("--date", help="YYYYMMDD (기본: 오늘,UTC기준)", default=datetime.utcnow().strftime("%Y%m%d"))
    ap.add_argument("--in-dir", type=Path, default=Path("output"))
    ap.add_argument("--out-dir", type=Path, default=Path("reports"))
    ap.add_argument("--tz", choices=["utc", "kst"], default="kst", help="그래프 시간대(utc|kst), 기본 kst")
    args = ap.parse_args()

    in_path = args.in_dir / f"metrics-{args.date}.jsonl"
    if not in_path.exists():
        print(f"[정보] 입력 파일이 없습니다: {in_path}")
        return

    summary = summarize(in_path)
    if not summary:
        print("[정보] 데이터가 없습니다.")
        return

    print("[요약 - 공통 지표]")
    print(f"  수집 개수: {summary['count']}")
    print(f"  CPU 평균/최대: {summary['cpu_avg']} / {summary['cpu_max']}")
    print(f"  MEM 평균/최대: {summary['mem_avg']} / {summary['mem_max']}")
    print(f"  DISK 평균/최대: {summary['disk_avg']} / {summary['disk_max']}")
    
    print("[요약 - 시간(UTC/KST)]")
    print(f"  CPU 최대 시각: UTC {summary['cpu_max_time_utc']} | KST {summary['cpu_max_time_kst']}")
    print(f"  MEM 최대 시각: UTC {summary['mem_max_time_utc']} | KST {summary['mem_max_time_kst']}")
    print(f"  DISK 최대 시각: UTC {summary['disk_max_time_utc']} | KST {summary['disk_max_time_kst']}")
    
    
    fig = plot(in_path, args.out_dir, tz=args.tz)
    if fig:
        print(f"[정보] 그래프 저장: {fig}")

    fig_kst = plot(in_path, args.out_dir, tz="kst")
    fig_utc = plot(in_path, args.out_dir, tz="utc")
    print(f"[정보] 그래프(양쪽 시간대) 저장: {fig_kst}, {fig_utc}")

if __name__ == "__main__":
    main()
