import os
import re
import json
import random
import urllib.request
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)

MENSAGENS = [
    {"texto": "Nascer, morrer, renascer ainda e progredir sempre, tal é a lei.", "autor": "Allan Kardec"},
    {"texto": "O software é uma grande combinação entre arte e engenharia.", "autor": "Bill Gates"},
    {"texto": "A caridade é o dever moral de todo o homem, sem a qual não há verdadeira civilização.", "autor": "Allan Kardec"},
    {"texto": "A máquina analítica não tem qualquer pretensão de criar algo por si mesma. Pode fazer qualquer coisa que saibamos como ordená-la a executar.", "autor": "Ada Lovelace"}
]

def fetch_quotes_from_web():
    temas = ["tecnologia", "frases_espiritas"]
    hoje = date.today()
    seed = hoje.year * 10000 + hoje.month * 100 + hoje.day
    random.seed(seed)
    
    tema_do_dia = random.choice(temas)
    
    try:
        url = f"https://www.pensador.com/{tema_do_dia}/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=4) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        frases = re.findall(r'<p class="frase[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
        autores = re.findall(r'<span class="autor[^>]*>(.*?)</span>', html, re.DOTALL | re.IGNORECASE)
        
        def limpa_html(texto):
            return re.sub(r'<[^>]+>', '', texto).replace('\n', ' ').strip()
            
        if frases and autores:
            todas = [{"texto": limpa_html(f), "autor": limpa_html(a)} for f, a in zip(frases, autores)]
            return random.choice(todas)
    except Exception as e:
        print("Aviso: Falha ao buscar mensagem na web, usando lista interna.")
    
    return random.choice(MENSAGENS)

def get_mensagem_do_dia():
    CACHE_FILE = 'mensagem_cache.json'
    hoje_str = date.today().strftime('%Y-%m-%d')
    
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('data') == hoje_str:
                    return data.get('mensagem')
        except:
            pass
            
    msg = fetch_quotes_from_web()
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'data': hoje_str, 'mensagem': msg}, f, ensure_ascii=False)
    except:
        pass
        
    return msg

TASKS_FILE = 'tarefasDiarias.txt'
HISTORY_FILE = 'historico.txt'

def parse_notice_board():
    """Lê seções de aviso do arquivo de tarefas (deploy, importante, etc.)"""
    if not os.path.exists(TASKS_FILE):
        return []
    
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    notices = []
    lines = content.split('\n')
    
    # Seções que queremos capturar como avisos (não são Demandas/Melhorias do Kanban)
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
    
    for line in lines:
        stripped = line.strip()
        
        # Detecta cabeçalho (# ou ##)
        if stripped.startswith('#'):
            header_text = stripped.lstrip('#').strip()
            header_upper = header_text.upper()
            
            # Verifica se é seção de aviso
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
        
        # Captura conteúdo da seção de aviso
        if current_section and stripped and not stripped.startswith('-' * 5):
            # Remove marcadores de lista
            text = stripped.lstrip('*').lstrip('-').strip()
            if text:
                current_items.append(text)
    
    flush_section()
    return notices

def parse_tasks():
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
            # Extract only the text part, without prefix
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
            
            # Detect if there's a reference to another block/file
            subtask_file = None
            # Flexible regex for different quotes and optional "o"
            ref_match = re.search(r'consultar\s+(?:o\s+)?bloco\s+["\u201c\u201d\']([^"\u201c\u201d\']+)["\u201c\u201d\']', full_text, re.IGNORECASE)
            if ref_match:
                subtask_file = ref_match.group(1)
                # Ensure .txt extension
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

def append_to_history(block, contract, task_type):
    now_str = datetime.now().strftime("%d/%m/%Y - %H:%M")
    
    entry = f"[{contract}] {task_type.upper()}\n"
    entry += f"Data de Conclusão: {now_str}\n"
    entry += '\n'.join(block) + "\n"
    entry += "-" * 60 + "\n\n"
    
    mode = 'a' if os.path.exists(HISTORY_FILE) else 'w'
    with open(HISTORY_FILE, mode, encoding='utf-8') as f:
        f.write(entry)

