import os
import pytest
import kanban_semanal

@pytest.fixture
def setup_test_file():
    original_db = kanban_semanal.DATABASE
    kanban_semanal.DATABASE = 'test_kanban.db'
    
    if os.path.exists(kanban_semanal.DATABASE):
        os.remove(kanban_semanal.DATABASE)
        
    kanban_semanal.init_db()
    
    with kanban_semanal.get_db() as db:
        # Insere tarefas de teste
        db.execute("""
            INSERT INTO tasks (title, contract, tag, status, is_active, created_at)
            VALUES ('Aplicação Gestão Acadêmica', 'INTO', 'Demandas', 'doing', 1, '2026-08-14 12:00:00')
        """)
        db.execute("""
            INSERT INTO tasks (title, contract, tag, status, is_active, created_at)
            VALUES ('Ajustar layout do formulário', 'INTO', 'Demandas', 'todo', 1, '2026-08-14 12:00:00')
        """)
        db.execute("""
            INSERT INTO tasks (title, contract, tag, status, is_active, created_at)
            VALUES ('Estudar testes automatizados', 'JBRJ', 'Melhorias', 'todo', 1, '2026-08-14 12:00:00')
        """)
        db.execute("""
            INSERT INTO tasks (title, contract, tag, status, is_active, created_at)
            VALUES ('Corrigir bug da Kelly', 'INTO', 'Correções', 'todo', 1, '2026-08-14 12:00:00')
        """)
        
        # Insere avisos de teste
        db.execute("""
            INSERT INTO notices (section, text, is_active, created_at)
            VALUES ('IMPORTANTE', 'VPN', 1, '2026-08-14 12:00:00')
        """)
        db.execute("""
            INSERT INTO notices (section, text, is_active, created_at)
            VALUES ('IMPORTANTE', 'Git', 1, '2026-08-14 12:00:00')
        """)
        db.execute("""
            INSERT INTO notices (section, text, is_active, created_at)
            VALUES ('PRAZOS E DEADLINES', 'Gestão Acadêmica - Prazo: 18/08/2026', 1, '2026-08-14 12:00:00')
        """)
        db.execute("""
            INSERT INTO notices (section, text, is_active, created_at)
            VALUES ('PRAZOS E DEADLINES', 'Atualizar o Manual do Jabot - Prazo 14/08/2026', 1, '2026-08-14 12:00:00')
        """)
        db.execute("""
            INSERT INTO notices (section, text, is_active, created_at)
            VALUES ('FÉRIAS', '2026- Férias', 1, '2026-08-14 12:00:00')
        """)
        db.commit()
        
    yield
    
    if os.path.exists(kanban_semanal.DATABASE):
        os.remove(kanban_semanal.DATABASE)
    kanban_semanal.DATABASE = original_db

def test_parse_notice_board(setup_test_file):
    notices = kanban_semanal.parse_notice_board()
    assert len(notices) >= 2
    
    titles = [n['title'] for n in notices]
    assert 'IMPORTANTE' in titles
    assert 'PRAZOS E DEADLINES' in titles
    
    prazos_section = next(n for n in notices if n['title'] == 'PRAZOS E DEADLINES')
    assert len(prazos_section['items']) == 2
    prazos_texts = [i['text'] for i in prazos_section['items']]
    assert "Gestão Acadêmica - Prazo: 18/08/2026" in prazos_texts

def test_parse_tasks(setup_test_file):
    tasks = kanban_semanal.parse_tasks()
    assert len(tasks) == 4
    
    into_demanda = [t for t in tasks if t['contract'] == 'INTO' and t['type'] == 'Demandas']
    assert len(into_demanda) == 2
    assert into_demanda[0]['text'].strip() == 'Aplicação Gestão Acadêmica'
    assert into_demanda[0]['status'] == 'doing'
    
    into_correcao = [t for t in tasks if t['contract'] == 'INTO' and t['type'] == 'Correções']
    assert len(into_correcao) == 1
    assert into_correcao[0]['text'].strip() == 'Corrigir bug da Kelly'

