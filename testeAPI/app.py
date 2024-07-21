from flask import Flask, request, jsonify, render_template, g, redirect, url_for
from flask_cors import CORS
import sqlite3

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Adiciona suporte a CORS

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def close_db(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_appcontext
def teardown_request(exception):
    close_db(exception)

def setup_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS numeros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alt_edv INTEGER NOT NULL,
            tipo_pessoa TEXT NOT NULL DEFAULT 'interno', 
            cpf TEXT,
            email TEXT,
            tenda_frios TEXT NOT NULL DEFAULT 'pendente',
            tenda_cesta TEXT NOT NULL DEFAULT 'pendente',
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        card = request.form['card']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO numeros (alt_edv) VALUES (?)', (card,))
        conn.commit()
        conn.close()
    
    return render_template('retirada.html', card=request.form['card'])

@app.route('/definir_estado', methods=['POST'])
def definir_estado():
    tipo_pessoa = request.form.get('tipo_pessoa')
    card = request.form.get('card')
    
    if not tipo_pessoa or not card:
        return redirect(url_for('home'))  # Redireciona para a página inicial em caso de erro
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE numeros SET tipo_pessoa = ? WHERE alt_edv = ?', (tipo_pessoa, card))
    conn.commit()
    conn.close()
    
    if tipo_pessoa == 'externo':
        return render_template('dados_externos.html', card=card)
    return redirect(url_for('conclusao'))

@app.route('/salvar_dados_externos', methods=['POST'])
def salvar_dados_externos():
    card = request.form.get('card')
    cpf = request.form.get('cpf')
    email = request.form.get('email')
    
    if not card or not cpf or not email:
        return redirect(url_for('home'))  # Redireciona para a página inicial em caso de erro
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE numeros SET cpf = ?, email = ? WHERE alt_edv = ?', (cpf, email, card))
    conn.commit()
    conn.close()
    
    return redirect(url_for('conclusao'))

@app.route('/update_person_type', methods=['POST'])
def update_person_type():
    data = request.json
    number = data.get('number')
    new_type = data.get('type')

    if not number or not new_type:
        return jsonify({'status': 'erro'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE numeros SET tipo_pessoa = ? WHERE alt_edv = ?', (new_type, number))

    if new_type == 'interno':
        # Atualiza o tipo de pessoa e define ambos os campos como 'pendente'
        cursor.execute('UPDATE numeros SET tenda_frios = ?, tenda_cesta = ? WHERE alt_edv = ?', ('pendente', 'pendente', number))

    conn.commit()
    conn.close()

    return jsonify({'status': 'ok'})

@app.route('/conclusao', methods=['GET'])
def conclusao():
    return render_template('page_conclusao.html')

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    return render_template('stats.html')

@app.route('/grafico', methods=['GET'])
def grafico():
    return render_template('stats.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        card = request.form['card']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM numeros WHERE alt_edv = ?', (card,))
        result = cursor.fetchone()
        
        if result and result[0] == 1:  # Verifica se is_admin é 1 (administrador)
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('admin_login'))  # Se o EDV não for do admin, redireciona de volta
    
    return render_template('index_admin.html')

@app.route('/get_status', methods=['GET'])
def get_status():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT alt_edv, tipo_pessoa, tenda_frios, tenda_cesta, cpf, email FROM numeros")
    rows = cursor.fetchall()
    
    return jsonify([{
        'alt_edv': row[0],
        'tipo_pessoa': row[1],
        'tenda_frios': row[2],
        'tenda_cesta': row[3],
        'cpf': row[4],
        'email': row[5]
    } for row in rows])

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    edv = data.get('edv')
    tenda_frios = data.get('tenda_frios')
    tenda_cesta = data.get('tenda_cesta')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE numeros
        SET tenda_frios = ?,
            tenda_cesta = ?
        WHERE alt_edv = ?
    """, (tenda_frios, tenda_cesta, edv))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/validate', methods=['POST'])
def validate_number():
    data = request.json
    number = data.get('number')
    tenda = data.get('tenda')

    if not number or not tenda:
        return jsonify({'status': 'erro'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM numeros WHERE alt_edv = ?', (number,))
    result = cursor.fetchone()
    
    if result:
        if tenda == 'frios':
            current_status = result[5]  # Índice de tenda_frios
            if current_status == 'pendente':
                cursor.execute('UPDATE numeros SET tenda_frios = ? WHERE alt_edv = ?', ('concluido', number))
                conn.commit()
                status = 'concluido_frios'
            elif current_status == 'concluido':
                status = 'ja_pegou_frios'
            else:
                status = current_status
        elif tenda == 'cesta':
            current_status = result[6]  # Índice de tenda_cesta
            if current_status == 'pendente':
                cursor.execute('UPDATE numeros SET tenda_cesta = ? WHERE alt_edv = ?', ('concluido', number))
                conn.commit()
                status = 'concluido_cesta'
            elif current_status == 'concluido':
                status = 'ja_pegou_cesta'
            else:
                status = current_status
    else:
        status = 'nao encontrado'
    
    conn.close()
    return jsonify({'status': status})

def add_admin():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM numeros WHERE alt_edv = ?', (1234,))
    result = cursor.fetchone()
    
    if not result:
        # Adiciona um usuário administrador com alt_edv 1234 apenas se não existir
        cursor.execute('INSERT INTO numeros (alt_edv, is_admin) VALUES (?, ?)', (1234, 1))
        conn.commit()
    
    conn.close()

@app.route('/get_status_frios', methods=['GET'])
def get_status_frios():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT alt_edv, tipo_pessoa, tenda_frios FROM numeros")
    rows = cursor.fetchall()
    
    return jsonify([{
        'alt_edv': row[0],
        'tipo_pessoa': row[1],
        'tenda_frios': row[2]
    } for row in rows])


@app.route('/get_status_cestas', methods=['GET'])
def get_status_cestas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT alt_edv, tipo_pessoa, tenda_cesta FROM numeros")
    rows = cursor.fetchall()
    
    return jsonify([{
        'alt_edv': row[0],
        'tipo_pessoa': row[1],
        'tenda_cesta': row[2]
    } for row in rows])

@app.route('/status_frios')
def status_frios_page():
    return render_template('status_frios.html')

@app.route('/status_cestas')
def status_cestas_page():
    return render_template('status_cestas.html')


if __name__ == "__main__":
    setup_database()
    add_admin()  # para adicionar admin
    app.run(debug=True)
