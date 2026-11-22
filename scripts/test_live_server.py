"""Test live uvicorn server startup and HTTP responses."""
import subprocess
import time
import urllib.request
import json
import sys

def test_server():
    print("Starting uvicorn server process...")
    cmd = [
        r"C:\Users\GAURAV DAS\.conda\envs\fakedeal\python.exe",
        "-m", "uvicorn",
        "app.main:app",
        "--app-dir", "backend",
        "--host", "127.0.0.1",
        "--port", "8008",
        "--log-level", "warning"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        # Wait up to 10 seconds for server to start
        url_health = "http://127.0.0.1:8008/health"
        started = False
        for attempt in range(20):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen(url_health, timeout=2) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        print("Server is UP! Health:", data)
                        started = True
                        break
            except Exception:
                pass

        if not started:
            stdout, stderr = proc.communicate(timeout=2)
            print("Server failed to start:", stdout.decode(), stderr.decode())
            sys.exit(1)

        # Probe catalog metadata
        with urllib.request.urlopen("http://127.0.0.1:8008/api/catalog/metadata", timeout=5) as response:
            meta = json.loads(response.read().decode())
            print(f"Catalog Metadata: {len(meta['platforms'])} platforms, {len(meta['categories'])} categories")
            assert len(meta['platforms']) == 5
            assert len(meta['categories']) == 7

        # Probe synthetic comparison
        with urllib.request.urlopen("http://127.0.0.1:8008/api/models/synthetic-comparison", timeout=5) as response:
            comp = json.loads(response.read().decode())
            print(f"Synthetic Comparison: {comp['status']}, Selected: {comp['selected_model']}")
            assert comp['status'] == 'AVAILABLE'
            assert comp['selected_model'] == 'random_forest'

        print("Live server testing passed successfully!")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        print("Server process terminated cleanly.")

if __name__ == "__main__":
    test_server()
