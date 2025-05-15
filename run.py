from flask import Flask, render_template,redirect, url_for, request
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='src/templates', static_folder='src/static')
app.secret_key = 'supersecretkey'
socketio = SocketIO(app)

fila = []
is_guiche_active = [1,0,0,0]
people_to_guiche = [0,0,0,0]

@app.route('/')
def index():
    return render_template('index.html', guiches=is_guiche_active, fila = fila, people_to_guiche = people_to_guiche)

@app.route('/registro')
def registro():
    return render_template('registro.html', fila = fila)

@app.route('/registrar', methods=["POST"])
def registrar():
    name = request.form.get("name-input")
    fila.append(name)
    return redirect('/registro')

@app.route('/remover', methods=["POST"])
def remover():
    nome = request.form.get("nome")
    if nome in fila:
        fila.remove(nome)
    return redirect('/registro')

@app.route('/guiches')
def guiche():
    gx = request.args.get("gx")
    return render_template('guiches.html', gx=gx)

@app.route('/proximo', methods=["POST"])
def proximo():
    gx = request.form.get("gx")
    print(gx)
    global guiches
    if fila:
        people_to_guiche[int(gx)-1] = fila.pop()
        # Emite um evento para todos os clientes conectados
        socketio.emit('atualizar_ficha', room=None)

    return redirect(url_for("guiche", gx=gx))

@app.route('/update/<var>')
def update(var):

    print(var)
    print(type(var))

    return redirect('/guiches')

@app.route('/reset')
def reset():
    global guiches
    global ultimos
    guiches = [0,0,0,0]
    ultimos = []
    socketio.emit('atualizar_ficha', room=None)
    return redirect('/guiches')

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)