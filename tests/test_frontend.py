import os
import pytest
from bs4 import BeautifulSoup
import kanban_semanal

@pytest.fixture
def test_setup():
    """Configura um banco SQLite de teste isolado e insere dados para validar a interface."""
    original_db = kanban_semanal.DATABASE
    kanban_semanal.DATABASE = 'test_frontend.db'
    
    if os.path.exists(kanban_semanal.DATABASE):
        os.remove(kanban_semanal.DATABASE)
        
    kanban_semanal.init_db()
    
    with kanban_semanal.get_db() as db:
        # Tarefa em "A Fazer" com detalhes completos
        db.execute("""
            INSERT INTO tasks (
                title, description, contract, tag, status, 
                start_date, end_date, subtask_title, is_active, created_at
            ) VALUES (
                'Desenvolver Módulo Acadêmico', 
                'Implementar tela de notas e frequência.', 
                'INTO', 
                'Demanda', 
                'todo', 
                '2026-09-01', 
                '2026-09-10', 
                'Subtarefas do Módulo', 
                1, 
                '2026-09-01 10:00:00'
            )
        """)
        task_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO subtasks (task_id, text, is_done) VALUES (?, ?, 0)", (task_id, 'Criar tabelas'))
        db.execute("INSERT INTO subtasks (task_id, text, is_done) VALUES (?, ?, 1)", (task_id, 'Testar endpoints'))

        # Tarefa em "Em Andamento" (JBRJ)
        db.execute("""
            INSERT INTO tasks (
                title, description, contract, tag, status, 
                start_date, end_date, subtask_title, is_active, created_at
            ) VALUES (
                'Atualizar Servidor de Produção', 
                'Realizar upgrade de segurança.', 
                'JBRJ', 
                'Melhoria', 
                'doing', 
                '2026-09-05', 
                '2026-09-06', 
                NULL, 
                1, 
                '2026-09-05 09:00:00'
            )
        """)

        # Tarefa pessoal
        db.execute("""
            INSERT INTO tasks (
                title, description, contract, tag, status, 
                start_date, end_date, subtask_title, is_active, created_at
            ) VALUES (
                'Estudar Arquitetura em Python', 
                NULL, 
                'PESSOAL', 
                'Estudo', 
                'todo', 
                NULL, 
                NULL, 
                NULL, 
                1, 
                '2026-09-06 08:00:00'
            )
        """)

        # Avisos no mural
        db.execute("""
            INSERT INTO notices (section, text, is_active, created_at)
            VALUES ('IMPORTANTE', 'Janela de manutenção às 22h', 1, '2026-09-01 10:00:00')
        """)
        db.execute("""
            INSERT INTO notices (section, text, is_active, created_at)
            VALUES ('PRAZOS E DEADLINES', 'Entrega do relatório - Prazo: 15/09/2026', 1, '2026-09-01 10:00:00')
        """)
        db.execute("""
            INSERT INTO notices (section, text, is_active, created_at)
            VALUES ('DEPLOY', 'Deploy versão 2.4 agendado', 1, '2026-09-01 10:00:00')
        """)

        # Login frequente
        db.execute("""
            INSERT INTO logins (label, username, password, is_active)
            VALUES ('Homologação', 'admin_teste', 'senha123', 1)
        """)

        db.commit()

    client = kanban_semanal.app.test_client()
    yield client

    if os.path.exists(kanban_semanal.DATABASE):
        os.remove(kanban_semanal.DATABASE)
    kanban_semanal.DATABASE = original_db


def test_home_page_status_and_title(test_setup):
    """Garante que a página principal responde com status 200 e título correto."""
    response = test_setup.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.content_type

    soup = BeautifulSoup(response.data, 'html.parser')
    assert soup.title is not None
    assert 'Planejamento Semanal - Kanban' in soup.title.string


def test_kanban_columns_structure(test_setup):
    """Garante a existência das 3 colunas do Kanban com seus atributos de status e contadores."""
    response = test_setup.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    # Valida container do board
    board = soup.find('div', class_='board')
    assert board is not None

    # Valida as 3 colunas esperadas
    col_todo = soup.find('div', id='todo')
    col_doing = soup.find('div', id='doing')
    col_done = soup.find('div', id='done')

    assert col_todo is not None and col_todo.get('data-status') == 'todo'
    assert col_doing is not None and col_doing.get('data-status') == 'doing'
    assert col_done is not None and col_done.get('data-status') == 'done'

    # Valida os contadores visuais
    assert soup.find('span', id='count-todo') is not None
    assert soup.find('span', id='count-doing') is not None
    assert soup.find('span', id='count-done') is not None


