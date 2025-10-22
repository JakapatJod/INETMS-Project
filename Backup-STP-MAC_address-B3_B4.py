import paramiko
from datetime import datetime
from pathlib import Path

# ----------------- Auth & Base Path -----------------
username = "admin"
password = "1Net@5cG2024"  

base_dir = Path(r"C:\Users\Administrator\Desktop\Backup-STP_VLAN_MAC-address_B3_B4")
base_dir.mkdir(parents=True, exist_ok=True)

# ----------------- Device groups (B3/B4) -----------------
DEVICE_GROUPS = {
    "B3": {
        "172.23.84.50": "SCG-BS-S-B3-FL01-24G-01",
        "172.23.84.51": "SCG-BS-S-B3-FL02-24G-01",
        "172.23.84.52": "SCG-BS-S-B3-FL03-24G-01",
        "172.23.84.53": "SCG-BS-S-B3-FL04-48G-01",
    },
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
}

# ----------------- Commands -----------------
COMMANDS = [
    "no page",
    "sho spanning-tree summary root",
    "show mac-address-table",
    "show int lag 1",
    "show lacp aggregates"
]

SSH_CONNECT_TIMEOUT = 20
CMD_TIMEOUT = 180

# ----------------- SSH helper -----------------
def ssh_run_multi(host: str, cmds: list[str]) -> tuple[bool, dict[str, str]]:
    """
    เปิด SSH ครั้งเดียวแล้วรันทุกคำสั่งตามลำดับ
    return: (ok, {cmd: output})
    """
    outputs: dict[str, str] = {}
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

        for c in cmds:
            try:
                stdin, stdout, stderr = client.exec_command(c, timeout=CMD_TIMEOUT)
                out = stdout.read().decode(errors="ignore")
                err = stderr.read().decode(errors="ignore")
                outputs[c] = (out + ("\n" + err if err else "")).strip() or "(no output)"
            except Exception as e:
                outputs[c] = f"[ERROR while running '{c}'] {type(e).__name__}: {e}"

        return True, outputs

    except Exception as e:
        return False, { "connection": f"[ERROR] {type(e).__name__}: {e}" }
    finally:
        try:
            if client:
                client.close()
        except Exception:
            pass

# ----------------- Save helper -----------------
def save_txt(group: str, device_name: str, ip: str, cmd_outputs: dict[str, str]) -> Path:
    """
    เซฟไฟล์เป็นชื่ออุปกรณ์ .txt และแยกโฟลเดอร์ตามกลุ่ม (B3/B4)
    """
    group_dir = base_dir / group
    group_dir.mkdir(parents=True, exist_ok=True)
    path = group_dir / f"{device_name}.txt"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"[{ts}]  {device_name} ({ip})"]
    for cmd in COMMANDS:
        if cmd in cmd_outputs:
            lines.append(f"\n>>> {cmd}\n{cmd_outputs[cmd]}")
    content = "\n".join(lines).rstrip() + "\n"

    with path.open("w", encoding="utf-8") as f:
        f.write(content)

    return path

# ----------------- One-shot main -----------------
def main():
    print("Start collecting outputs (one run, sequential)...")
    for group, mapping in DEVICE_GROUPS.items():      
        for ip, name in mapping.items():              
            print(f"- {group} | {name} ({ip}) ...")
            ok, outputs = ssh_run_multi(ip, COMMANDS)
            p = save_txt(group, name, ip, outputs)
            print(f"  -> saved: {p}")
    print("Done.")

if __name__ == "__main__":
    main()
