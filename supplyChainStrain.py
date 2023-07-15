from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import firmware_flasher
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def home():
    return render_template("index.html")

@socketio.on('flash_firmware')
def flash_firmware():
    def send_log_line(line):
        emit('console_log', line)

    emit('firmware_flash_ready')  # Emit the event to set the button color to green
    result = firmware_flasher.send_file('/dev/cu.usbserial-A56ULRQ8', 'firmware.bin', send_log_line)
    emit('firmware_flash_result', {'result': result})
    emit('firmware_flash_complete')  # Emit the event to reset the button color

if __name__ == "__main__":
    socketio.run(app, debug=True)