def test_tasks_rendered_in_correct_columns(test_setup):
    """Verifica se tarefas com status 'todo' e 'doing' estão em suas respectivas colunas."""
    response = test_setup.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    col_todo = soup.find('div', id='todo')
    todo_cards = col_todo.find_all('div', class_='task-card')
    assert len(todo_cards) == 2

    col_doing = soup.find('div', id='doing')
    doing_cards = col_doing.find_all('div', class_='task-card')
    assert len(doing_cards) == 1

    # Valida o texto dos cards
    todo_texts = [card.find('div', class_='task-text').get_text(strip=True) for card in todo_cards]
    assert 'Desenvolver Módulo Acadêmico' in todo_texts
    assert 'Estudar Arquitetura em Python' in todo_texts

    doing_texts = [card.find('div', class_='task-text').get_text(strip=True) for card in doing_cards]
    assert 'Atualizar Servidor de Produção' in doing_texts


def test_task_card_details_and_badges(test_setup):
    """Valida detalhes do card: badges de contrato, datas, botões de ação e subtarefas."""
    response = test_setup.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    # Localiza o card com detalhes completos
    card = soup.find('div', string=lambda t: t and 'Desenvolver Módulo Acadêmico' in t).find_parent('div', class_='task-card')
    assert card is not None

    # Valida atributos de dados
    assert card.get('data-contract') == 'INTO'
    assert card.get('data-type') == 'Demanda'
    assert card.has_attr('data-id')

    # Valida badge do contrato
    badge = card.find('span', class_='task-badge')
    assert badge is not None
    assert 'badge-INTO' in badge.get('class', [])
    assert 'INTO' in badge.get_text()

    # Valida botões de ação do card (excluir e editar)
    btn_delete = card.find('button', class_='btn-delete-card')
    btn_edit = card.find('button', class_='btn-edit-card')
    assert btn_delete is not None
    assert btn_edit is not None
    assert 'deleteTask(' in btn_delete.get('onclick', '')
    assert 'openEditModal(' in btn_edit.get('onclick', '')

    # Valida botão de subtarefas presente quando houver subtask_title
    btn_subtasks = card.find('button', class_='btn-subtasks')
    assert btn_subtasks is not None
    assert 'Subtarefas do Módulo' in btn_subtasks.get_text()

    # Valida exibição de datas formatadas (DD/MM)
    card_text = card.get_text()
    assert '01/09' in card_text
    assert '10/09' in card_text


def test_notice_board_rendering(test_setup):
    """Valida o bloco do Quadro de Avisos, toggle/recolher e lista de avisos com botão de exclusão."""
    response = test_setup.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    wrapper = soup.find('div', id='noticeBoardWrapper')
    assert wrapper is not None

    toggle_bar = soup.find('div', class_='notice-toggle-bar')
    assert toggle_bar is not None
    assert 'toggleNoticeBoard()' in toggle_bar.get('onclick', '')

    board = soup.find('div', id='noticeBoard')
    assert board is not None

    # Valida cards de avisos
    notice_cards = board.find_all('div', class_='notice-card')
    # Esperamos pelo menos 3 avisos + 1 card de logins
    assert len(notice_cards) >= 4

    # Valida item de aviso e botão de exclusão
    notice_items = board.find_all('div', class_='notice-item')
    assert len(notice_items) >= 3

    first_item = notice_items[0]
    btn_del_notice = first_item.find('button', class_='btn-delete-notice')
    assert btn_del_notice is not None
    assert 'deleteNotice(' in btn_del_notice.get('onclick', '')


def test_frequent_logins_card(test_setup):
    """Valida o card de Logins Frequentes e seus campos de formulário inline."""
    response = test_setup.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    login_card = soup.find('div', id='loginCard')
    assert login_card is not None

    # Lista onde os logins são injetados via JS
    assert login_card.find('div', id='loginList') is not None

    # Campos para adicionar novo login
    assert login_card.find('input', id='loginLabel') is not None
    assert login_card.find('input', id='loginUser') is not None
    assert login_card.find('input', id='loginPwd') is not None

    btn_add = login_card.find('button', class_='btn-add-login')
    assert btn_add is not None
    assert 'addLogin()' in btn_add.get('onclick', '')


