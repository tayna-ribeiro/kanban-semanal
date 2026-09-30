# ESPEC - Testes de Frontend e Automação de CI (GitHub Actions)

* **Autor:** Antigravity (AI Coding Assistant) & Tayna Ribeiro
* **Data:** 30/09/2026
* **Status:** Esboço / Proposta

---

## 1. Objetivo e Contexto

Atualmente, o Kanban Semanal possui uma suíte de 12 testes automatizados focados no backend (SQLite e rotas da API em `tests/test_kanban.py`). No entanto, não há testes que garantam a integridade e funcionamento do frontend (`templates/index.html`), como a estrutura do DOM, presença de modais de cadastro e edição, colunas do quadro Kanban, quadro de avisos, filtros e elementos interativos.

Além disso, os testes atualmente só rodam se executados manualmente no terminal.

O objetivo desta especificação é:
1. Criar uma suíte de testes de interface/frontend para validar os elementos essenciais da UI e suas interações com as rotas.
2. Estruturar a pipeline de Integração Contínua (CI) com **GitHub Actions** para rodar automaticamente toda a suíte de testes a cada `push` ou `pull_request` no GitHub.
3. Atualizar a documentação do projeto (`README.md`) refletindo a nova arquitetura de testes e o status da pipeline.

---

## 2. Requisitos e Critérios de Aceitação

### Testes de Frontend / Interface
- [x] **Renderização do Quadro Kanban:** Garantir que a página principal (`/`) renderiza corretamente com as colunas essenciais (`A Fazer`, `Em Andamento`, `Concluído`) e seus contadores.
- [x] **Estrutura dos Modais:** Validar que os diálogos HTML essenciais existem com os IDs esperados pelo JavaScript:
  - Modal de Criação (`#addDialog`) com abas para Tarefa e Prazo/Aviso.
  - Modal de Edição (`#editDialog`) com todos os campos de formulário (título, contrato, tags, datas, subtarefas).
- [x] **Quadro de Avisos:** Garantir que o bloco `#noticeBoardWrapper` e a barra de recolher/expandir estão presentes e renderizam os avisos ativos por categoria.
- [x] **Badges e Contratos:** Garantir que os contratos suportados (`INTO`, `JBRJ`, `PESSOAL`) possuem suas respectivas classes CSS e atributos renderizados.
- [x] **Barra de Acesso Rápido / Logins:** Garantir a presença do container de logins e botão de novo acesso.
- [x] **Consistência de Assets:** Garantir que estilos CSS fundamentais e funções do frontend não geram erros de renderização ou quebras de sintaxe no Jinja.

### Pipeline do GitHub Actions (CI)
- [x] **Execução Automática:** Executar a suíte de testes automaticamente em qualquer `push` para a branch `main`/`master` e em Pull Requests.
- [x] **Ambiente Limpo:** Configurar máquina virtual Ubuntu com Python 3.12, instalação de dependências e execução do `pytest`.
- [x] **Feedback Rápido:** Falhar a pipeline caso algum teste quebre e exibir badge/status de sucesso se tudo passar.
- [x] **Compatibilidade:** Funcionar 100% gratuito em contas pessoais do GitHub.

---

## 3. Arquitetura e Solução Técnica

* **Arquivos modificados/criados:**
  - `tests/test_frontend.py` - Nova suíte de testes de renderização e integridade do frontend/UI via Flask Test Client e analisador DOM.
  - `.github/workflows/ci.yml` - Arquivo de configuração da pipeline do GitHub Actions.
  - `requirements.txt` - Arquivo com dependências do projeto para permitir que o GitHub Actions instale os pacotes necessários.
  - `README.md` - Atualização da documentação ao final do processo.

* **Estratégia de Teste de Frontend:**
  - Usaremos o test client do Flask integrado a validações semânticas de HTML para verificar se todos os elementos, atributos `id`, classes de estilização e tags dinâmicas Jinja (`tasks`, `notices`) estão sendo injetados no HTML sem quebras.

---

## 4. Plano de Verificação (Testes)

* **Teste Manual:**
  1. Executar os testes localmente via terminal: `PYTHONPATH=. ./venv/bin/pytest tests/`.
  2. Verificar se todos os testes (backend + frontend) passam.
* **Teste Automatizado / Pipeline:**
  1. Fazer `git push` para o GitHub e verificar a aba **Actions** no repositório.
  2. Garantir que a pipeline executa e fica verde (sucesso).