def test_insert_task_in_file_existing_section(setup_test_file):
    success = kanban_semanal.insert_task_in_file('INTO', 'Demandas', 'Nova demanda de teste')
    assert success is True
    
    tasks = kanban_semanal.parse_tasks()
    into_demanda = [t for t in tasks if t['contract'] == 'INTO' and t['type'] == 'Demandas']
    assert len(into_demanda) == 3
    assert into_demanda[-1]['text'].strip() == 'Nova demanda de teste'

def test_insert_task_in_file_new_section(setup_test_file):
    success = kanban_semanal.insert_task_in_file('JBRJ', 'Estudos', 'Estudar Machine Learning')
    assert success is True
    
    tasks = kanban_semanal.parse_tasks()
    jbrj_estudos = [t for t in tasks if t['contract'] == 'JBRJ' and t['type'] == 'Estudos']
    assert len(jbrj_estudos) == 1
    assert jbrj_estudos[0]['text'].strip() == 'Estudar Machine Learning'

def test_insert_deadline_in_file_existing_section(setup_test_file):
    success = kanban_semanal.insert_deadline_in_file('Prazos e Deadlines', 'Fazer deploy - Prazo 20/08')
    assert success is True
    
    notices = kanban_semanal.parse_notice_board()
    prazos_section = next(n for n in notices if n['title'] == 'PRAZOS E DEADLINES')
    assert len(prazos_section['items']) == 3
    prazos_texts = [i['text'] for i in prazos_section['items']]
    assert "Fazer deploy - Prazo 20/08" in prazos_texts

def test_delete_task(setup_test_file):
    tasks = kanban_semanal.parse_tasks()
    original_count = len(tasks)
    
    first_task = tasks[0]
    success, msg = kanban_semanal.delete_task_from_file(first_task['id'])
    assert success is True
    assert msg == "Success"
    
    tasks_new = kanban_semanal.parse_tasks()
    assert len(tasks_new) == original_count - 1
    
    task_texts = [t['text'] for t in tasks_new]
    assert 'Aplicação Gestão Acadêmica' not in task_texts

def test_delete_notice(setup_test_file):
    notices = kanban_semanal.parse_notice_board()
    prazos = next(n for n in notices if n['title'] == 'PRAZOS E DEADLINES')
    original_count = len(prazos['items'])
    
    first_notice = prazos['items'][0]
    success, msg = kanban_semanal.delete_notice_from_file(first_notice['line_idx'])
    assert success is True
    assert msg == "Success"
    
    notices_new = kanban_semanal.parse_notice_board()
    prazos_new = next(n for n in notices_new if n['title'] == 'PRAZOS E DEADLINES')
    assert len(prazos_new['items']) == original_count - 1
    
    notice_texts = [i['text'] for i in prazos_new['items']]
    assert "Gestão Acadêmica - Prazo: 18/08/2026" not in notice_texts

def test_delete_task_route(setup_test_file):
    client = kanban_semanal.app.test_client()
    
    tasks = kanban_semanal.parse_tasks()
    first_task = tasks[0]
    
    response = client.post('/delete_task', json={'id': first_task['id']})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    tasks_new = kanban_semanal.parse_tasks()
    assert len(tasks_new) == len(tasks) - 1

def test_delete_notice_route(setup_test_file):
    client = kanban_semanal.app.test_client()
    
    notices = kanban_semanal.parse_notice_board()
    prazos = next(n for n in notices if n['title'] == 'PRAZOS E DEADLINES')
    first_notice = prazos['items'][0]
    
    response = client.post('/delete_notice', json={'line_idx': first_notice['line_idx']})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    notices_new = kanban_semanal.parse_notice_board()
    prazos_new = next(n for n in notices_new if n['title'] == 'PRAZOS E DEADLINES')
    assert len(prazos_new['items']) == len(prazos['items']) - 1