def update_task_in_file(start_idx, new_status, contract, task_type, expected_text_start):
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
        
    if start_idx >= len(lines):
        return False, "Index out of range"
        
    line = lines[start_idx]
    if not line.strip().startswith('*'):
        return False, "File changed unexpectedly"
        
    task_match = re.match(r'^([\s\*]+)(?:\[Em andamento\]\s+)?(.*)', line, re.IGNORECASE)
    if not task_match:
        return False, "Parse error"
        
    prefix = task_match.group(1)
    text = task_match.group(2)
    
    # Very basic validation to ensure we are editing the right task
    if expected_text_start and not text.startswith(expected_text_start[:20]):
        return False, "Task mismatch, file might have been edited."
    
    if new_status == 'todo':
        lines[start_idx] = prefix + text
    elif new_status == 'doing':
        lines[start_idx] = prefix + "[Em andamento] " + text
    elif new_status == 'done':
        end_idx = start_idx
        j = start_idx + 1
        while j < len(lines):
            next_stripped = lines[j].strip()
            if next_stripped == '' or next_stripped.startswith('*') or next_stripped.startswith('#') or next_stripped.startswith('-'):
                break
            j += 1
        end_idx = j - 1
        
        block = [prefix + text] + lines[start_idx+1:end_idx+1]
        
        append_to_history(block, contract, task_type)
        
        del lines[start_idx:end_idx+1]
    
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        
    return True, "Success"

@app.route('/')
def index():
    tasks = parse_tasks()
    notices = parse_notice_board()
    mensagem = get_mensagem_do_dia()
    return render_template('index.html', tasks=tasks, notices=notices, mensagem_do_dia=mensagem)

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
    # Security: don't allow accessing files outside the directory or sensitive ones
    if not filename.endswith('.txt') or '/' in filename or '\\' in filename or filename == TASKS_FILE:
        return jsonify([])
        
    if not os.path.exists(filename):
        return jsonify([])
        
    subtasks = []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('*'):
            # Detect [x] or - OK or nothing
            is_done = False
            text = stripped.lstrip('*').strip()
            
            if text.lower().endswith('- ok'):
                is_done = True
                text = text[:-4].strip()
            elif '[x]' in line.lower():
                is_done = True
                text = text.replace('[x]', '').replace('[X]', '').strip()
            
            subtasks.append({
                'id': i,
                'text': text,
                'done': is_done
            })
            
    if not subtasks:
        # If no explicit checklist, return the file content to be viewed
        return jsonify({"content": "".join(lines)})
            
    return jsonify(subtasks)

@app.route('/toggle_subtask', methods=['POST'])
def toggle_subtask():
    data = request.json
    filename = data.get('filename')
    line_idx = data.get('id')
    is_done = data.get('done')
    
    if not filename or line_idx is None:
        return jsonify({"success": False, "error": "Invalid data"}), 400
        
    if not os.path.exists(filename):
        return jsonify({"success": False, "error": "File not found"}), 404
        
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    if line_idx >= len(lines):
        return jsonify({"success": False, "error": "Index out of range"}), 400
        
    line = lines[line_idx]
    if not line.strip().startswith('*'):
        return jsonify({"success": False, "error": "Not a task line"}), 400
        
    # Update logic
    stripped = line.rstrip()
    if is_done:
        if not stripped.lower().endswith('- ok'):
            lines[line_idx] = stripped + " - OK\n"
    else:
        if stripped.lower().endswith('- ok'):
            lines[line_idx] = stripped[:-4].rstrip() + "\n"
            
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        
    return jsonify({"success": True})

if __name__ == '__main__':
    print("Iniciando o Kanban Semanal...")
    print("Acesse http://127.0.0.1:5000 no seu navegador.")
    app.run(debug=True, port=5000)
