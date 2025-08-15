# !/usr/bin/env python3 
import json
# json = 컴퓨터 프로그램의 변수값을 표현
from datetime import datetime
# from pathlib import Path =파일과 디렉터리 경로를 다룰 때 더 직관적이고 안전한 객체 지향 방식
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


def summarize_processes(path: Path) -> dict: 
    data = {} 
    for row in load_jsonl(path):
        for p in row.get("processes", []): 
            name = p.get("name") or "unknown" 
            entry = data.setdefault(name, {"cpu": [], "mem": [], "count": 0})
            entry["cpu"].append(float(p.get("cpu") or 0.0))
            entry["mem"].append(float(p.get("mem") or 0.0))
            entry["count"] += 1



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

    plt.figure(figsize=(10, 4), dpi=120)
    plt.plot(ts, cpu, label="CPU 사용률(%)",color = "#ff6b6b",linewidth =2)
    plt.plot(ts, mem, label="MEM 사용률(%)",color = "#4dabf7",linewidth =2)
    plt.plot(ts, disk, label="DISK 사용률(%)",color = "#94d82d",linewidth = 2)
    plt.grid(True,alpha =0.3, linestyle = "--",linewidth=0.7)
    plt.legend(loc = "upper left", frameon = False)
    plt.title(f"시스템 자원 추이 [{tz_label}]")
    plt.xlabel(f"시간 ({tz_label})")
    plt.ylabel("사용률(%)")
    plt.tight_layout()
    plt.savefig(fig_path)
    plt.close()

    return fig_path

def print_top_processes(items: list[dict], key: str = "cpu_avg", top: int = 10): 
    key_label = "CPU 평균" if key == "cpu_avg" else "메모리 평균" 
    items = sorted(items, key=lambda x: x[key], reverse=True)[:top] 
    print(f"[프로세스 요약 - TOP {top} ({key_label} 기준)]")
    for i, it in enumerate(items, 1):
        print(f"{i:>2}) {it['name']:<20} | CPU {it['cpu_avg']:>5.1f}% | MEM {it['mem_avg']:>5.1f}% | 등장 {it['count']:>3}회")

def plot_proc_bars(items: list[dict], out_dir: Path, date_str: str):
    out_dir.mkdir(parents=True, exist_ok=True)

# CPU 평균 Top10
    cpu_top = sorted(items, key=lambda x: x["cpu_avg"], reverse=True)[:10]
    names = [x["name"] for x in cpu_top]
    cpu_vals = [x["cpu_avg"] for x in cpu_top]
    plt.figure(figsize=(10, 5), dpi=120)
    plt.barh(names[::-1], cpu_vals[::-1], color="#ff922b")
    plt.xlabel("CPU 평균(%)")
    plt.title("프로세스 TOP10 (CPU 평균 기준)")
    plt.tight_layout()
    cpu_path = out_dir / f"proc-top-cpu-{date_str}.png"
    plt.savefig(cpu_path)
    plt.close()

# 메모리 평균 Top10
    mem_top = sorted(items, key=lambda x: x["mem_avg"], reverse=True)[:10]
    names = [x["name"] for x in mem_top]
    mem_vals = [x["mem_avg"] for x in mem_top]
    plt.figure(figsize=(10, 5), dpi=120)
    plt.barh(names[::-1], mem_vals[::-1], color="#4263eb")
    plt.xlabel("메모리 평균(%)")
    plt.title("프로세스 TOP10 (메모리 평균 기준)")
    plt.tight_layout()
    mem_path = out_dir / f"proc-top-mem-{date_str}.png"
    plt.savefig(mem_path)
    plt.close()

    return cpu_path, mem_path



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
    
    fig_req = plot(in_path, args.out_dir, tz=args.tz)
    fig_kst = plot(in_path, args.out_dir, tz="kst")
    fig_utc = plot(in_path, args.out_dir, tz="utc")
    if fig_req:
        print(f"[정보] 라인 그래프 저장: {fig_req}")
        print(f"[정보] 라인 그래프(추가): {fig_kst}, {fig_utc}")
        
    proc_items = summarize_processes(in_path)
    if proc_items:
        print_top_processes(proc_items, key="cpu_avg", top=10)
        print_top_processes(proc_items, key="mem_avg", top=10)
        cpu_bar, mem_bar = plot_proc_bars(proc_items, args.out_dir, args.date)
        print(f"[정보] 프로세스 그래프 저장: {cpu_bar}, {mem_bar}")
    else:
        print("[정보] 프로세스 데이터가 없어 요약/그래프를 건너뜁니다.")        

if __name__ == "__main__":
    main()
