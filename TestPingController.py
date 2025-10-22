import paramiko
import os
import time
from datetime import datetime
import pandas as pd
import re
from typing import Tuple

# ----------------- Runtime Parameters -----------------
ip_list = ['172.23.83.12', '172.23.83.14', '172.23.83.16']
username = "admin"
password = "1Net@5cG2024"
save_dir = r"C:\Users\Administrator\Desktop\ArubaController-PingTest-CPPM"
os.makedirs(save_dir, exist_ok=True)

TARGET_IP = "10.100.10.20"
TARGET_IP_2 = "172.23.83.1"
PING_COUNT = 100
INTERVAL_MINUTES = 3  # run every 3 minutes

# ----------------- Device labels ---------------------
DEVICE_LABELS = {
    '172.23.83.12': 'SCG-BS-N-HO2-FL05-9240-01',
    '172.23.83.14': 'SCG-BS-N-HO2-FL05-9240-02',
    '172.23.83.16': 'SCG-BS-S-B20-FL02-9240-01',
}

def get_device_label(ip: str) -> str:
    """Return 'DeviceName (IP)' for headers inside the file."""
    name = DEVICE_LABELS.get(ip, ip)
    return name

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

# ----------------- Excel File Helper -----------------------------------
def parse_ping_result(result: str, ip: str) -> dict:
    """
    Parse the ping result and extract the Success Rate, Packets Sent/Received,
    and Round-trip min/avg/max.
    """
    # Extract Success Rate
    success_rate = re.search(r"Success rate is (\d+)%", result)
    success_rate_value = success_rate.group(1) if success_rate else "N/A"

    # Extract Packets Sent/Received
    packets_sent_received = re.search(r"(\d+)/(\d+)", result)
    packets_sent = packets_sent_received.group(1) if packets_sent_received else "N/A"
    packets_received = packets_sent_received.group(2) if packets_sent_received else "N/A"

    # Extract round-trip min/avg/max
    round_trip = re.search(r"round-trip min/avg/max = ([\d\.]+)\/([\d\.]+)\/([\d\.]+)", result)
    round_trip_min = round_trip.group(1) if round_trip else "N/A"
    round_trip_avg = round_trip.group(2) if round_trip else "N/A"
    round_trip_max = round_trip.group(3) if round_trip else "N/A"
    
    return {
        'Device Name': get_device_label(ip),  # Device Name based on IP
        'IP': ip,
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Ping Success Rate': f"{success_rate_value}% ({packets_sent}/{packets_received})",
        'Round-Trip Min (ms)': round_trip_min,
        'Round-Trip Avg (ms)': round_trip_avg,
        'Round-Trip Max (ms)': round_trip_max,
    }

def create_ping_report(ip_list, dt: datetime):
    """Create Excel report for ping results."""
    report_data = []
    
    for ip in ip_list:
        ping_cmd_1 = f"ping {TARGET_IP} count {PING_COUNT}"
        ping_cmd_2 = f"ping {TARGET_IP_2} count {PING_COUNT}"
        
        # Execute ping commands for both IPs
        ok1, result1 = ssh_run_command(ip, ping_cmd_1, timeout=300)
        ok2, result2 = ssh_run_command(ip, ping_cmd_2, timeout=300)
        
        # Prepare data for both TARGET_IP and TARGET_IP_2
        row_1 = parse_ping_result(result1, ip)  # For TARGET_IP
        row_2 = parse_ping_result(result2, ip)  # For TARGET_IP_2
        
        # Append the data for both IPs
        report_data.append(row_1)
        report_data.append(row_2)
        
        # Delay 1 minute before pinging the next IP
        time.sleep(60)
    
    # Convert data to pandas DataFrame
    df = pd.DataFrame(report_data)
    
    # Create file path with timestamp
    report_file_name = f"Ping-ClearPass-{dt.strftime('%Y-%m-%d')}.xlsx"
    file_path = os.path.join(save_dir, report_file_name)
    
    # Save the DataFrame to Excel
    df.to_excel(file_path, index=False)

    print(f"Report saved to: {file_path}")

# ----------------- Main Loop -------------------------------------------
def main_loop():
    """
    Every INTERVAL_MINUTES:
      - For each IP: SSH, run 'ping ... count N'
      - Append to the shared daily file <YYYY-MM-DD>.xlsx
    """
    print("Starting ping scheduler... (Ctrl+C to stop)")
    while True:
        start = datetime.now()
        
        # Create the report
        create_ping_report(ip_list, start)
        
        # Sleep until the next interval
        sleep_sec = 60 * INTERVAL_MINUTES
        time.sleep(sleep_sec)

if __name__ == "__main__":
    main_loop()
