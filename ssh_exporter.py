import os
import paramiko
from prometheus_client import start_http_server, Gauge
import time

SSH_HOST = os.getenv("SSH_HOST", "127.0.0.1")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER", "root")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH", "/id_rsa")
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", "9122"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))

cpu_load = Gauge('ssh_cpu_load_1min', '1 minute CPU load')
cpu_usage = Gauge('ssh_cpu_usage_percent', 'CPU usage percent')
memory_free = Gauge('ssh_memory_free_mb', 'Free memory in MB')
memory_total = Gauge('ssh_memory_total_mb', 'Total memory in MB')
memory_used_percent = Gauge('ssh_memory_used_percent', 'Memory used percent')
disk_usage = Gauge('ssh_root_disk_usage_percent', 'Root filesystem usage percent')
disk_total = Gauge('ssh_disk_total_gb', 'Total disk size of root in GB')

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, key_filename=SSH_KEY_PATH)
    return client

def collect_metrics():
    try:
        client = get_ssh_client()

        # CPU Load
        stdin, stdout, stderr = client.exec_command("cat /proc/loadavg")
        output = stdout.read().decode().strip()
        try:
            loadavg = float(output.split()[0])
            cpu_load.set(loadavg)
        except Exception:
            pass

        # CPU Usage %
        stdin, stdout, stderr = client.exec_command("top -bn1 | grep '%Cpu' | awk '{print 100 - $8}'")
        output = stdout.read().decode().strip()
        try:
            cpu_percent = float(output)
            cpu_usage.set(cpu_percent)
        except Exception:
            pass

        # Memory stats
        stdin, stdout, stderr = client.exec_command("free -m | grep Mem")
        output = stdout.read().decode().strip()
        try:
            mem_line = output.split()
            total_mem = int(mem_line[1])
            free_mem = int(mem_line[2])
            memory_total.set(total_mem)
            memory_free.set(free_mem)
        except Exception:
            pass

        # Real memory usage %
        stdin, stdout, stderr = client.exec_command("free -m | grep Mem")
        output = stdout.read().decode().strip()
        try:
            mem_line = output.split()
            total_mem = int(mem_line[1])
            available_mem = int(mem_line[6])  # <---- patch: use 'available' column
            used_mem_percent_value = ((total_mem - available_mem) / total_mem) * 100 if total_mem > 0 else 0
            memory_used_percent.set(used_mem_percent_value)
        except Exception:
            pass

        # Disk usage
        stdin, stdout, stderr = client.exec_command("df / | tail -1")
        output = stdout.read().decode().strip()
        try:
            disk_line = output.split()
            usage_percent = int(disk_line[4].replace('%', ''))
            total_blocks = int(disk_line[1])
            total_gb = round(total_blocks / (1024 * 1024), 2)
            disk_usage.set(usage_percent)
            disk_total.set(total_gb)
        except Exception:
            pass

        client.close()

    except Exception:
        pass

def main():
    start_http_server(EXPORTER_PORT)
    while True:
        collect_metrics()
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()