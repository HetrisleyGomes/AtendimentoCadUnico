from flask import Flask, render_template,redirect, url_for, request, Blueprint
from src.server.server import (
    socketio,
)
import json
from datetime import datetime

main_bp = Blueprint("main_bp", __name__)
# Caminho do arquivo
file_path = 'src\database\data.json'

fila = []
is_guiche_active = [0,0,0,0]

@main_bp.route('/')
def index():
    get_data()
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
        data = get_data()
        data[int(gx)-1] += 1
        print(data)
        set_data(data)

    return redirect(url_for("main_bp.guiche", gx=gx))

@main_bp.route('/finalizar', methods=["POST"])
def finalizar():
    gx = request.form.get("gx")
    global guiches
    is_guiche_active[int(gx)-1] = 0
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

def get_data():
    data = read_data()
    # Obtém a data de hoje no formato 'DD-MM-YYYY'
    hoje = datetime.now().strftime('%d-%m-%Y')

    # Verifica se a chave existe, senão cria com valor vazio
    if hoje not in data:
        data[hoje] = [0,0,0,0]
        save_json(data)

    return data[hoje]

def set_data(new_data):
    data = read_data()
    hoje = datetime.now().strftime('%d-%m-%Y')
    data[hoje] = new_data
    print('SET DATA ------------------------')
    print(data)
    save_json(data)

def read_data():
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            data = {}
    return data

def save_json(data_to_save):
    print('SAVE json DATA ------------------------')
    print(data_to_save)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data_to_save, file, ensure_ascii=False, indent=4)