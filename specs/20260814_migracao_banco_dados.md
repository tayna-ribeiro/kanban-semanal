# ESPEC - Migração para Banco de Dados e Edição Completa de Cards

* **Autor:** Antigravity (AI Coding Assistant) & Tayna Ribeiro
* **Data:** 14/08/2026
* **Status:** Concluído

---

## 1. Objetivo e Contexto
O Kanban Semanal cresceu em funcionalidades e complexidade. A persistência atual baseada em arquivos de texto (`tarefasDiarias.txt`, `historico.txt` e checklists `.txt` separados) está alcançando seus limites de escalabilidade, robustez e flexibilidade. Qualquer modificação concorrente ou erro de parsing pode corromper os dados.

O objetivo desta especificação é definir a transição do sistema de arquivos de texto para um banco de dados relacional local (**SQLite**), e implementar uma tela/modal avançado de **Edição de Cards** que permita gerenciar o título, descrição, prazos de início/fim e subtarefas de forma estruturada.

---

## 2. Requisitos e Critérios de Aceitação

### 2.1 Migração para Banco de Dados (SQLite)
- [x] **Persistência de Tarefas (Cards):** Armazenar todas as tarefas no banco de dados, incluindo datas de prazo e controle de arquivamento.
- [x] **Persistência de Subtarefas:** Armazenar as subtarefas vinculadas a um card, eliminando a necessidade de ler/escrever arquivos `.txt` individuais para checklists secundários.
- [x] **Persistência de Quadro de Avisos (Notices):** Armazenar lembretes, deploys e prazos organizados por seções no banco.
- [x] **Persistência de Logins Favoritos:** Migrar os logins frequentes do *localStorage* do navegador para o banco de dados (permitindo centralização e backup automático).
- [x] **Compatibilidade e Carga Inicial:** No primeiro boot com banco de dados, o backend deve ler o arquivo `tarefasDiarias.txt` atual e migrar todos os dados existentes para o banco SQLite automaticamente, para que o usuário não perca nada do seu quadro atual.

### 2.2 Funcionalidade de Edição Completa de Cards
- [x] **Interface de Edição:** Clicar em um card (ou em um botão de editar "✏️" nele) deve abrir um modal avançado de edição.
- [x] **Campos de Edição:** O modal deve permitir editar:
  - Título do card.
  - Contrato (INTO, JBRJ, PESSOAL, OUTROS).
  - Tag/Tipo (Demanda, Melhoria, Correção, Estudo, Ajuste, Documentação).
  - Descrição detalhada.
  - Data de Início (`start_date`) - Seletor de data (Calendário).
  - Data de Fim/Prazo (`end_date`) - Seletor de data (Calendário).
- [x] **Gerenciador de Subtarefas dentro do Modal:**
  - O modal deve permitir definir um **Título para o Bloco de Subtarefas** (ex: *gestaoAcademica2*).
  - Deve conter uma área de texto onde o usuário cola ou digita subtarefas (uma por linha).
  - Ao salvar, essas linhas são automaticamente convertidas em itens individuais de checklist na tabela de subtarefas no banco.
- [x] **Interação de Checklists:** No próprio card do Kanban, o usuário deve poder marcar/desmarcar os itens da subtarefa de forma reativa (salvando no banco via requisição AJAX).

---

## 3. Arquitetura e Solução Técnica

### 3.1 Modelo de Dados (Schema SQLite)

