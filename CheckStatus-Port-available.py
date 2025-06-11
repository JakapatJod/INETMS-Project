import re
import paramiko
from datetime import datetime, time as dt_time, timedelta
import os
import time

# ----------------- Parameters -----------------
ip_list = ['172.30.246.57','172.30.246.58','172.23.84.6','172.23.84.7','172.23.84.8','172.23.84.9','172.23.84.10','172.23.84.11','172.23.84.12','172.23.84.13','172.23.84.14','172.23.84.15','172.23.84.16','172.23.84.17','172.23.84.18','172.23.84.19','172.23.84.20','172.23.84.21','172.23.84.22','172.23.84.23','172.23.84.24','172.23.84.25','172.23.84.26','172.23.84.27','172.23.84.28','172.23.84.29','172.23.84.30','172.23.84.96','172.23.84.94','172.23.84.95','172.23.84.97','172.22.252.6','172.22.252.7','172.22.252.8','172.22.252.9','172.22.252.10','172.22.252.11','172.22.252.12','172.22.252.13','172.22.252.14','172.22.252.15','172.22.252.16','172.22.252.17','172.22.252.18','172.22.252.19','172.22.252.20','172.22.252.21','172.22.252.22','172.22.252.23','172.22.252.24','172.22.252.25','172.22.252.26','172.22.252.27','172.22.252.28','172.22.252.29','172.22.252.30','172.22.252.31','172.22.252.32','172.22.252.33','172.22.252.34','172.22.252.35','172.22.252.36','172.23.84.31','172.23.84.32','172.23.84.33','172.23.84.34','172.23.84.35','172.23.84.36','172.23.84.37','172.23.84.38','172.23.84.39','172.23.84.40','172.23.84.41','172.23.84.42','172.23.84.93','172.23.84.43','172.23.84.44','172.23.84.45','172.23.84.46','172.23.84.47','172.23.84.48','172.23.84.49','172.23.84.50','172.23.84.51','172.23.84.52','172.23.84.53','172.23.84.54','172.23.84.55','172.23.84.56','172.23.84.57','172.23.84.58','172.23.84.59','172.23.84.60','172.23.84.61','172.23.84.62','172.23.84.63','172.23.84.64','172.23.84.65','172.23.84.66','172.23.84.67','172.23.84.68','172.23.84.69','172.23.84.70','172.23.84.71','172.23.84.72','172.23.84.73','172.23.84.74','172.23.84.75','172.23.84.76','172.23.84.77','172.23.84.78','172.23.84.79','172.23.84.80','172.23.84.81','172.23.84.82','172.23.84.83','172.23.84.84','172.23.84.85','172.23.84.86','172.23.84.87','172.23.84.88','172.23.84.89','172.23.84.90','172.23.84.91','172.23.84.92']

username  = "admin"
password  = "1Net@5cG2024"

save_dir = r"C:\Users\Administrator\Desktop\Port-available"
os.makedirs(save_dir, exist_ok=True)

# ---------- helper ----------
DOWN_RE  = re.compile(r"Link state:\s*down\s+for\s+(\d+)\s+months?", re.IGNORECASE)
DESC_RE  = re.compile(r"\bPC[_\- ]?IPPhone\b", re.IGNORECASE)

def send_command(ssh, cmd):
    stdin, stdout, _ = ssh.exec_command(f"no page\n{cmd}\n")
    return stdout.read().decode(errors="ignore")

# ---------- job ----------
def check_ports_job():
    timestamp_str = datetime.now().strftime("%B-%d-%Y_%H-%M")
    output_file   = os.path.join(
        save_dir, f"port_available_report_{timestamp_str}.txt"
    )

    print(f"\n📋  Starting port-check job @ {timestamp_str}")
    with open(output_file, "w", encoding="utf-8") as file:
        for ip in ip_list:
            try:
                print(f"\n🔌 Connecting to {ip} …")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    ip, username=username, password=password,
                    look_for_keys=False, allow_agent=False, timeout=10
                )

                # hostname
                host_out = send_command(ssh, "show run | include hostname")
                m_host   = re.search(r"hostname\s+(\S+)", host_out)
                hostname = m_host.group(1) if m_host else ip
                print(f"✅  Connected to → {hostname}")

                # interface brief
                brief_out  = send_command(ssh, "show interface brief")
                interfaces = [
                    re.match(r"^\s*(\S+)", ln).group(1)
                    for ln in brief_out.splitlines()
                    if DESC_RE.search(ln) and re.match(r"^\s*(\S+)", ln)
                ]

                if not interfaces:
                    print("  ❌ No interfaces found with keyword 'PC_IPPhone'")
                    ssh.close()
                    continue

                print(f"  ▶ Found {len(interfaces)} ports: {interfaces}")

                down_ports = []
                for intf in interfaces:
                    int_out = send_command(ssh, f"show interface {intf}")
                    m_down  = DOWN_RE.search(int_out)
                    if m_down and int(m_down.group(1)) >= 1:
                        down_ports.append((intf, m_down.group(1)))

                if down_ports:
                    file.write(f"Device : {hostname} ({ip})\n")
                    file.write("=" * 56 + "\n")
                    for intf, months in down_ports:
                        file.write(f"{intf}  down for {months} months\n")
                    file.write("=" * 56 + "\n\n")
                    print("  📝 Ports down ≥1 month have been written to the file")
                else:
                    print("  ✅ All ports are up or down less than 1 month")

                ssh.close()

            except Exception as e:
                print(f"[ERROR] {ip} – {e}")
                file.write(f"[ERROR] {ip} – {e}\n")

    print(f"📄 Report saved to: {output_file}")

# ---------- lightweight scheduler ----------
RUN_TIMES = [dt_time(9,0), dt_time(12,0), dt_time(15,0), dt_time(18,0)]

def seconds_until_next_run(now=None):
    if now is None:
        now = datetime.now()

    today_runs = [datetime.combine(now.date(), t) for t in RUN_TIMES]
    upcoming   = [rt for rt in today_runs if rt > now]
    if upcoming:
        next_run = min(upcoming)
    else:
        # วันถัดไปเวลา 09:00
        next_run = datetime.combine(now.date() + timedelta(days=1), RUN_TIMES[0])

    return (next_run - now).total_seconds(), next_run

if __name__ == "__main__":
    print("⏰  Port-check daemon started")
    while True:
        secs, nr = seconds_until_next_run()
        mins = int(secs // 60)
        print(f"   Next run: {nr.strftime('%Y-%m-%d %H:%M')} (in {mins} min)")
        time.sleep(secs)
        check_ports_job()
