import paramiko
from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Dict, Tuple

# ----------------- Auth & Base Path -----------------
username = "admin"
password = "1Net@5cG2024"

base_dir = Path(r"C:\Users\Administrator\Desktop\Backup-STP_VLAN_MAC-address-Day")
base_dir.mkdir(parents=True, exist_ok=True)

# ----------------- Device groups -----------------
DEVICE_GROUPS: Dict[str, Dict[str, str]] = {
    "B1": {
        "172.23.84.43": "SCG-BS-S-B1-FL01-24G-01",
        "172.23.84.44": "SCG-BS-S-B1-FL02-24G-01",
    },
    "B17": {"172.23.84.39": "SCG-BS-N-B17-FL02-24G-01"},
    "B18": {"172.23.84.62": "SCG-BS-S-B18-FL01-24G-01"},
    "B19": {
        "172.23.84.63": "SCG-BS-S-B19-FL01-24G-01",
        "172.23.84.64": "SCG-BS-S-B19-FL02-24G-01",
    },
    "B19_1": {"172.23.84.65": "SCG-BS-S-B19_1-FL01-24G-01"},
    "B1A": {"172.23.84.45": "SCG-BS-S-B1A-FL01-48G-01"},
    "B2": {
        "172.23.84.46": "SCG-BS-S-B2-FL01-24G-01",
        "172.23.84.47": "SCG-BS-S-B2-FL02-24G-01",
        "172.23.84.48": "SCG-BS-S-B2-FL03-24G-01",
        "172.23.84.49": "SCG-BS-S-B2-FL04-24G-01",
    },
    "B20": {"172.23.84.66": "SCG-BS-S-B20-FL01-24G-01"},
    "B21_1": {"172.23.84.67": "SCG-BS-S-B21_1-FL02-24G-01"},
    "B21_2": {
        "172.23.84.68": "SCG-BS-S-B21_2-FL01-24G-01",
        "172.23.84.69": "SCG-BS-S-B21_2-FL02-24G-01",
    },
    "B22_1": {"172.23.84.70": "SCG-BS-S-B22_1-FL01-24G-01"},
    "B22_4": {"172.23.84.71": "SCG-BS-S-B22_4-FL02-24G-01"},
    "B23": {
        "172.23.84.72": "SCG-BS-S-B23-FL01-24G-01",
        "172.23.84.73": "SCG-BS-S-B23-FL02-24G-01",
    },
    "B23A": {"172.23.84.74": "SCG-BS-S-B23A-FL01-24G-01"},
    "B24_1": {"172.23.84.75": "SCG-BS-S-B24_1-FL01-24G-01"},
    "B24_2": {"172.23.84.76": "SCG-BS-S-B24_2-FL01-24G-01"},
    "B25": {"172.23.84.77": "SCG-BS-S-B25-FL01-24G-01"},
    "B26": {"172.23.84.78": "SCG-BS-S-B26-FL01-48G-01"},
    "B26A": {"172.23.84.79": "SCG-BS-S-B26A-FL01-24G-01"},
    "B27": {"172.23.84.80": "SCG-BS-S-B27-FL01-48G-01"},
    "B28": {"172.23.84.81": "SCG-BS-S-B28-FL01-24G-01"},
    "B29": {"172.23.84.82": "SCG-BS-S-B29-FL01-24G-01"},
    "B3": {
        "172.23.84.50": "SCG-BS-S-B3-FL01-24G-01",
        "172.23.84.51": "SCG-BS-S-B3-FL02-24G-01",
        "172.23.84.52": "SCG-BS-S-B3-FL03-24G-01",
        "172.23.84.53": "SCG-BS-S-B3-FL04-48G-01",
    },
    "B30B": {"172.23.84.83": "SCG-BS-S-B30B-FL01-24G-01"},
    "B30C": {"172.23.84.84": "SCG-BS-S-B30C-FL01-24G-01"},
    "B30D": {"172.23.84.85": "SCG-BS-S-B30D-FL01-48G-01"},
    "B31": {"172.23.84.86": "SCG-BS-S-B31-FL01-24G-01"},
    "B32": {"172.23.84.87": "SCG-BS-S-B32-FL02-24G-01"},
    "B34": {"172.23.84.88": "SCG-BS-S-B34-FL02-24G-01"},
    "B37": {"172.23.84.89": "SCG-BS-S-B37-FL01-24G-01"},
    "B4": {
        "172.23.84.54": "SCG-BS-S-B4-FL01-24G-01",
        "172.23.84.55": "SCG-BS-S-B4-FL02-24G-01",
        "172.23.84.56": "SCG-BS-S-B4-FL03-24G-01",
        "172.23.84.57": "SCG-BS-S-B4-FL04-48G-01",
        "172.23.84.58": "SCG-BS-S-B4-FL05-24G-01",
        "172.23.84.59": "SCG-BS-S-B4-FL06-48G-01",
        "172.23.84.60": "SCG-BS-S-B4-FL07-24G-01",
        "172.23.84.61": "SCG-BS-S-B4-FL08-24G-01",
    },
    "B5": {
        "172.23.84.31": "SCG-BS-N-B5-FL02-48G-01",
        "172.23.84.32": "SCG-BS-N-B5-FL03-24G-01",
        "172.23.84.33": "SCG-BS-N-B5-FL04-24G-01",
        "172.23.84.34": "SCG-BS-N-B5-FL05-24G-01",
    },
    "B8": {"172.23.84.35": "SCG-BS-N-B8-FL01-24G-01"},
    "B9": {
        "172.23.84.36": "SCG-BS-N-B9-FL01-24G-01",
        "172.23.84.37": "SCG-BS-N-B9-FL02-24G-01",
    },
    "Canteen1": {"172.23.84.93": "SCG-BS-N-canteen1-FL01-24G-01"},
    "Canteen4": {"172.23.84.90": "SCG-BS-S-Canteen4-FL01-24G-01"},
    "CarPark3": {"172.23.84.91": "SCG-BS-S-CarPark3-FL01-24G-01"},
    "ChangDee": {"172.23.84.92": "SCG-BS-S-Naichangdee-FL01-24G-01"},
    "Gate_1": {"172.23.84.40": "SCG-BS-N-Gate_1-FL01-24G-01"},
    "HC": {"172.22.252.34": "SCG-BS-N-HC-FL04-48G-01"},
    "HO1": {
        "172.23.84.6": "SCG-BS-N-HO1-FLM-48G-01",
        "172.23.84.7": "SCG-BS-N-HO1-FL01-48G-01",
        "172.23.84.8": "SCG-BS-N-HO1-FL02-48G-01",
        "172.23.84.9": "SCG-BS-N-HO1-FL03-24G-01",
        "172.23.84.10": "SCG-BS-N-HO1-FL04-48G-01",
        "172.23.84.11": "SCG-BS-N-HO1-FL05-48G-01",
        "172.23.84.12": "SCG-BS-N-HO1-FL06-48G-01",
        "172.23.84.13": "SCG-BS-N-HO1-FL07-48G-01",
        "172.23.84.14": "SCG-BS-N-HO1-FL08-48G-01",
        "172.23.84.15": "SCG-BS-N-HO1-FL09-48G-01",
        "172.23.84.16": "SCG-BS-N-HO1-FL10-48G-01",
        "172.23.84.17": "SCG-BS-N-HO1-FL11-48G-01",
        "172.23.84.94": "SCG-BS-N-HO1-FL01-48G-02",
        "172.23.84.95": "SCG-BS-N-HO1-FL10-48G-02",
        "172.23.84.96": "SCG-BS-N-HO1-FL11-48G-02",
    },
    "HO2": {
        "172.23.84.18": "SCG-BS-N-HO2-FLM-48G-01",
        "172.23.84.19": "SCG-BS-N-HO2-FL01-24G-01",
        "172.23.84.20": "SCG-BS-N-HO2-FL02-48G-01",
        "172.23.84.21": "SCG-BS-N-HO2-FL03-48G-01",
        "172.23.84.22": "SCG-BS-N-HO2-FL04-48G-01",
        "172.23.84.23": "SCG-BS-N-HO2-FL05-48G-01",
        "172.23.84.24": "SCG-BS-N-HO2-FL06-48G-01",
        "172.23.84.25": "SCG-BS-N-HO2-FL07-48G-01",
        "172.23.84.26": "SCG-BS-N-HO2-FL08-48G-01",
        "172.23.84.27": "SCG-BS-N-HO2-FL09-48G-01",
        "172.23.84.28": "SCG-BS-N-HO2-FL10-48G-01",
        "172.23.84.29": "SCG-BS-N-HO2-FL11-48G-01",
        "172.23.84.30": "SCG-BS-N-HO2-FL12-48G-01",
        "172.23.84.97": "SCG-BS-N-HO2-FL12-48G-02",
    },
    "HO3": {
        "172.22.252.6": "SCG-BS-N-HO3-FLM-48G-01",
        "172.22.252.7": "SCG-BS-N-HO3-FLM-48G-02",
        "172.22.252.8": "SCG-BS-N-HO3-FL01-48G-01",
        "172.22.252.9": "SCG-BS-N-HO3-FL02-48G-01",
        "172.22.252.10": "SCG-BS-N-HO3-FL03-48G-01",
        "172.22.252.11": "SCG-BS-N-HO3-FL04-48G-01",
        "172.22.252.12": "SCG-BS-N-HO3-FL05-48G-01",
        "172.22.252.13": "SCG-BS-N-HO3-FL06-48G-01",
        "172.22.252.14": "SCG-BS-N-HO3-FL07-48G-01",
        "172.22.252.15": "SCG-BS-N-HO3-FL08-48G-01",
        "172.22.252.16": "SCG-BS-N-HO3-FL09-48G-01",
        "172.22.252.17": "SCG-BS-N-HO3-FL10-48G-01",
        "172.22.252.18": "SCG-BS-N-HO3-FL11-48G-01",
        "172.22.252.19": "SCG-BS-N-HO3-FL12-48G-01",
        "172.22.252.20": "SCG-BS-N-HO3-FL13-48G-01",
        "172.22.252.21": "SCG-BS-N-HO3-FL14-48G-01",
        "172.22.252.22": "SCG-BS-N-HO3-FL15-48G-01",
        "172.22.252.23": "SCG-BS-N-HO3-FL16-48G-01",
        "172.22.252.24": "SCG-BS-N-HO3-FL17-48G-01",
        "172.22.252.25": "SCG-BS-N-HO3-FL18-48G-01",
        "172.22.252.26": "SCG-BS-N-HO3-FL19-48G-01",
        "172.22.252.27": "SCG-BS-N-HO3-FL20-48G-01",
        "172.22.252.28": "SCG-BS-N-HO3-FL21-48G-01",
        "172.22.252.36": "SCG-BS-100Y-HO3-FL01-24G-02",
    },
    "MPP": {
        "172.22.252.29": "SCG-BS-N-MPP-FL01-24G-01",
        "172.22.252.30": "SCG-BS-N-MPP-FL03-24G-01",
        "172.22.252.31": "SCG-BS-N-MPP-FL06-24G-01",
        "172.22.252.32": "SCG-BS-N-MPP-FL08-24G-01",
        "172.22.252.33": "SCG-BS-N-MPP-FL10-48G-01",
        "172.22.252.35": "SCG-BS-100Y-MPP-FL10-24G-02",
    },
    "SportCenter": {"172.23.84.42": "SCG-BS-N-SportCenter-FL04-24G-01"},
    "Tennis": {"172.23.84.41": "SCG-BS-N-Tennis-FL01-24G-01"},
    "B17": {"172.23.84.38": "SCG-BS-N-B17-FL01-48G-01"},
}