```sql
-- Tabela de Tarefas
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    contract TEXT NOT NULL,          -- INTO, JBRJ, PESSOAL, OUTROS
    tag TEXT NOT NULL,               -- Demanda, Melhoria, Correção, etc.
    status TEXT NOT NULL,            -- todo, doing, done
    start_date TEXT,                 -- Formato YYYY-MM-DD
    end_date TEXT,                   -- Formato YYYY-MM-DD
    subtask_title TEXT,              -- Título do bloco de subtarefas
    is_active INTEGER DEFAULT 1,     -- 1 = Ativo, 0 = Excluído/Inativo
    created_at TEXT NOT NULL
);

-- Tabela de Subtarefas
CREATE TABLE IF NOT EXISTS subtasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    is_done INTEGER DEFAULT 0,       -- 0 = Pendente, 1 = Concluído
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Tabela de Quadro de Avisos (Notices)
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section TEXT NOT NULL,           -- Prazos e Deadlines, Deploy, Importante, Férias
    text TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,     -- 1 = Ativo, 0 = Inativo (Histórico)
    created_at TEXT NOT NULL
);

-- Tabela de Logins Frequentes
CREATE TABLE IF NOT EXISTS logins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,             -- Sistema/URL
    username TEXT NOT NULL,          -- Usuário
    password TEXT,                   -- Senha
    is_active INTEGER DEFAULT 1
);
```

### 3.2 Backend (`kanban_semanal.py`)
1. **Conexão de Banco:** Criar um módulo ou helper para gerenciar a conexão do SQLite (`kanban.db`).
2. **Script de Inicialização e Migração:**
   - Ao iniciar o app, verificar se `kanban.db` existe.
   - Se não existir, criar as tabelas.
   - Executar uma rotina única que lê `tarefasDiarias.txt` e migra as tarefas e prazos antigos para o banco de dados.
3. **Novos Endpoints:**
   - `GET /api/tasks` e `GET /api/notices` - Retorna os dados em JSON.
   - `POST /api/add_item` - Adiciona tarefa ou aviso.
   - `POST /api/edit_task` - Atualiza os detalhes de uma tarefa e recria/atualiza suas subtarefas associadas a partir do texto enviado.
   - `POST /api/toggle_subtask` - Altera o status `is_done` de uma subtarefa específica.
   - `POST /api/delete_task` e `POST /api/delete_notice` - Altera `is_active = 0` (exclusão lógica) ou remove fisicamente.
   - `GET /api/logins` e `POST /api/add_login` / `/api/delete_login` - Para gerenciar os logins favoritos via banco.

### 3.3 Frontend (`templates/index.html`)
1. **Modal de Edição (`#editDialog`):**
   - Um novo elemento `<dialog>` contendo o formulário de edição de card.
   - Um campo `textarea` para colar/digitar subtarefas linha a linha.
2. **Renderização Dinâmica via Jinja/JS:**
   - Adaptar os cards do Kanban para exibir datas de prazo em formato visual legível (ex: "📅 14/08 a 18/08").
   - Exibir subtarefas atreladas.
3. **Persistência de Logins:**
   - Substituir a leitura do *localStorage* por chamadas AJAX para `/api/logins`.

---

## 4. Plano de Verificação (Testes)

### 4.1 Testes de Migração (Carga Inicial)
1. Certificar que um arquivo `tarefasDiarias.txt` preenchido é migrado integralmente para `kanban.db` na primeira inicialização.
2. Conferir se todas as colunas (contrato, status, tags) foram migradas com precisão.

### 4.2 Testes Manuais
1. **Edição do Card:**
   - Abrir o modal de edição de um card.
   - Alterar título, datas de início/fim e adicionar um bloco de subtarefas:
     ```text
     Instalar pytest
     Escrever testes unitários
     Rodar suite de testes
     ```
   - Salvar e validar se o card mostra o prazo e se as subtarefas aparecem como checkboxes.
   - Ticar uma subtarefa na tela e atualizar a página. Ela deve permanecer marcada (salva no banco).
2. **Gestão de Logins e Avisos:**
   - Cadastrar logins e avisos e verificar se permanecem após apagar o cache do navegador (provando a persistência no banco SQLite).

### 4.3 Testes Automatizados (`tests/test_kanban.py`)
- Testar a criação de tabelas SQLite.
- Testar a inserção, edição e exclusão de tarefas via banco de dados usando mocks ou um banco temporário em memória (`:memory:`).
