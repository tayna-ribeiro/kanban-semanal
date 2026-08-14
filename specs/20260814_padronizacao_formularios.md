# ESPEC - Padronização e Unificação dos Formulários de Criação e Edição

* **Autor:** Antigravity (AI Coding Assistant) & Tayna Ribeiro
* **Data:** 14/08/2026
* **Status:** Concluído

---

## 1. Objetivo e Contexto
Atualmente, existe uma divergência visual e funcional na interface do Kanban Semanal:
* O modal de **Edição** (`#editDialog`) é completo, permitindo definir Título, Descrição detalhada, datas de início/fim e subtarefas estruturadas.
* O modal de **Adição** (`#addDialog`) é básico, permitindo apenas selecionar o Contrato, Tag e preencher a descrição principal da tarefa.

Para garantir consistência na experiência do usuário (UX) e integridade dos dados no banco de dados SQLite, o objetivo desta especificação é **padronizar ambos os formulários**, tornando o modal de criação tão completo quanto o de edição, com suporte a datas, descrição detalhada e inclusão de subtarefas no momento do cadastro.

---

## 2. Requisitos e Critérios de Aceitação

### 2.1 Unificação do Formulário de Criação (`#addDialog`)
- [x] **Campos Avançados na Criação:** A aba "Nova Tarefa" no modal de criação deve conter:
  - Título da Tarefa (campo de texto, obrigatório).
  - Descrição Detalhada (área de texto multilinha, opcional).
  - Contrato (Select: INTO, JBRJ, PESSOAL, OUTROS).
  - Tag/Tipo (Select: Demanda, Melhoria, Correção, Estudo, Ajuste, Documentação).
  - Data de Início e Prazo Final (calendários, opcionais).
  - Título do Bloco de Subtarefas (texto, opcional).
  - Subtarefas (área de texto multilinha, opcional, convertida em itens de checklist no banco).
- [x] **Validação de Título:** Impedir o salvamento se o título da tarefa estiver em branco.

### 2.2 Atualização da API de Criação (`/add_item`)
- [x] **Novos Parâmetros no Backend:** Atualizar a rota `/add_item` no backend para receber todos os campos estendidos de tarefas e inserir na tabela `tasks` e `subtasks` do banco SQLite (seguindo o mesmo padrão de transação e parsing da rota `/edit_task`).
- [x] **Compatibilidade com Quadro de Avisos:** Garantir que a aba "Prazo ou Lembrete" no mesmo modal continue funcionando corretamente para inserir notices no Quadro de Avisos.

---

## 3. Arquitetura e Solução Técnica

### 3.1 Backend (`kanban_semanal.py`)
Atualizar a rota `/add_item` para lidar com a inserção completa:
```python
@app.route('/add_item', methods=['POST'])
def add_item():
    data = request.json
    item_type = data.get('item_type')
    
    if item_type == 'task':
        title = data.get('title')
        description = data.get('description', '')
        contract = data.get('contract')
        tag = data.get('tag')
        start_date = data.get('start_date') or None
        end_date = data.get('end_date') or None
        subtask_title = data.get('subtask_title', '').strip()
        subtasks_text = data.get('subtasks_text', '')
        
        if not title:
            return jsonify({"success": False, "error": "Título é obrigatório"}), 400
            
        try:
            with get_db() as db:
                # 1. Inserir tarefa
                cursor = db.execute("""
                    INSERT INTO tasks (title, description, contract, tag, status, start_date, end_date, subtask_title, is_active, created_at)
                    VALUES (?, ?, ?, ?, 'todo', ?, ?, ?, 1, ?)
                """, (title, description, contract, tag, start_date, end_date, subtask_title, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                task_id = cursor.lastrowid
                
                # 2. Inserir subtarefas
                if subtasks_text.strip():
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
                        db.executemany("INSERT INTO subtasks (task_id, text, is_done) VALUES (?, ?, ?)", subtasks_list)
                db.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
```

### 3.2 Frontend (`templates/index.html`)
Substituir a área antiga da aba "Tarefa" no modal `#addDialog` pelo mesmo formulário estruturado de `#editDialog`.

---

## 4. Plano de Verificação (Testes)

### 4.1 Testes Manuais
1. Abrir o modal **Novo Item**.
2. Preencher a aba **Nova Tarefa** com Título, Descrição, data de início/fim e 2 subtarefas.
3. Salvar e verificar se o card aparece na coluna "A Fazer" com os prazos formatados e as subtarefas disponíveis no checklist.
4. Adicionar outro item e deixar o Título em branco para verificar a mensagem de erro.

### 4.2 Testes Automatizados (`tests/test_kanban.py`)
Atualizar os testes de inserção de tarefas para enviar o payload completo (com título, datas e subtarefas) e verificar no banco temporário se foram inseridos com sucesso.