# ----------------- Commands -----------------
PRE_COMMANDS = ["no page"]
COMMANDS = [
    "show spanning-tree summary root",
    "show mac-address-table",
    "show int lag 1",
    "show lacp aggregates",
]

SSH_CONNECT_TIMEOUT = 20
CMD_TIMEOUT = 180
RETRIES = 2

# ----------------- SSH helper -----------------
def ssh_run_multi(host: str) -> Tuple[bool, Dict[str, str]]:
    outputs: Dict[str, str] = {}
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host,
            username=username,
            password=password,
            look_for_keys=False,
            allow_agent=False,
            timeout=SSH_CONNECT_TIMEOUT,
        )
        # ปิด paging (ถ้าไม่รองรับจะเงียบ)
        for pc in PRE_COMMANDS:
            try:
                _in, _out, _err = client.exec_command(pc, timeout=10)
                _ = _out.read(); _ = _err.read()
            except Exception:
                pass

        # คำสั่งหลัก + รีทราย
        for c in COMMANDS:
            last_err = None
            for attempt in range(1, RETRIES + 1):
                try:
                    stdin, stdout, stderr = client.exec_command(c, timeout=CMD_TIMEOUT)
                    out = stdout.read().decode(errors="ignore")
                    err = stderr.read().decode(errors="ignore")
                    outputs[c] = (out + ("\n" + err if err else "")).strip() or "(no output)"
                    break
                except Exception as e:
                    last_err = f"[attempt {attempt}/{RETRIES}] {type(e).__name__}: {e}"
                    outputs[c] = f"[ERROR while running '{c}'] {last_err}"
        return True, outputs

    except Exception as e:
        return False, {"connection": f"[ERROR] {type(e).__name__}: {e}"}
    finally:
        try:
            if client:
                client.close()
        except Exception:
            pass

