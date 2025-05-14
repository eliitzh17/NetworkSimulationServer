import subprocess
import sys
import os
import time

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKERS_DIR = os.path.join(BASE_DIR, "app", "workers")
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")

# List all worker scripts
worker_files = [
    f for f in os.listdir(WORKERS_DIR)
    if f.endswith(".py") and not f.startswith("__") and f != "base_worker.py"
]

processes = []

env = os.environ.copy()
env["PYTHONPATH"] = BASE_DIR  # Add project root to PYTHONPATH

try:
    # Start main app
    print(f"Starting main app: {MAIN_SCRIPT}")
    main_proc = subprocess.Popen([sys.executable, MAIN_SCRIPT], env=env)
    processes.append(main_proc)

    # Start each worker
    for worker in worker_files:
        worker_path = os.path.join(WORKERS_DIR, worker)
        print(f"Starting worker: {worker_path}")
        proc = subprocess.Popen([sys.executable, worker_path], env=env)
        processes.append(proc)

    # Wait for all processes
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down all processes...")
    for proc in processes:
        proc.terminate()
    for proc in processes:
        proc.wait()
    print("All processes terminated.")