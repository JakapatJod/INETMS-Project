import paramiko
from datetime import datetime, timedelta
import os
import time
from typing import Tuple

# ----------------- Runtime Parameters -----------------
ip_list = ['172.23.83.12','172.23.83.14','172.23.83.16']

username = "admin"
password = "1Net@5cG2024"

save_dir = r"C:\Users\Administrator\Desktop\ArubaController-PingTest-CPPM"
os.makedirs(save_dir, exist_ok=True)

TARGET_IP = "10.100.10.20"
PING_COUNT = 100
INTERVAL_MINUTES = 3  # run every 3 minutes

# ----------------- Device labels (shown in the file) ---------------------
DEVICE_LABELS = {
    '172.23.83.12': 'SCG-BS-N-HO2-FL05-9240-01',
    '172.23.83.14': 'SCG-BS-N-HO2-FL05-9240-02',
    '172.23.83.16': 'SCG-BS-S-B20-FL02-9240-01',
}

def get_device_label(ip: str) -> str:
    """Return 'DeviceName (IP)' for headers inside the file."""
    name = DEVICE_LABELS.get(ip, ip)
    return f"{name} ({ip})"

# ----------------- Per-device ping command -------------------------------
# Aruba/Linux-style "count"
DEFAULT_PING_CMD = f"ping {TARGET_IP} count {PING_COUNT}"
DEVICE_PING_CMD = {
    '172.23.83.12': f"ping {TARGET_IP} count {PING_COUNT}",
    '172.23.83.14': f"ping {TARGET_IP} count {PING_COUNT}",
    '172.23.83.16': f"ping {TARGET_IP} count {PING_COUNT}",
}

# ----------------- SSH Helpers ------------------------------------------
def ssh_run_command(host: str, cmd: str, timeout: int = 180) -> Tuple[bool, str]:
    """Open SSH, run one command, return (ok, output)."""
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host, username=username, password=password,
            look_for_keys=False, allow_agent=False, timeout=20
        )
        # Best-effort: disable pagination if available
        try:
            _stdin, _stdout, _stderr = client.exec_command("terminal length 0", timeout=5)
            _ = _stdout.read()
        except Exception:
            pass

        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        client.close()
        output = (out + ("\n" + err if err else "")).strip()
        return True, output if output else "(no output)"
    except Exception as e:
        try:
            if client:
                client.close()
        except Exception:
            pass
        return False, f"[ERROR] {type(e).__name__}: {e}"

# ----------------- Daily file helpers (single file for all devices) ------
def day_file_path(dt: datetime) -> str:
    """
    Daily file path (single file for all controllers):
      <save_dir>/<YYYY-MM-DD>.txt
    """
    fname = f"{dt.strftime('%Y-%m-%d')}.txt"
    return os.path.join(save_dir, fname)

def append_block(dt: datetime, ip: str, raw_output: str):
    """
    Append one block containing:
      [YYYY-MM-DD HH:MM:SS]  <DeviceName (IP)>
      <raw ping output>
    Then one blank line as separator.
    """
    path = day_file_path(dt)
    ts = dt.strftime("%Y-%m-%d %H:%M:%S")
    label = get_device_label(ip)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}]  {label}\n")
        f.write(raw_output.rstrip() + "\n\n")

# ----------------- Scheduler -------------------------------------------
def seconds_until_next_interval(dt: datetime, every_minutes: int) -> int:
    """Seconds until the next aligned minute (e.g., every 5 min -> 00,05,10,...)."""
    minute = dt.minute
    next_slot_min = ((minute // every_minutes) + 1) * every_minutes
    if next_slot_min >= 60:
        next_run = dt.replace(second=0, microsecond=0) + timedelta(hours=1)
        next_run = next_run.replace(minute=0)
    else:
        next_run = dt.replace(minute=next_slot_min, second=0, microsecond=0)
    return max(1, int((next_run - dt).total_seconds()))

def main_loop():
    """
    Every INTERVAL_MINUTES:
      - For each IP: SSH, run 'ping ... count N'
      - Append to the shared daily file <YYYY-MM-DD>.txt
    """
    print("Starting ping scheduler... (Ctrl+C to stop)")
    while True:
        start = datetime.now()
        for ip in ip_list:
            cmd = DEVICE_PING_CMD.get(ip, DEFAULT_PING_CMD)
            ok, out = ssh_run_command(ip, cmd, timeout=300)
            append_block(start, ip, out if ok else out)
            print(f"[{start.strftime('%Y-%m-%d %H:%M:%S')}] {get_device_label(ip)} -> {day_file_path(start)}")

        sleep_sec = seconds_until_next_interval(datetime.now(), INTERVAL_MINUTES)
        time.sleep(sleep_sec)

if __name__ == "__main__":
    main_loop()
