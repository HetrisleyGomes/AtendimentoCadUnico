from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = 'supersecretkey'
socketio = SocketIO(app)


@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


@socketio.on("update_request")
def handle_update_request():
    # Broadcast update to all clients
    emit("update", broadcast=True)


@socketio.on("message")
def handle_message(data):
    print("received message: " + data)
