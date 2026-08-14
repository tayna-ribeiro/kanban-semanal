# ESPEC - Exclusão de Cards e Prazos/Deadlines

* **Autor:** Antigravity (AI Coding Assistant) & Tayna Ribeiro
* **Data:** 14/08/2026
* **Status:** Concluído

---

## 1. Objetivo e Contexto

Atualmente, o Kanban Semanal permite adicionar tarefas e prazos diretamente da interface gráfica, mas não oferece uma forma direta de excluir itens incorretos ou obsoletos sem ter que abrir o arquivo de texto `tarefasDiarias.txt` manualmente.

O objetivo desta especificação é definir a interface e a lógica de backend necessárias para:

1. Excluir uma tarefa (card) diretamente do quadro Kanban.
2. Excluir um prazo ou lembrete (notice) diretamente do Quadro de Avisos.

---

## 2. Requisitos e Critérios de Aceitação

### Exclusão de Cards (Kanban)

- [x] **Interface do Card:** Cada card no Kanban deve exibir um pequeno botão de exclusão (lixeira ou "✕") visível ao passar o mouse (hover) ou posicionado de forma discreta no canto superior direito do card.
* [x] **Confirmação:** Ao clicar no botão de excluir do card, o sistema deve solicitar uma confirmação nativa (ex: `confirm("Deseja realmente excluir esta tarefa?")`) antes de proceder.
* [x] **Persistência no Arquivo:** Ao confirmar, a tarefa e todas as suas linhas associadas (blocos multilinha) devem ser removidas fisicamente de `tarefasDiarias.txt`.
* [x] **Feedback Visual:** A página deve exibir um aviso toast de sucesso ("Tarefa excluída") e recarregar para atualizar os índices do arquivo.

### Exclusão de Prazos/Lembretes (Quadro de Avisos)

- [x] **Interface do Aviso:** Cada item listado nos quadros de avisos (como "Prazos e Deadlines", "Deploy", etc.) deve exibir um botão de exclusão ("✕") ao passar o mouse.
* [x] **Confirmação:** Ao clicar no botão, pedir confirmação.
* [x] **Persistência no Arquivo:** Ao confirmar, a linha exata correspondente a esse aviso deve ser removida de `tarefasDiarias.txt`.
* [x] **Feedback Visual:** Exibir toast de sucesso ("Lembrete excluído") e recarregar o quadro.

---

## 3. Arquitetura e Solução Técnica

### Backend (`kanban_semanal.py`)

1. **Modificação em `parse_notice_board`**:
   Atualmente, a lista de itens de cada aviso contém apenas a string de texto. Vamos alterá-la para conter dicionários com a linha física do arquivo (`line_idx`) e o texto:

   ```python
   # Exemplo de estrutura de retorno:
   {
       'title': 'PRAZOS E DEADLINES',
       'items': [
           {'line_idx': 21, 'text': 'Gestão Acadêmica - Prazo: 18/08/2026'}
       ]
   }
   ```

2. **Função `delete_line_from_file(line_idx)`**:
   Remove uma linha específica de `tarefasDiarias.txt`, criando um backup de segurança antes da gravação.
3. **Função `delete_task_from_file(start_idx)`**:
   Remove a linha inicial do card e todas as linhas seguintes que fazem parte daquele bloco de descrição (até encontrar uma linha em branco, outra tarefa ou cabeçalho).
4. **Novas rotas de API**:
   * `POST /delete_task` - Recebe o `{ "id": start_idx }` da tarefa para remover.
   * `POST /delete_notice` - Recebe o `{ "line_idx": line_idx }` do aviso para remover.

### Frontend (`templates/index.html`)

1. **Renderização de Lembretes:** Atualizar o loop Jinja para lidar com objetos `{'line_idx', 'text'}` em vez de strings brutas.
2. **Estilização de Botões de Exclusão:**
   * Adicionar botões de exclusão nos cards e nos itens de avisos com transições suaves de opacidade no hover.
3. **Funções JS:**
   * `deleteTask(id)`: Faz a requisição para `/delete_task`.
   * `deleteNotice(lineIdx)`: Faz a requisição para `/delete_notice`.

---

## 4. Plano de Verificação (Testes)

### Testes Manuais

1. **Excluir Card:**
   * Adicionar uma tarefa temporária "Tarefa Teste Exclusão".
   * Clicar no "✕" do card, cancelar a confirmação (o card deve permanecer).
   * Clicar novamente, confirmar. A página deve recarregar e o card deve ter sumido do quadro.
   * Verificar no arquivo `tarefasDiarias.txt` se a linha correspondente sumiu.
2. **Excluir Prazo:**
   * Adicionar um prazo temporário na seção "Prazos e Deadlines".
   * Clicar no "✕" ao lado do item de aviso. Confirmar a exclusão.
   * Garantir que o item sumiu e que a linha foi apagada do arquivo de texto.

### Testes Automatizados (`tests/test_kanban.py`)

- Criar funções de teste `test_delete_task()` e `test_delete_notice()` simulando as exclusões e verificando se os parses subsequentes retornam os dados corretos sem corromper o restante do arquivo.