def test_edit_task_route(setup_test_file):
    client = kanban_semanal.app.test_client()
    
    tasks = kanban_semanal.parse_tasks()
    task = tasks[0]
    
    payload = {
        'id': task['id'],
        'title': 'Título Editado',
        'description': 'Nova descrição detalhada',
        'contract': 'JBRJ',
        'tag': 'Melhorias',
        'start_date': '2026-08-15',
        'end_date': '2026-08-20',
        'subtask_title': 'novasSubtarefas',
        'subtasks_text': '* Subtarefa 1\n* Subtarefa 2 - OK'
    }
    
    response = client.post('/edit_task', json=payload)
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # Busca os detalhes via API
    response_details = client.get(f"/api/task/{task['id']}")
    assert response_details.status_code == 200
    task_details = response_details.get_json()
    
    assert task_details['title'] == 'Título Editado'
    assert task_details['description'] == 'Nova descrição detalhada'
    assert task_details['contract'] == 'JBRJ'
    assert task_details['tag'] == 'Melhorias'
    assert task_details['start_date'] == '2026-08-15'
    assert task_details['end_date'] == '2026-08-20'
    assert task_details['subtask_title'] == 'novasSubtarefas'
    assert len(task_details['subtasks']) == 2
    assert task_details['subtasks'][0]['text'] == 'Subtarefa 1'
    assert task_details['subtasks'][0]['done'] is False
    assert task_details['subtasks'][1]['text'] == 'Subtarefa 2'
    assert task_details['subtasks'][1]['done'] is True

def test_login_routes(setup_test_file):
    client = kanban_semanal.app.test_client()
    
    # 1. Add login
    response = client.post('/api/add_login', json={
        'label': 'GitHub',
        'user': 'taynaribeiro',
        'pwd': 'secretpassword'
    })
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # 2. Get logins
    response_get = client.get('/api/logins')
    assert response_get.status_code == 200
    logins = response_get.get_json()
    assert len(logins) == 1
    assert logins[0]['label'] == 'GitHub'
    assert logins[0]['user'] == 'taynaribeiro'
    assert logins[0]['pwd'] == 'secretpassword'
    
    # 3. Delete login
    response_del = client.post('/api/delete_login', json={'id': logins[0]['id']})
    assert response_del.status_code == 200
    assert response_del.get_json()['success'] is True
    
    # 4. Verify gone
    response_get2 = client.get('/api/logins')
    assert len(response_get2.get_json()) == 0

def test_add_item_route_complete(setup_test_file):
    client = kanban_semanal.app.test_client()
    
    payload = {
        'item_type': 'task',
        'title': 'Nova Tarefa Completa',
        'description': 'Descrição cadastrada',
        'contract': 'PESSOAL',
        'tag': 'Estudo',
        'start_date': '2026-08-14',
        'end_date': '2026-08-16',
        'subtask_title': 'subCadastro',
        'subtasks_text': '* Passo A\n* Passo B - OK'
    }
    
    response = client.post('/add_item', json=payload)
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # Verifica no DB
    tasks = kanban_semanal.parse_tasks()
    new_task = next(t for t in tasks if t['text'] == 'Nova Tarefa Completa')
    assert new_task['description'] == 'Descrição cadastrada'
    assert new_task['contract'] == 'PESSOAL'
    assert new_task['type'] == 'Estudo'
    assert new_task['start_date'] == '2026-08-14'
    assert new_task['end_date'] == '2026-08-16'
    assert new_task['subtask_title'] == 'subCadastro'
    
    # Verifica subtarefas
    subtasks = new_task['subtasks']
    assert len(subtasks) == 2
    assert subtasks[0]['text'] == 'Passo A'
    assert subtasks[0]['done'] is False
    assert subtasks[1]['text'] == 'Passo B'
    assert subtasks[1]['done'] is True
