from src.server.server import app, socketio
from src.routes.routes import main_bp

if __name__ == "__main__":
    app.register_blueprint(main_bp)
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)