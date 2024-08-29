from flask import Flask, render_template, jsonify
import subprocess
import os
import sys
import platform
import shutil

def get_python_executable():
    if platform.system() == "Windows":
        return sys.executable
    else:
        # On Linux, prefer 'python3' if available, fall back to 'python'
        python3_path = shutil.which('python3')
        if python3_path:
            return python3_path
        return shutil.which('python') or sys.executable

app = Flask(__name__)

script_process = None
script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "detect_notify", "main.py"))
print(script_path)

@app.route('/')
def home():
    global script_process
    is_running = script_process is not None and script_process.poll() is None
    return render_template('index.html', is_running=is_running)

@app.route('/start')
def start_script():
    global script_process
    if script_process is None or script_process.poll() is not None:
        python_exec = get_python_executable()
        script_process = subprocess.Popen([python_exec, script_path])
    return jsonify({"status": "Running"})

@app.route('/stop')
def stop_script():
    global script_process
    if script_process is not None and script_process.poll() is None:
        script_process.terminate()
        script_process = None
    return jsonify({"status": "Stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)