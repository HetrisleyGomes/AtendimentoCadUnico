from flask import Flask, render_template,redirect, url_for, request, Blueprint, send_from_directory 
from src.server.server import (
    socketio,
)
import json, os, time
import pyttsx3
from datetime import datetime

main_bp = Blueprint("main_bp", __name__)

# Caminho do arquivo de data
data_file_path = 'src\database\data.json'
# Caminho do registro de atendimento
registro_file_path = 'src\\database\\registro.json'
# Fila atual
fila = []
# Fila atual para o responsável
fila_prior = []
# Guichês ativos
is_guiche_active = [0,0,0,0]

is_prior_actived = False

# CPF FAKE: 68027706017


# VOZ ------------------------
ultimo = 0
g_name = 0
AUDIO_DIR = os.path.join(os.getcwd(), 'src', 'static', 'audio')

@main_bp.route('/')
def index():
    # Obtem os dados de hoje
    get_data(data_file_path)
    global ultimo, g_name
    audio_file_url  = None # Inicializa a variável para o nome do arquivo de áudio

    if ultimo != 0:
        # Geração de um nome de arquivo único usando timestamp
        # Isso garante que o navegador sempre veja um URL novo
        timestamp = int(time.time()) # Obtém o timestamp atual
        audio_filename = f"chamado_{ultimo}_{timestamp}.mp3" # Nome do arquivo com valor e timestamp
        audio_filepath = os.path.join(AUDIO_DIR, audio_filename)

        # Opcional: Remover arquivos de áudio antigos para evitar acúmulo
        # Você pode ajustar a lógica aqui, por exemplo, remover apenas o último arquivo gerado
        for f in os.listdir(AUDIO_DIR):
            if f.startswith("chamado_") and f.endswith(".mp3") and f != audio_filename:
                try:
                    os.remove(os.path.join(AUDIO_DIR, f))
                except OSError as e:
                    print(f"Erro ao remover arquivo antigo: {e}")

        # Inicializa o pyttsx3
        engine = pyttsx3.init()
        
        # Mensagem
        msg = f"Atenção {ultimo}, compareça ao Guichê {g_name}"
        # Converte o texto para fala e salva no arquivo
        engine.save_to_file(msg, audio_filepath)
        engine.runAndWait()
        
        # Agora passamos o URL completo para o template
        audio_file_url = url_for('main_bp.serve_audio', filename=audio_filename)
        ultimo = 0
    return render_template('index.html', guiches=is_guiche_active, fila=fila, 
                           is_prior_actived=is_prior_actived, audio_file_url=audio_file_url)