# ----------------- Save helper -----------------
def today_group_dir(group: str) -> Path:
    day_dir = base_dir / datetime.now().strftime("%Y-%m-%d") / group
    day_dir.mkdir(parents=True, exist_ok=True)
    return day_dir

def save_txt(group: str, device_name: str, ip: str, cmd_outputs: Dict[str, str]) -> Path:
    """เซฟเป็น <DeviceName>-YYYY-MM-DD.txt ภายใต้โฟลเดอร์วันที่/อาคาร (append)."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = today_group_dir(group) / f"{device_name}-{date_str}.txt"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [f"[{ts}]  {device_name} ({ip})"]
    for cmd in COMMANDS:
        lines.append(f"\n>>> {cmd}")
        lines.append(cmd_outputs.get(cmd, "(no output)"))
    content = "\n".join(lines).rstrip() + "\n\n"

    with path.open("a", encoding="utf-8") as f:
        f.write(content)
    return path

# ----------------- One-round job -----------------
def ip_sort_key(ip: str):
    try:
        return tuple(map(int, ip.split(".")))
    except Exception:
        return (999, 999, 999, 999)

def run_one_round():
    print(f"Start @ {datetime.now():%Y-%m-%d %H:%M:%S}")
    for group in sorted(DEVICE_GROUPS.keys(), key=lambda s: s.lower()):
        mapping = DEVICE_GROUPS[group]
        for ip in sorted(mapping.keys(), key=ip_sort_key):
            name = mapping[ip]
            print(f"- {group} | {name} ({ip}) ...")
            ok, outputs = ssh_run_multi(ip)
            p = save_txt(group, name, ip, outputs)
            print(f"  -> saved: {p}")
    print("Round done.")

# ----------------- Scheduling config -----------------
# โหมดตั้งเวลา: ให้รันทุกวันตามชั่วโมงที่กำหนด
MODE = "daily"               # <-- แก้เป็น daily
RUN_HOURS = [17]             # รันเวลา 17:00 ของทุกวัน (ใช้ชั่วโมง 24 ชม.)
RUN_IMMEDIATELY = False      # ถ้าอยากให้รันทันทีหนึ่งครั้งตอนเริ่ม ให้เปลี่ยนเป็น True

def seconds_until_next_run() -> int:
    now = datetime.now()
    if MODE.lower() == "interval":
        # เผื่ออนาคตถ้าสลับกลับไปโหมด interval
        INTERVAL_MIN = 30
        return max(1, INTERVAL_MIN * 60)
    else:
        today_times = [
            now.replace(hour=h, minute=0, second=0, microsecond=0) for h in sorted(RUN_HOURS)
        ]
        for t in today_times:
            if now < t:
                return max(1, int((t - now).total_seconds()))
        # ข้ามไปเวลานัดแรกของวันถัดไป
        t = today_times[0] + timedelta(days=1)
        return max(1, int((t - now).total_seconds()))

def main():
    try:
        if MODE.lower() == "daily":
            pretty = ", ".join(f"{h:02d}:00" for h in sorted(RUN_HOURS))
            print(f"Looping daily at {pretty}. Press Ctrl+C to stop.")
            if RUN_IMMEDIATELY:
                run_one_round()  # รันทันทีครั้งแรก (ตัวเลือก)
            while True:
                time.sleep(seconds_until_next_run())
                run_one_round()
        else:
            # โหมดนี้ไม่ถูกใช้ในเวอร์ชันที่แก้ แต่เว้นไว้เพื่อความยืดหยุ่น
            print("Looping in interval mode. Press Ctrl+C to stop.")
            while True:
                run_one_round()
                time.sleep(seconds_until_next_run())
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()
