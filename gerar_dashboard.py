import os
import re
import random
from datetime import datetime
import base64

def generate_dashboard():
    # Folder onde o script e os txts estão
    folder_path = "."
    files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    
    # Categorias principais
    categories = {
        'INTO': {},
        'Jardim Botânico RJ': {},
        'Outros': {}
    }
    
    # Palavras-chave
    kw_into = ['into']
    kw_jbrj = ['jardim botânico', 'jardim botanico', 'jbrj']
    
    # Variáveis de parsing
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue # Ignorar linhas vazias
                
                # Identificar se é tarefa
                task_match = re.match(r'^-\s+\[([xX\s])\]\s+(.*)$', line)
                if task_match:
                    item_type = 'task'
                    status_char = task_match.group(1).lower()
                    status = (status_char == 'x')
                    text = task_match.group(2)
                else:
                    item_type = 'note'
                    status = False
                    text = line
                
                # Definir categoria verificando palavras-chave
                text_lower = text.lower()
                category = 'Outros'
                for kw in kw_into:
                    if kw in text_lower:
                        category = 'INTO'
                        break
                if category == 'Outros':
                    for kw in kw_jbrj:
                        if kw in text_lower:
                            category = 'Jardim Botânico RJ'
                            break
                
                # Garantir estrutura
                if filename not in categories[category]:
                    categories[category][filename] = []
                    
                # Parsing de referências simples @arquivo.txt
                text = re.sub(r'@([\w\s.-]+\.txt)', r'<a href="#\1" class="ref-link">@\1</a>', text)
                
                categories[category][filename].append({
                    'type': item_type,
                    'status': status,
                    'text': text,
                    'raw_text': line
                })

    # Diferencial: Frase motivacional
    quotes = [
        "Foco no progresso, não na perfeição.",
        "Execute primeiro, ajuste depois.",
        "Menos planejamento, mais entrega."
    ]
    quote = random.choice(quotes)
    date_str = datetime.now().strftime("%d/%m/%Y")
    
    # Gerando o HTML
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Diário</title>
    <style>
        :root {{
            --bg: #f5f7fa;
            --text: #2c3e50;
            --card-bg: #ffffff;
            --into-color: #3498db;
            --jbrj-color: #2ecc71;
            --outros-color: #95a5a6;
            --completed-color: #7f8c8d;
            --border: #e2e8f0;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }}
        .header {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .header-left h1 {{
            margin: 0;
            font-size: 26px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .header-left .date-badge {{
            font-size: 14px;
            background: #eef2f7;
            padding: 4px 10px;
            border-radius: 20px;
            color: #5b6b79;
            font-weight: 500;
        }}
        .quote {{
            font-style: italic;
            color: #64748b;
            margin-top: 8px;
            font-size: 15px;
        }}
        .stats {{
            display: flex;
            gap: 12px;
        }}
        .stat-box {{
            background: var(--bg);
            padding: 12px 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid var(--border);
            min-width: 80px;
        }}
        .stat-box.total div {{ color: var(--text); font-weight: 700; font-size: 24px; }}
        .stat-box.pending div {{ color: #e74c3c; font-weight: 700; font-size: 24px; }}
        .stat-box.completed div {{ color: var(--jbrj-color); font-weight: 700; font-size: 24px; }}
        
        .container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 24px;
        }}
        
        .section {{
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            padding: 24px;
        }}
        .section h2 {{
            margin-top: 0;
            border-bottom: 2px solid;
            padding-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 20px;
            margin-bottom: 20px;
        }}
        .section-INTO h2 {{ border-color: var(--into-color); }}
        .section-JBRJ h2 {{ border-color: var(--jbrj-color); }}
        .section-Outros h2 {{ border-color: var(--outros-color); }}
        
        details {{
            margin-bottom: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
            background: #fafafa;
        }}
        summary {{
            padding: 12px 16px;
            cursor: pointer;
            font-weight: 600;
            list-style: none; /* Hide default arrow */
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        summary::-webkit-details-marker {{
            display: none;
        }}
        summary::after {{
            content: '▼';
            font-size: 12px;
            color: #888;
            transition: transform 0.2s;
        }}
        details[open] summary::after {{
            transform: rotate(180deg);
        }}
        summary:hover {{
            background: #f0f4f8;
        }}
        .tab-content {{
            padding: 12px;
            background: #fff;
            border-top: 1px solid var(--border);
        }}
        
        .item {{
            margin-bottom: 8px;
            padding: 10px;
            border-radius: 6px;
            background: #ffffff;
            border: 1px solid #edf2f7;
            border-left: 4px solid transparent;
            transition: all 0.2s;
        }}
        .item:last-child {{
            margin-bottom: 0;
        }}
        .item:hover {{
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            border-color: #cbd5e1;
        }}
        .item.task {{
            border-left-color: #3498db;
        }}
        .item.note {{
            border-left-color: #f39c12;
            font-size: 0.95em;
            color: #475569;
        }}
        
        .task-label {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            cursor: pointer;
            margin: 0;
        }}
        .task-label input[type="checkbox"] {{
            margin-top: 4px;
            cursor: pointer;
            width: 18px;
            height: 18px;
            accent-color: var(--jbrj-color);
        }}
        .task-text {{
            flex: 1;
            transition: color 0.2s, text-decoration 0.2s;
            line-height: 1.4;
        }}
        .completed .task-text {{
            text-decoration: line-through;
            color: var(--completed-color);
        }}
        .ref-link {{
            color: #2980b9;
            text-decoration: none;
            background: #ebf5fb;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 0.9em;
        }}
        .ref-link:hover {{
            background: #d4e6f1;
            text-decoration: underline;
        }}
        
        /* Highlight specific anchors */
        details:target summary {{
            background-color: #ffffcc;
        }}
        
        @media (max-width: 768px) {{
            .header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .stats {{
                width: 100%;
                justify-content: space-between;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <h1>Painel Diário <span class="date-badge">{date_str}</span></h1>
            <div class="quote">"{quote}"</div>
        </div>
        <div class="stats">
            <div class="stat-box completed">
                Concluídas<br><div id="count-completed">0</div>
            </div>
            <div class="stat-box pending">
                Pendentes<br><div id="count-pending">0</div>
            </div>
            <div class="stat-box total">
                Total<br><div id="count-total">0</div>
            </div>
        </div>
    </div>
    
    <div class="container">
"""
    
    colors = {
        'INTO': '🔵',
        'Jardim Botânico RJ': '🟢',
        'Outros': '⚪'
    }
    class_map = {
        'INTO': 'section-INTO',
        'Jardim Botânico RJ': 'section-JBRJ',
        'Outros': 'section-Outros'
    }
    
    for cat_name, files_dict in categories.items():
        # Ignorar seção se estiver vazia
        if not files_dict:
            continue
            
        html += f'''
        <div class="section {class_map[cat_name]}">
            <h2>{colors[cat_name]} {cat_name}</h2>
'''
        for filename, items in files_dict.items():
            html += f'''
            <details open id="{filename}">
                <summary>{filename}</summary>
                <div class="tab-content">
'''
            for item in items:
                if item['type'] == 'task':
                    # Gerar ID persistente baseado no nome do arquivo e texto original para manter o track mesmo editando status no TXT
                    task_id_raw = f"{filename}::{item['raw_text'].replace('[x]', '[ ]').replace('[X]', '[ ]')}".encode('utf-8')
                    task_id = base64.b64encode(task_id_raw).decode('utf-8')
                    checked_attr = 'checked' if item['status'] else ''
                    html += f'''
                    <div class="item task">
                        <label class="task-label">
                            <input type="checkbox" class="task-checkbox" data-task-id="{task_id}" data-default-checked="{str(item['status']).lower()}" {checked_attr}>
                            <span class="task-text">{item['text']}</span>
                        </label>
                    </div>
'''
                else:
                    html += f'''
                    <div class="item note">
                        📝 {item['text']}
                    </div>
'''
            html += '''
                </div>
            </details>
'''
        html += '''
        </div>
'''
        
    html += """
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const checkboxes = document.querySelectorAll('.task-checkbox');
            const totalEl = document.getElementById('count-total');
            const pendingEl = document.getElementById('count-pending');
            const completedEl = document.getElementById('count-completed');
            
            function updateCounters() {
                let total = checkboxes.length;
                let completed = 0;
                checkboxes.forEach(cb => {
                    const itemDiv = cb.closest('.item');
                    if(cb.checked) {
                        completed++;
                        itemDiv.classList.add('completed');
                    } else {
                        itemDiv.classList.remove('completed');
                    }
                });
                let pending = total - completed;
                
                totalEl.textContent = total;
                pendingEl.textContent = pending;
                completedEl.textContent = completed;
            }

            checkboxes.forEach(cb => {
                const id = cb.getAttribute('data-task-id');
                
                // Prioriza localStorage se existir o registro de click (persistencia estendida)
                const savedState = localStorage.getItem('task_' + id);
                if (savedState !== null) {
                    cb.checked = savedState === 'true';
                }
                
                cb.addEventListener('change', (e) => {
                    localStorage.setItem('task_' + id, e.target.checked);
                    updateCounters();
                });
            });
            
            // Contagem e formatação inicial baseada nos checkboxes
            updateCounters();
        });
    </script>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Dashboard gerado com sucesso: index.html")

if __name__ == "__main__":
    generate_dashboard()
