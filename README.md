# 📌 Planejamento Semanal - Kanban

Um sistema leve e ágil de gerenciamento de tarefas estruturado como um quadro Kanban no navegador. Construído em **Python (Flask)**, o sistema lê dados de arquivos de texto locais (como `tarefasDiarias.txt`), converte anotações em cartões interativos (com recurso de arrastar e soltar) e acompanha o ciclo de vida das suas atividades diárias e recados.

## ✨ Funcionalidades

- **Kanban Interativo (Drag & Drop):** Arraste tarefas entre as colunas "A Fazer", "Em Andamento" e "Concluído" de forma simples.
- **Integração com Arquivos Texto:** O sistema dispensa banco de dados complexos; basta editar o seu arquivo `tarefasDiarias.txt` e a interface é atualizada automaticamente!
- **Checklists Secundários:** Crie arquivos `.txt` de apoio (ex: `Reabilitacao.txt`) para gerenciar subtarefas. O Kanban interpreta chamadas como `consultar o bloco "Reabilitacao"` e embute uma lista de checagem nativa no card.
- **Histórico Automático:** Ao arrastar uma tarefa para "Concluído", o sistema não a perde. Ela é registrada permanentemente no arquivo `historico.txt` com a data e hora do encerramento.
- **📋 Quadro de Avisos:** Gerencia recados cruciais da equipe (como links úteis, lembretes de **Deploy** ou datas  **Pessoais**) no topo do painel.
- **Inspirador Diário:** Graças a um web scraper nativo, a barra de título exibe diariamente uma citação inteligente/inspiradora sobre Tecnologia ou Doutrina Espírita capturada da web.
- **🔑 Cofre de Logins Frequentes:** Gerenciador interno usando *localStorage* do seu navegador para guardar rapidamente sistemas/URLs e senhas. Copie os dados com um simples clique para transitar melhor entre os sistemas corporativos.

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python + Flask (microframework rápido e excelente para scripts locais).
- **Frontend:** HTML5, CSS Nativo (aparência minimalista e *clean*) e Vanilla JavaScript.
- **Recursos Dinâmicos:** [SortableJS](https://sortablejs.github.io/Sortable/) (para animações de Kanban fluidas).

## 🚀 Como Executar

1. **Pré-requisitos:**
   Certifique-se de ter o Python instalado na sua máquina. A biblioteca `flask` é necessária.
   ```bash
   pip install flask
   ```

2. **Inicializando o App:**
   No seu terminal, dentro do diretório do projeto, rode:
   ```bash
   python kanban_semanal.py
   ```

3. **Acessando na Web:**
   Seu Kanban estará no ar imediatamente. Abra no seu navegador:
   🔗 [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 📁 Estrutura do Projeto

```text
/tarefas_diarias
 │
 ├── kanban_semanal.py      # Servidor Backend (Flask) e lógicas Python
 ├── tarefasDiarias.txt     # Seu arquivo principal que alimenta o sistema
 ├── historico.txt          # Seu log de registro de conclusão de atividades armazenado automaticamente
 ├── Reabilitacao.txt       # Arquivos extras atuam como 'sub-tarefas' (Checklists embutidos)
 │
 └── /templates
      └── index.html        # Interface de Usuário Inteligente (Quadro + Scripts JS)
```

## 📝 Como usar o `tarefasDiarias.txt`

O Backend reconhece padrões no seu texto:

- Títulos maiores (H2) que contenham *Demanda* ou *Melhoria* indicam a criação de tarefas no Kanban ("A Fazer" por padrão). 
- O projeto usa termos-chave nos títulos para colorir de forma dinâmica os cartões (Ex: `## DEMANDAS DO INTO` ou `## DEMANDAS DO JBRJ`).
- Títulos soltos com as palavras `DEPLOY` ou `PESSOAL` irão direto para o quadro recolhível de Avisos.
- Adicionar no texto o trecho `[Em andamento]` coloca o cartão direto no status amarelo do painel.

---


