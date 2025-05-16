from flask import Flask, render_template,redirect, url_for, request, Blueprint
from src.server.server import (
    socketio,
)

main_bp = Blueprint("main_bp", __name__)

fila = []
is_guiche_active = ["José cralos de albuquerque bragança silva ssauro de buarque bragança2",0,5525258,4]

@main_bp.route('/')
def index():
    return render_template('index.html', guiches=is_guiche_active, fila = fila)

@main_bp.route('/registro')
def registro():
    return render_template('registro.html', fila = fila)

@main_bp.route('/registrar', methods=["POST"])
def registrar():
    name = request.form.get("name-input")
    fila.append(name)
    return redirect(url_for('main_bp.registro'))

@main_bp.route('/remover', methods=["POST"])
def remover():
    nome = request.form.get("nome")
    if nome in fila:
        fila.remove(nome)
    return redirect(url_for('main_bp.registro'))

@main_bp.route('/guiches')
def guiche():
    gx = request.args.get("gx")
    return render_template('guiches.html', gx=gx)

@main_bp.route('/proximo', methods=["POST"])
def proximo():
    gx = request.form.get("gx")
    print(gx)
    global guiches
    if fila:
        is_guiche_active[int(gx)-1] = fila.pop(0)
        # Emite um evento para todos os clientes conectados
        socketio.emit('update', {}, room=None)

    return redirect(url_for("main_bp.guiche", gx=gx))

@main_bp.route('/update/<var>')
def update(var):

    print(var)
    print(type(var))

    return redirect('/guiches')

@main_bp.route('/reset')
def reset():
    global guiches
    global ultimos
    guiches = [0,0,0,0]
    ultimos = []
    socketio.emit('update', room=None)
    return redirect('/guiches')