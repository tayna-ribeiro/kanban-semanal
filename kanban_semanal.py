import os
import re
import json
import shutil
import sqlite3
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)

DATABASE = 'kanban.db'
TASKS_FILE = 'tarefasDiarias.txt'
HISTORY_FILE = 'historico.txt'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        # Tabela de Tarefas (Cards)
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                contract TEXT NOT NULL,
                tag TEXT NOT NULL,
                status TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                subtask_title TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        # Tabela de Subtarefas
        db.execute("""
            CREATE TABLE IF NOT EXISTS subtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                is_done INTEGER DEFAULT 0,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        # Tabela de Quadro de Avisos (Notices)
        db.execute("""
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section TEXT NOT NULL,
                text TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        # Tabela de Logins Frequentes
        db.execute("""
            CREATE TABLE IF NOT EXISTS logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        db.commit()

# --- CÓDIGO DE PARSING ORIGINAL (MANTIDO APENAS PARA MIGRAÇÃO INICIAL) ---
def parse_notice_board_txt():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    notices = []
    lines = content.split('\n')
    NOTICE_KEYWORDS = ['DEPLOY', 'IMPORTANTE', 'FÉRIAS', 'FERIAS', 'POSSIBILIDADE', 'PRAZOS', 'DEADLINE']
    SKIP_KEYWORDS = ['DEMANDA', 'MELHORIA']
    current_section = None
    current_items = []
    
    def flush_section():
        if current_section and current_items:
            notices.append({
                'title': current_section,
                'items': list(current_items)
            })
            
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            header_text = stripped.lstrip('#').strip()
            header_upper = header_text.upper()
            is_notice = any(kw in header_upper for kw in NOTICE_KEYWORDS)
            is_skip = any(kw in header_upper for kw in SKIP_KEYWORDS)
            if is_notice and not is_skip:
                flush_section()
                current_section = header_text
                current_items = []
            else:
                flush_section()
                current_section = None
                current_items = []
            continue
        if current_section and stripped and not stripped.startswith('-' * 5):
            text = stripped.lstrip('*').lstrip('-').strip()
            if text:
                current_items.append({'line_idx': idx, 'text': text})
    flush_section()
    return notices

def parse_tasks_txt():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    tasks = []
    lines = content.split('\n')
    current_contract = None
    current_type = None
    in_target_section = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('##'):
            header_text = stripped.upper()
            match = re.match(r'^##\s+([A-ZÇÃÕÉÍÓÚ\s]+?)\s+(?:DO|NO|DE)\s+([A-Z\s]+)', header_text)
            if match:
                in_target_section = True
                current_type = match.group(1).strip().title()
                contract_raw = match.group(2).strip()
                if 'INTO' in contract_raw:
                    current_contract = 'INTO'
                elif 'JBRJ' in contract_raw or 'JABOT' in contract_raw or 'JARDIM' in contract_raw:
                    current_contract = 'JBRJ'
                else:
                    current_contract = contract_raw
            else:
                if 'DEMANDA' in header_text or 'MELHORIA' in header_text:
                    in_target_section = True
                    if 'INTO' in header_text:
                        current_contract = 'INTO'
                    elif 'JBRJ' in header_text or 'JABOT' in header_text or 'JARDIM' in header_text:
                        current_contract = 'JBRJ'
                    else:
                        current_contract = 'OUTROS'
                    if 'DEMANDA' in header_text:
                        current_type = 'Demanda'
                    else:
                        current_type = 'Melhoria'
                else:
                    in_target_section = False
            i += 1
            continue
        if in_target_section and stripped.startswith('*'):
            start_idx = i
            block_lines = [line]
            task_match = re.match(r'^([\s\*]+)(?:\[(Em andamento)\]\s+)?(.*)', line, re.IGNORECASE)
            prefix = task_match.group(1) if task_match else "* "
            status_tag = task_match.group(2) if task_match else None
            first_line_text = task_match.group(3) if task_match else line.lstrip('*').lstrip()
            status = 'todo'
            if status_tag and status_tag.lower() == 'em andamento':
                status = 'doing'
            j = i + 1
            while j < len(lines):
                next_stripped = lines[j].strip()
                if next_stripped == '' or next_stripped.startswith('*') or next_stripped.startswith('#') or next_stripped.startswith('-'):
                    break
                block_lines.append(lines[j])
                j += 1
            full_text = '\n'.join([first_line_text] + [l.strip() for l in block_lines[1:]])
            subtask_file = None
            ref_match = re.search(r'consultar\s+(?:o\s+)?bloco\s+["\u201c\u201d\']([^"\u201c\u201d\']+)["\u201c\u201d\']', full_text, re.IGNORECASE)
            if ref_match:
                subtask_file = ref_match.group(1)
                if not subtask_file.lower().endswith('.txt'):
                    subtask_file += '.txt'
            tasks.append({
                'id': start_idx,
                'start_idx': start_idx,
                'contract': current_contract,
                'type': current_type,
                'text': full_text,
                'status': status,
                'subtask_file': subtask_file
            })
            i = j
            continue
        i += 1
    return tasks

# --- MIGRACÃO AUTOMÁTICA ---
def migrate_txt_to_sqlite():
    if os.path.exists(TASKS_FILE):
        print("Migração: Encontrado tarefasDiarias.txt. Migrando para o SQLite...")
        try:
            init_db()
            with get_db() as db:
                cursor = db.execute("SELECT COUNT(*) FROM tasks")
                if cursor.fetchone()[0] > 0:
                    print("Migração: Banco de dados já possui tarefas. Ignorando migração.")
                    return
            
            tasks = parse_tasks_txt()
            notices = parse_notice_board_txt()
            
            with get_db() as db:
                # Migrar tarefas e subtarefas
                for t in tasks:
                    subtask_title_val = None
                    if t.get('subtask_file'):
                        subtask_title_val = t['subtask_file'].replace('.txt', '')
                        
                    cursor = db.execute("""
                        INSERT INTO tasks (title, description, contract, tag, status, start_date, end_date, subtask_title, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, 1, ?)
                    """, (
                        t['text'],
                        "",
                        t['contract'],
                        t['type'],
                        t['status'],
                        subtask_title_val,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    task_id = cursor.lastrowid
                    
                    if t.get('subtask_file') and os.path.exists(t['subtask_file']):
                        subtasks_list = []
                        with open(t['subtask_file'], 'r', encoding='utf-8') as sf:
                            sf_lines = sf.readlines()
                        for line in sf_lines:
                            stripped = line.strip()
                            if stripped.startswith('*'):
                                is_done = 0
                                st_text = stripped.lstrip('*').strip()
                                if st_text.lower().endswith('- ok'):
                                    is_done = 1
                                    st_text = st_text[:-4].strip()
                                elif '[x]' in line.lower():
                                    is_done = 1
                                    st_text = st_text.replace('[x]', '').replace('[X]', '').strip()
                                subtasks_list.append((task_id, st_text, is_done))
                        if subtasks_list:
                            db.executemany("""
                                INSERT INTO subtasks (task_id, text, is_done)
                                VALUES (?, ?, ?)
                            """, subtasks_list)
                            
                # Migrar quadro de avisos
                for section in notices:
                    section_title = section['title']
                    for item in section['items']:
                        item_text = item['text'] if isinstance(item, dict) else item
                        db.execute("""
                            INSERT INTO notices (section, text, is_active, created_at)
                            VALUES (?, ?, 1, ?)
                        """, (section_title, item_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                db.commit()
            
            shutil.copyfile(TASKS_FILE, TASKS_FILE + '.old')
            os.remove(TASKS_FILE)
            print("Migração concluída com sucesso!")
        except Exception as e:
            print(f"Erro na migração: {e}")

# --- BANCO DE DADOS PERSISTENCE HELPERS ---
def parse_tasks():
    init_db()
    migrate_txt_to_sqlite()
    
    tasks = []
    try:
        with get_db() as db:
            cursor = db.execute("""
                SELECT t.*, 
                       (SELECT json_group_array(
                           json_object('id', s.id, 'text', s.text, 'done', s.is_done)
                       ) FROM subtasks s WHERE s.task_id = t.id) as subtasks_json
                FROM tasks t
                WHERE t.is_active = 1 AND t.status != 'done'
                ORDER BY t.id ASC
            """)
            rows = cursor.fetchall()
            for row in rows:
                subtasks_list = json.loads(row['subtasks_json']) if row['subtasks_json'] else []
                tasks.append({
                    'id': row['id'],
                    'start_idx': row['id'],
                    'contract': row['contract'],
                    'type': row['tag'],
                    'text': row['title'],
                    'description': row['description'] or "",
                    'status': row['status'],
                    'start_date': row['start_date'] or "",
                    'end_date': row['end_date'] or "",
                    'subtask_title': row['subtask_title'] or "",
                    'subtask_file': row['subtask_title'] + '.txt' if row['subtask_title'] else None,
                    'subtasks': subtasks_list
                })
    except Exception as e:
        print(f"Erro ao buscar tarefas: {e}")
    return tasks

def parse_notice_board():
    init_db()
    migrate_txt_to_sqlite()
    
    sections = {}
    try:
        with get_db() as db:
            cursor = db.execute("SELECT id, section, text FROM notices WHERE is_active = 1 ORDER BY id ASC")
            rows = cursor.fetchall()
            for row in rows:
                sec = row['section'].upper()
                if sec not in sections:
                    sections[sec] = []
                sections[sec].append({
                    'line_idx': row['id'],
                    'text': row['text']
                })
    except Exception as e:
        print(f"Erro ao buscar avisos: {e}")
        
    notices = []
    for title, items in sections.items():
        notices.append({
            'title': title,
            'items': items
        })
    return notices

def append_to_history(block, contract, task_type):
    now_str = datetime.now().strftime("%d/%m/%Y - %H:%M")
    entry = f"[{contract}] {task_type.upper()}\n"
    entry += f"Data de Conclusão: {now_str}\n"
    entry += '\n'.join(block) + "\n"
    entry += "-" * 60 + "\n\n"
    
    mode = 'a' if os.path.exists(HISTORY_FILE) else 'w'
    with open(HISTORY_FILE, mode, encoding='utf-8') as f:
        f.write(entry)

def make_backup():
    # Mantido para compatibilidade, sem efeito sobre SQLite
    pass

def insert_task_in_file(contract, tag, text):
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO tasks (title, description, contract, tag, status, is_active, created_at)
                VALUES (?, '', ?, ?, 'todo', 1, ?)
            """, (text, contract, tag, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            db.commit()
        return True
    except Exception as e:
        print(f"Erro ao inserir tarefa no DB: {e}")
        return False

def insert_deadline_in_file(section_title, text):
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO notices (section, text, is_active, created_at)
                VALUES (?, ?, 1, ?)
            """, (section_title, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            db.commit()
        return True
    except Exception as e:
        print(f"Erro ao inserir aviso no DB: {e}")
        return False

def update_task_in_file(task_id, new_status, contract, task_type, expected_text_start):
    try:
        with get_db() as db:
            if new_status == 'done':
                cursor = db.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                if row:
                    append_to_history([row['title']], contract, task_type)
                db.execute("UPDATE tasks SET status = 'done', is_active = 1 WHERE id = ?", (task_id,))
            else:
                db.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
            db.commit()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def delete_task_from_file(task_id):
    try:
        with get_db() as db:
            db.execute("UPDATE tasks SET is_active = 0 WHERE id = ?", (task_id,))
            db.commit()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def delete_notice_from_file(notice_id):
    try:
        with get_db() as db:
            db.execute("UPDATE notices SET is_active = 0 WHERE id = ?", (notice_id,))
            db.commit()
        return True, "Success"
    except Exception as e:
        return False, str(e)

# --- ROTAS FLASK ---
@app.route('/')
def index():
    tasks = parse_tasks()
    notices = parse_notice_board()
    return render_template('index.html', tasks=tasks, notices=notices)

@app.route('/add_item', methods=['POST'])
def add_item():
    data = request.json
    item_type = data.get('item_type')
    
    if not item_type:
        return jsonify({"success": False, "error": "Tipo de item não especificado"}), 400
        
    if item_type == 'task':
        contract = data.get('contract')
        tag = data.get('tag')
        text = data.get('text')
        if not contract or not tag or not text:
            return jsonify({"success": False, "error": "Contrato, tag e texto são obrigatórios"}), 400
        success = insert_task_in_file(contract, tag, text)
        return jsonify({"success": success})
    elif item_type == 'notice':
        section = data.get('section')
        text = data.get('text')
        if not section or not text:
            return jsonify({"success": False, "error": "Seção e texto são obrigatórios"}), 400
        success = insert_deadline_in_file(section, text)
        return jsonify({"success": success})
    else:
        return jsonify({"success": False, "error": "Tipo de item inválido"}), 400

@app.route('/avisos')
def get_avisos():
    notices = parse_notice_board()
    return jsonify(notices)

@app.route('/update', methods=['POST'])
def update_status():
    data = request.json
    start_idx = data.get('id')
    new_status = data.get('status')
    contract = data.get('contract')
    task_type = data.get('type')
    expected_text = data.get('text', '')
    
    if start_idx is None or not new_status:
        return jsonify({"success": False, "error": "Invalid data"}), 400
        
    success, msg = update_task_in_file(start_idx, new_status, contract, task_type, expected_text)
    return jsonify({"success": success, "error": msg})

@app.route('/subtasks/<filename>')
def get_subtasks(filename):
    subtask_title = filename.replace('.txt', '')
    try:
        with get_db() as db:
            cursor = db.execute("SELECT id FROM tasks WHERE subtask_title = ? AND is_active = 1", (subtask_title,))
            task = cursor.fetchone()
            if not task:
                return jsonify([])
            
            task_id = task['id']
            cursor = db.execute("SELECT id, text, is_done FROM subtasks WHERE task_id = ?", (task_id,))
            rows = cursor.fetchall()
            
            subtasks = []
            for row in rows:
                subtasks.append({
                    'id': row['id'],
                    'text': row['text'],
                    'done': bool(row['is_done'])
                })
            return jsonify(subtasks)
    except Exception as e:
        print(f"Erro ao buscar subtarefas: {e}")
        return jsonify([])

@app.route('/toggle_subtask', methods=['POST'])
def toggle_subtask():
    data = request.json
    subtask_id = data.get('id')
    is_done = data.get('done')
    
    if subtask_id is None:
        return jsonify({"success": False, "error": "Invalid data"}), 400
        
    try:
        with get_db() as db:
            db.execute("UPDATE subtasks SET is_done = ? WHERE id = ?", (1 if is_done else 0, subtask_id))
            db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/delete_task', methods=['POST'])
def delete_task_route():
    data = request.json
    start_idx = data.get('id')
    if start_idx is None:
        return jsonify({"success": False, "error": "ID da tarefa não informado"}), 400
    success, msg = delete_task_from_file(start_idx)
    return jsonify({"success": success, "error": msg})

@app.route('/delete_notice', methods=['POST'])
def delete_notice_route():
    data = request.json
    line_idx = data.get('line_idx')
    if line_idx is None:
        return jsonify({"success": False, "error": "Índice da linha não informado"}), 400
    success, msg = delete_notice_from_file(line_idx)
    return jsonify({"success": success, "error": msg})

# --- NOVAS ROTAS DE EDIÇÃO DE CARDS E LOGINS ---
@app.route('/api/task/<int:task_id>')
def get_task_details(task_id):
    try:
        with get_db() as db:
            cursor = db.execute("SELECT * FROM tasks WHERE id = ? AND is_active = 1", (task_id,))
            task = cursor.fetchone()
            if not task:
                return jsonify({"error": "Tarefa não encontrada"}), 404
                
            cursor = db.execute("SELECT id, text, is_done FROM subtasks WHERE task_id = ?", (task_id,))
            sub_rows = cursor.fetchall()
            subtasks = [{"id": r['id'], "text": r['text'], "done": bool(r['is_done'])} for r in sub_rows]
            
            return jsonify({
                "id": task['id'],
                "title": task['title'],
                "description": task['description'] or "",
                "contract": task['contract'],
                "tag": task['tag'],
                "start_date": task['start_date'] or "",
                "end_date": task['end_date'] or "",
                "subtask_title": task['subtask_title'] or "",
                "subtasks": subtasks
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/edit_task', methods=['POST'])
def edit_task():
    data = request.json
    task_id = data.get('id')
    title = data.get('title')
    description = data.get('description', '')
    contract = data.get('contract')
    tag = data.get('tag')
    start_date_val = data.get('start_date') or None
    end_date_val = data.get('end_date') or None
    subtask_title_val = data.get('subtask_title', '').strip()
    subtasks_text = data.get('subtasks_text', '')
    
    if not task_id or not title:
        return jsonify({"success": False, "error": "ID e título são obrigatórios"}), 400
        
    try:
        with get_db() as db:
            db.execute("""
                UPDATE tasks 
                SET title = ?, description = ?, contract = ?, tag = ?, start_date = ?, end_date = ?, subtask_title = ?
                WHERE id = ?
            """, (title, description, contract, tag, start_date_val, end_date_val, subtask_title_val, task_id))
            
            db.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
            
            subtasks_lines = subtasks_text.split('\n')
            subtasks_list = []
            for line in subtasks_lines:
                line_stripped = line.strip()
                if line_stripped:
                    text_clean = line_stripped.lstrip('*').lstrip('-').strip()
                    if text_clean:
                        is_done = 0
                        if text_clean.lower().endswith('- ok') or '[x]' in line_stripped.lower():
                            is_done = 1
                            if text_clean.lower().endswith('- ok'):
                                text_clean = text_clean[:-4].strip()
                            else:
                                text_clean = text_clean.replace('[x]', '').replace('[X]', '').strip()
                        subtasks_list.append((task_id, text_clean, is_done))
                        
            if subtasks_list:
                db.executemany("""
                    INSERT INTO subtasks (task_id, text, is_done)
                    VALUES (?, ?, ?)
                """, subtasks_list)
                
            db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/logins')
def get_logins():
    try:
        with get_db() as db:
            cursor = db.execute("SELECT id, label, username, password FROM logins WHERE is_active = 1 ORDER BY id ASC")
            rows = cursor.fetchall()
            logins = []
            for row in rows:
                logins.append({
                    'id': row['id'],
                    'label': row['label'],
                    'user': row['username'],
                    'pwd': row['password']
                })
            return jsonify(logins)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add_login', methods=['POST'])
def add_login():
    data = request.json
    label = data.get('label')
    username = data.get('user')
    password = data.get('pwd')
    
    if not label or not username:
        return jsonify({"success": False, "error": "Sistema e Usuário são obrigatórios"}), 400
        
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO logins (label, username, password, is_active)
                VALUES (?, ?, ?, 1)
            """, (label, username, password))
            db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/delete_login', methods=['POST'])
def delete_login():
    data = request.json
    login_id = data.get('id')
    if login_id is None:
        return jsonify({"success": False, "error": "ID do login não informado"}), 400
    try:
        with get_db() as db:
            db.execute("UPDATE logins SET is_active = 0 WHERE id = ?", (login_id,))
            db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("Iniciando o Kanban Semanal...")
    print("Acesse http://127.0.0.1:5000 no seu navegador.")
    init_db()
    migrate_txt_to_sqlite()
    app.run(debug=True, port=5000)
