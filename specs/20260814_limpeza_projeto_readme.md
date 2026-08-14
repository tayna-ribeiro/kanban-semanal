# ESPEC - Limpeza do Projeto e Atualização do README

* **Autor:** Antigravity (AI Coding Assistant) & Tayna Ribeiro
* **Data:** 14/08/2026
* **Status:** Concluído

---

## 1. Objetivo e Contexto
Com a transição bem-sucedida do Kanban Semanal de arquivos de texto para o banco de dados relacional **SQLite** (`kanban.db`), o diretório do projeto acumula diversos arquivos `.txt` e backups antigos que se tornaram obsoletos e redundantes. 

O objetivo desta especificação é definir:
1. Quais arquivos antigos serão removidos com segurança para manter o diretório do projeto limpo.
2. Como atualizar o arquivo `README.md` para refletir com precisão a nova arquitetura do sistema, o uso de banco de dados, as novas funcionalidades de edição avançada e as instruções de execução modernas.

---

## 2. Requisitos e Critérios de Aceitação

### 2.1 Limpeza de Arquivos Obsoletos
- [x] **Remoção de Backups Temporários:** Excluir os backups antigos `tarefasDiarias.txt.old` e `tarefasDiarias.txt.bak`.
- [x] **Remoção de Checklists Migrados:** Excluir arquivos de subtarefas legados cujos dados já foram migrados com sucesso para o banco de dados SQLite (como `gestaoAcademica2.txt`, etc.).
- [x] **Preservação do Histórico e Banco:** Manter o histórico legível de fechamento (`historico.txt`) e o banco de dados principal (`kanban.db`).

### 2.2 Atualização do README.md
- [x] **Descrição de Arquitetura:** Substituir a descrição antiga (que focava em arquivos de texto) pela nova arquitetura baseada em banco de dados SQLite.
- [x] **Novas Funcionalidades:** Descrever os novos recursos (Modal Avançado de Edição de Cards, Datas de Início/Prazo, Editor de Subtarefas por caixa de texto, e o Cofre de Logins centralizado no servidor).
- [x] **Instruções de Inicialização e Testes:** Incluir comandos modernos para ativação de ambiente virtual (`venv`), execução do servidor Flask e execução dos testes automatizados via `pytest`.
- [x] **Organização do Diretório:** Atualizar o mapa da árvore de diretórios do projeto no `README.md`.

---

## 3. Arquitetura e Solução Técnica

### 3.1 Lista de Arquivos a Remover (Com Consentimento)
Apenas os seguintes arquivos de dados antigos/obsoletos serão excluídos:
* `tarefasDiarias.txt.old` (Backup da migração)
* `tarefasDiarias.txt.bak` (Backup temporário antigo)
* `gestaoAcademica2.txt` (Checklist de subtarefas já migrado para a tabela `subtasks` vinculada ao card no banco)

*Nota: Os demais arquivos `.txt` na pasta serão mantidos caso o usuário os queira como referência futura.*

### 3.2 Atualização do `README.md`
O arquivo `README.md` será reformulado para descrever o projeto moderno com suporte a SQLite, e instruir o uso do comando `pytest` para testes.

---

## 4. Plano de Verificação (Testes)

### 4.1 Testes Manuais
1. Validar que os arquivos selecionados foram removidos do diretório.
2. Certificar que a aplicação continua iniciando e executando perfeitamente a partir do banco de dados `kanban.db` mesmo após a remoção dos arquivos.
3. Visualizar o `README.md` e certificar-se de que os links e instruções estão corretos.
