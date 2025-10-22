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
TARGET_IP2 = "172.23.83.1"

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
        # Disable pagination if available
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

# ----------------- Daily file helpers (split into two files) ---------
def day_file_path(dt: datetime, target_ip: str) -> str:
    """Generate the file path for either Target IP 1 or Target IP 2."""
    file_name = f"Ping-{('ClearPass' if target_ip == TARGET_IP else 'Gateway')}-{dt.strftime('%Y-%m-%d')}.txt"
    return os.path.join(save_dir, file_name)

def append_block(dt: datetime, ip: str, target_ip: str, raw_output: str):
    """
    Append one block containing:
      [YYYY-MM-DD HH:MM:SS]  <DeviceName (IP)>  -> PING <TargetIP>
      <raw ping output>
    """
    path = day_file_path(dt, target_ip)
    ts = dt.strftime("%Y-%m-%d %H:%M:%S")
    label = get_device_label(ip)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}]  {label}  -> PING {target_ip}\n")
        f.write(raw_output.rstrip() + "\n\n")

# ----------------- Scheduler ---------------------------------------------
def seconds_until_next_interval(dt: datetime, every_minutes: int) -> int:
    minute = dt.minute
    next_slot_min = ((minute // every_minutes) + 1) * every_minutes
    if next_slot_min >= 60:
        next_run = dt.replace(second=0, microsecond=0) + timedelta(hours=1)
        next_run = next_run.replace(minute=0)
    else:
        next_run = dt.replace(minute=next_slot_min, second=0, microsecond=0)
    return max(1, int((next_run - dt).total_seconds()))

def main_loop():
    print("Starting ping scheduler... (Ctrl+C to stop)")
    while True:
        start = datetime.now()
        for ip in ip_list:
            # Ping TARGET_IP (ClearPass)
            cmd1 = f"ping {TARGET_IP} count {PING_COUNT}"
            ok1, out1 = ssh_run_command(ip, cmd1, timeout=300)
            append_block(start, ip, TARGET_IP, out1 if ok1 else out1)
            print(f"[{start.strftime('%Y-%m-%d %H:%M:%S')}] {get_device_label(ip)} PING {TARGET_IP} -> {day_file_path(start, TARGET_IP)}")

            # Ping TARGET_IP2 (Gateway)
            cmd2 = f"ping {TARGET_IP2} count {PING_COUNT}"
            ok2, out2 = ssh_run_command(ip, cmd2, timeout=300)
            append_block(start, ip, TARGET_IP2, out2 if ok2 else out2)
            print(f"[{start.strftime('%Y-%m-%d %H:%M:%S')}] {get_device_label(ip)} PING {TARGET_IP2} -> {day_file_path(start, TARGET_IP2)}")

        sleep_sec = seconds_until_next_interval(datetime.now(), INTERVAL_MINUTES)
        time.sleep(sleep_sec)

if __name__ == "__main__":
    main_loop()