def test_add_item_dialog_structure(test_setup):
    """Valida o diálogo de adicionar novo item (tarefa vs prazo) e seus campos."""
    response = test_setup.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    dialog = soup.find('dialog', id='addDialog')
    assert dialog is not None

    # Abas de navegação interna
    tab_task = dialog.find('button', id='tabTask')
    tab_notice = dialog.find('button', id='tabNotice')
    assert tab_task is not None and 'switchTab(\'task\')' in tab_task.get('onclick', '')
    assert tab_notice is not None and 'switchTab(\'notice\')' in tab_notice.get('onclick', '')

    # Seção Tarefa
    assert dialog.find('div', id='formTaskSection') is not None
    assert dialog.find('input', id='taskTitle') is not None
    assert dialog.find('select', id='taskContract') is not None
    assert dialog.find('select', id='taskTag') is not None
    assert dialog.find('textarea', id='taskDescription') is not None
    assert dialog.find('input', id='taskStartDate') is not None
    assert dialog.find('input', id='taskEndDate') is not None
    assert dialog.find('input', id='taskSubtaskTitle') is not None
    assert dialog.find('textarea', id='taskSubtasksText') is not None

    # Seção Aviso / Prazo
    assert dialog.find('div', id='formNoticeSection') is not None
    assert dialog.find('select', id='noticeSection') is not None
    assert dialog.find('textarea', id='noticeText') is not None

    # Botão de salvar
    save_btn = dialog.find('button', class_='btn-primary')
    assert save_btn is not None
    assert 'submitNewItem()' in save_btn.get('onclick', '')


def test_edit_task_dialog_structure(test_setup):
    """Valida o diálogo de editar tarefa e seus campos."""
    response = test_setup.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    dialog = soup.find('dialog', id='editDialog')
    assert dialog is not None

    assert dialog.find('input', id='editTaskId') is not None
    assert dialog.find('input', id='editTaskTitle') is not None
    assert dialog.find('select', id='editTaskContract') is not None
    assert dialog.find('select', id='editTaskTag') is not None
    assert dialog.find('textarea', id='editTaskDescription') is not None
    assert dialog.find('input', id='editTaskStartDate') is not None
    assert dialog.find('input', id='editTaskEndDate') is not None
    assert dialog.find('input', id='editTaskSubtaskTitle') is not None
    assert dialog.find('textarea', id='editTaskSubtasksText') is not None

    save_btn = dialog.find('button', class_='btn-primary')
    assert save_btn is not None
    assert 'saveTaskEdit()' in save_btn.get('onclick', '')


def test_header_action_buttons_and_toast(test_setup):
    """Valida botões do cabeçalho da página e elemento de notificação toast."""
    response = test_setup.get('/')
    soup = BeautifulSoup(response.data, 'html.parser')

    # Botão de abrir modal de novo item
    btn_novo = soup.find('button', string=lambda t: t and 'Novo Item' in t)
    assert btn_novo is not None
    assert "addDialog" in btn_novo.get('onclick', '')

    # Botão de atualizar quadro
    btn_reload = soup.find('button', string=lambda t: t and 'Atualizar Quadro' in t)
    assert btn_reload is not None
    assert 'location.reload()' in btn_reload.get('onclick', '')

    # Elemento de notificação toast
    toast = soup.find('div', id='toast')
    assert toast is not None
    assert 'notification' in toast.get('class', [])


def test_empty_database_rendering():
    """Garante que a página renderiza perfeitamente mesmo sem nenhuma tarefa ou aviso no banco."""
    original_db = kanban_semanal.DATABASE
    kanban_semanal.DATABASE = 'test_empty.db'

    if os.path.exists(kanban_semanal.DATABASE):
        os.remove(kanban_semanal.DATABASE)

    kanban_semanal.init_db()

    client = kanban_semanal.app.test_client()
    response = client.get('/')
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, 'html.parser')
    # Colunas vazias
    assert len(soup.find('div', id='todo').find_all('div', class_='task-card')) == 0
    assert len(soup.find('div', id='doing').find_all('div', class_='task-card')) == 0
    assert len(soup.find('div', id='done').find_all('div', class_='task-card')) == 0

    if os.path.exists(kanban_semanal.DATABASE):
        os.remove(kanban_semanal.DATABASE)
    kanban_semanal.DATABASE = original_db