# Rota para servir os arquivos de áudio
@main_bp.route('/static/audio/<filename>')
def serve_audio(filename):
    # Para garantir que o navegador não cacheie esta resposta
    response = send_from_directory(AUDIO_DIR, filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@main_bp.route('/registro')
def registro():
    return render_template('registro.html', fila = fila, fila_prior=fila_prior)

@main_bp.route('/registrar', methods=["POST"])
def registrar():
    # Nome registrado pela recepcionista
    name = request.form.get("name-input")
    # CPF registrado pela recepcionista
    cpf = request.form.get("cpf-input")
    # Prior registrado pela recepcionista
    prior = request.form.get("prior-input")
    # Adiciona o nome na fila
    if prior:
        fila_prior.append(name)
        socketio.emit('updatemaster', room=None)
    else:
        fila.append(name)
        socketio.emit('update', room=None)
    data = {
        'nome': name,
        'cpf': cpf
    }
    set_data(registro_file_path, data, True)
    
    return redirect(url_for('main_bp.registro'))


@main_bp.route('/remover/<int:fila_id>', methods=["POST"])
def remover(fila_id):
    if fila_id == 0:
        # Nome para ser removido
        nome = request.form.get("nome")
        if nome in fila:
            fila.remove(nome)
    else:
        # Nome para ser removido
        nome = request.form.get("nome")
        if nome in fila_prior:
            fila_prior.remove(nome)
    socketio.emit('update', room=None)
    return redirect(url_for('main_bp.registro'))

@main_bp.route('/guiches')
def guiche():
    # ID do guichê
    gx = request.args.get("gx")
    return render_template('guiches.html', gx=gx, fila=fila)

@main_bp.route('/guichemaster')
def guichemaster():
    return render_template('guiche_especial.html', fila_prior=fila_prior)

@main_bp.route('/proximomaster', methods=["POST"])
def proximomaster():
    # Se houver alguém na fila, busca a próxima pessoa
    if fila_prior:
        global is_prior_actived, ultimo, g_name
        is_prior_actived = fila_prior.pop(0)
        ultimo = is_prior_actived
        g_name = "especial"
        # Emite um evento para todos os clientes conectados
        socketio.emit('update-main', {}, room=None)
        socketio.emit('update', {}, room=None)

    return redirect(url_for("main_bp.guichemaster"))

@main_bp.route('/finalizarmaster', methods=["POST"])
def finalizarmaster():
    global is_prior_actived
    is_prior_actived = False
    # Emite um evento para todos os clientes conectados
    socketio.emit('update-main', {}, room=None)
    return redirect(url_for("main_bp.guichemaster"))

@main_bp.route('/proximo', methods=["POST"])
def proximo():
    # ID do guichê
    gx = request.form.get("gx")
    global guiches, ultimo, g_name
    # Se houver alguém na fila, busca a próxima pessoa
    if fila:
        is_guiche_active[int(gx)-1] = fila.pop(0)
        ultimo = is_guiche_active[int(gx)-1]
        g_name = gx
        # Emite um evento para todos os clientes conectados
        socketio.emit('update-main', {}, room=None)
        socketio.emit('update', {}, room=None)
        data = get_data(data_file_path)
        data[int(gx)-1] += 1
        print(data)
        set_data(data_file_path, data)

    return redirect(url_for("main_bp.guiche", gx=gx))

@main_bp.route('/finalizar', methods=["POST"])
def finalizar():
    # Verifica se é o responsável pelo setor
    isprior = request.form.get("prior")
    if not isprior:
        # ID do guichê
        gx = request.form.get("gx")
        global guiches
        # Desativa o Ghichê
        is_guiche_active[int(gx)-1] = 0
    # Emite um evento para todos os clientes conectados
    socketio.emit('update-main', {}, room=None)

    return redirect(url_for("main_bp.guiche", gx=gx))

@main_bp.route('/reset')
def reset():
    # Reseta tudo
    global guiches
    guiches = [0,0,0,0]
    socketio.emit('update-main', room=None)
    socketio.emit('update', room=None)
    return redirect('/guiches')

@main_bp.route('/relatorio')
def relatorio():
    # Obtêm todos os dados
    data = read_data(data_file_path)
    registros = read_data(registro_file_path)
    return render_template('relatorio.html', data = data, registros = registros)

@main_bp.route('/resetar/<int:tipo_reset>', methods=["POST"])
def resetar(tipo_reset):
    if tipo_reset == 1:
        resetar_dados_guiches()
        # return "Dados do guichê apagados com sucesso!" # Pode retornar uma mensagem ou JSON
    elif tipo_reset == 2:
        resetar_dados_atendimento()
        # return "Dados de atendimento apagados com sucesso!" # Pode retornar uma mensagem ou JSON
    else:
        # Lidar com um tipo_reset inválido, talvez redirecionar para uma página de erro
        return "Tipo de reset inválido!", 400

    # Redireciona para a página de onde o formulário foi enviado (ou outra página)
    # Exemplo: redirecionar para a página principal ou de administração
    return redirect(url_for('main_bp.relatorio'))

# Função para gerar o áudio
def gerar_audio(texto, nome_arquivo):
    engine = pyttsx3.init()
    engine.save_to_file(texto, nome_arquivo)
    engine.runAndWait()

def resetar_dados_guiches():
    print("Dados do guichê resetados!")
    reset_json(data_file_path, id=1)

def resetar_dados_atendimento():
    print("Dados de atendimento resetados!")
    reset_json(registro_file_path, id=2)

def get_data(file_path):
    # Lê os dados
    data = read_data(file_path)
    # Obtém a data de hoje no formato 'DD-MM-YYYY'
    hoje = datetime.now().strftime('%d-%m-%Y')

    # Verifica se a chave existe, senão cria com valor vazio
    if hoje not in data:
        data[hoje] = [0,0,0,0]
        save_json(file_path, data)

    return data[hoje]

def set_data(file_path, new_data, append=False):
    # Lê os dados
    data = read_data(file_path)
    # Obtém a data de hoje no formato 'DD-MM-YYYY'
    hoje = datetime.now().strftime('%d-%m-%Y')
    # Faz o registro e salva
    if (not append):
        data[hoje] = new_data
    elif (hoje not in data):
        data[hoje] = [new_data]
    else:
        data[hoje].append(new_data)
    save_json(file_path, data)

def read_data(file_path):
    # Lê os dados
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            data = {}
    return data

def save_json(file_path, data_to_save):
    # Salva os dados
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data_to_save, file, ensure_ascii=False, indent=4)

def reset_json(file_path, id):
    data = {}
    hoje = datetime.now().strftime('%d-%m-%Y')
    if id == 1:
        data[hoje] = [0,0,0,0]
    elif id == 2:
        data[hoje] = [{}]
    save_json(file_path, data)