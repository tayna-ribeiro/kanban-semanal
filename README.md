# Planejamento Semanal - Kanban

![CI - Testes Automatizados](https://github.com/tayna-ribeiro/kanban-semanal/actions/workflows/ci.yml/badge.svg)

Um sistema leve, ágil e moderno de gerenciamento de tarefas estruturado como um quadro Kanban no navegador. Construído em **Python (Flask)** e **SQLite**, o sistema oferece cartões interativos (com recurso de arrastar e soltar), edição avançada de atividades, checklists de subtarefas, prazos de início/fim e um cofre seguro de logins frequentes.

---

## Funcionalidades

- **Kanban Interativo (Drag & Drop):** Arraste tarefas entre as colunas "A Fazer", "Em Andamento" e "Concluído" de forma fluida.
- **Persistência em Banco de Dados (SQLite):** Centralização completa e segura de dados no arquivo `kanban.db`. Acabe com a edição manual de arquivos de texto e inconsistências de concorrência.
- **Edição Avançada de Cards:** Abra o modal de edição clicando no ícone "✏️" para ajustar:
  - Título do card.
  - Vínculo de Contrato (INTO, JBRJ, PESSOAL, OUTROS).
  - Categorização por Tags (Demanda, Melhoria, Correção, Estudo, Ajuste, Documentação).
  - Descrição detalhada do card.
  - Datas de Início e Prazo Final (com calendário integrado).
- **Checklists Estruturados de Subtarefas:** Digite ou cole subtarefas linha a linha no editor do card (ex: `* Item 1`). O sistema salva no banco de dados e as exibe como itens interativos com checkboxes reativos diretamente no card do Kanban.
- **Quadro de Avisos Dinâmico:** Gerencie recados urgentes da equipe (como lembretes de **Deploy**, comunicados **Importantes**, prazos gerais ou **Férias**) de forma visual no topo do painel.
- **Cofre de Logins Frequentes:** Gerencie com segurança seus acessos rápidos (Sistema/URL, Usuário e Senha) salvando-os no banco de dados. Copie qualquer credencial para a área de transferência com um único clique.
- **Histórico de Fechamento:** Ao concluir uma tarefa, ela é registrada automaticamente em `historico.txt` com a data e hora do encerramento.

---

## Tecnologias Utilizadas

- **Backend:** Python + Flask (microframework rápido para servidores locais) + SQLite3 (banco de dados relacional em arquivo).
- **Frontend:** HTML5, CSS Nativo (aparência minimalista e moderna) e Vanilla JavaScript.
- **Componentes Dinâmicos:** [SortableJS](https://sortablejs.github.io/Sortable/) (para drag-and-drop de cards).
- **Testes Automatizados:** Pytest + BeautifulSoup4 (validação de banco, rotas HTTP e integridade da interface/DOM).
- **Integração Contínua (CI):** GitHub Actions (automação de testes em ambiente Linux/Python 3.12).

---

## Como Executar

### 1. Preparação do Ambiente (Recomendado)

Crie e ative um ambiente virtual virtualenv do Python:

```bash
# Criar o ambiente virtual
python3 -m venv venv

# Ativar o ambiente virtual (Linux/macOS)
source venv/bin/activate

# Ativar o ambiente virtual (Windows)
# venv\Scripts\activate
```

Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

### 2. Inicializando o Servidor

Execute o backend:

```bash
python kanban_semanal.py
```

Abra o seu navegador e acesse:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

### 3. Testes Automatizados e Pipeline de CI

O projeto conta com uma suíte de **22 testes automatizados** cobrindo ponta a ponta o backend e a interface:

* **Backend e APIs (`tests/test_kanban.py` - 12 testes):**
  - Leitura e listagem de tarefas e avisos no SQLite.
  - Inserção, edição e exclusão de cards e prazos.
  - Endpoints HTTP REST da API Flask (`/delete_task`, `/delete_notice`, `/edit_task`, etc.).
  - Gerenciamento de credenciais rápidas (adicionar, listar, remover logins).

* **Frontend e Interface (`tests/test_frontend.py` - 10 testes):**
  - Renderização das 3 colunas do Kanban (*A Fazer*, *Em Andamento*, *Concluído*) e contadores.
  - Exibição de cards, badges de contrato (`INTO`, `JBRJ`, `PESSOAL`) e datas formatadas.
  - Estrutura completa dos modais de criação (`#addDialog`) e edição (`#editDialog`).
  - Quadro de Avisos com alternância sanfona e widget de logins frequentes.
  - Renderização limpa mesmo quando o banco de dados estiver vazio.

#### Executando localmente:

```bash
PYTHONPATH=. ./venv/bin/pytest tests/ -v
```

#### Pipeline de Integração Contínua (GitHub Actions):

A cada `git push` ou *Pull Request* enviado para a branch `main`, o GitHub Actions dispara automaticamente a pipeline configurada em `.github/workflows/ci.yml`. Os testes são executados em um ambiente Ubuntu isolado para garantir que nenhuma alteração quebre o sistema.

---

## Estrutura do Projeto

```text
/tarefas_diarias
 │
 ├── .github/
 │    └── workflows/
 │         └── ci.yml           # Pipeline de automação de testes do GitHub Actions
 │
 ├── kanban_semanal.py          # Servidor Backend (Flask), rotas de API e conexões SQLite
 ├── kanban.db                  # Banco de dados SQLite contendo todas as tabelas
 ├── requirements.txt           # Dependências do projeto (Flask, pytest, beautifulsoup4)
 ├── historico.txt              # Log de auditoria e arquivamento das tarefas concluídas
 ├── start_kanban.sh            # Script shell para autostart rápido
 ├── README.md                  # Este manual de documentação
 │
 ├── /templates
 │    └── index.html            # Frontend da interface de usuário interativa (Kanban + Avisos)
 │
 ├── /tests
 │    ├── test_kanban.py        # Testes de backend, rotas e banco SQLite
 │    └── test_frontend.py      # Testes de integridade da UI, modais e layout
 │
 └── /specs
      └── [Especs].md           # Especificações de requisitos e evolução do projeto
```

---

## Carga Inicial e Migração Automática

Não se preocupe com seus dados antigos! Ao iniciar o servidor com banco de dados pela primeira vez:

1. O backend detecta a presença do arquivo legível `tarefasDiarias.txt`.
2. Faz o parsing automático de todos os cards, checklists e avisos.
3. Importa todos os dados com perfeição para o arquivo `kanban.db`.
4. Renomeia o arquivo antigo para `tarefasDiarias.txt.old` como cópia de segurança.
5. Sincroniza e importa os logins guardados anteriormente no navegador.
