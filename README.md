# Trabalho final Data Warehouse e BI — Prêmio Oceanos de Literatura

Projeto acadêmico de Business Intelligence desenvolvido sobre o histórico de inscrições do **Prêmio Oceanos de Literatura** (2015–2024).

---

## Escopo do trabalho

Arquivo em pdf do escopo do trabalho descrevendo o trabalho por completo e o que foi feito
 
 <a href="escopo_projeto_dw_oceanos.pdf">Escopo do trabalho</a>

---

##  Estrutura do projeto

```
BITrabalhoFinal/
│
├── data/
│   └── world_oceanos_mapeamento_historico_inscritos.csv   # Dataset original
│
├── etl_oceanos.py          # Pipeline ETL (Extract → Transform → Load)
├── consultas_analiticas.sql  # 12 consultas SQL analíticas
├── dashboard_oceanos.py    # Dashboard interativo (Streamlit)
├── escopo_projeto_dw_oceanos.docx  # Documento de escopo do projeto
└── README.md               # Este arquivo
```

---

##  Pré-requisitos

- Python 3.10 ou superior
- PostgreSQL com pgAdmin instalado e rodando
- Banco de dados `dwfinal` criado no PostgreSQL

#### Instalação das dependências

```powershell
pip install pandas sqlalchemy psycopg2-binary streamlit plotly
```

---

##  Como rodar o projeto

###  Rodar o ETL

O ETL lê o CSV, aplica as transformações e carrega as tabelas no PostgreSQL.

```powershell
python etl_oceanos.py
```

O que acontece internamente:

- **Extract:** lê o arquivo `data/world_oceanos_mapeamento_historico_inscritos.csv`
- **Transform:** preenche nulos, converte indicadores para 0/1, deriva `nivel_selecao` e `tipo_publicacao`
- **Load:** cria e popula as 5 tabelas no banco `dwfinal` do PostgreSQL

Ao final você verá no terminal:

```
[ETL] Arquivo carregado — 16799 linhas brutas.
[ETL] Transform concluído — {'Inscrito': 16247, 'Semifinalista': 448, 'Finalista': 71, 'Vencedor': 33}
[ETL] Carga concluída com sucesso!
  dim_tempo      : 10 registros
  dim_autor      : 11891 registros
  dim_livro      : 16761 registros
  dim_editora    : 1615 registros
  fato_inscricao : 16799 registros
```

---

### Explorar as consultas SQL (opcional)

O arquivo `consultas_analiticas.sql` contém 12 queries organizadas em 4 temas.
Você pode executá-las diretamente no pgAdmin conectando ao banco `dwfinal`.

| Query | Pergunta respondida |
|-------|---------------------|
| Q01 | Inscrições por ano |
| Q02 | Gêneros literários por ano |
| Q03 | Evolução da participação feminina |
| Q04 | Funil completo por ano (semi → final → vencedor) |
| Q05 | Taxa de conversão para vencedor por gênero |
| Q06 | Concentração de vitórias por país |
| Q07 | Gênero dos autores — inscritos vs premiados |
| Q08 | Perfil etário — inscritos vs vencedores |
| Q09 | Ranking de países por inscrições e vitórias |
| Q10 | Top 15 editoras por volume de inscrições |
| Q11 | Editoras com vitórias — concentração editorial |
| Q12 | Autopublicação vs editora tradicional por ano |

---

###  Rodar o dashboard

```powershell
python -m streamlit run dashboard_oceanos.py
```

O navegador abrirá automaticamente em `http://localhost:8501`.

---

## O que o dashboard mostra

O painel possui filtros na barra lateral (período e gênero literário) que atualizam todos os gráficos simultaneamente.

| Seção | Conteúdo |
|-------|----------|
| **KPIs** | Total de inscrições, semifinalistas, finalistas e vencedores |
| **Evolução temporal** | Inscrições por ano e distribuição de gêneros literários |
| **Funil de seleção** | Funil por gênero literário e evolução da participação feminina |
| **Diversidade** | Ranking de países e perfil etário dos autores |
| **Mercado editorial** | Top editoras, autopublicação vs tradicional |
| **Editoras premiadas** | Tabela detalhada com finalistas e vencedores por editora |

---

##  Modelo dimensional (Star Schema)

```
                  DIM_TEMPO
                      |
   DIM_AUTOR ── FATO_INSCRICAO ── DIM_LIVRO
                      |
                 DIM_EDITORA
```

| Tabela | Descrição 
|--------|-----------
| `fato_inscricao` | Uma linha por inscrição no prêmio 
| `dim_tempo` | Anos 2015–2024 com período e década 
| `dim_autor` | Dados demográficos dos autores 
| `dim_livro` | Título, gênero e país de publicação 
| `dim_editora` | Editora, sede e tipo de publicação 

---

##  Configuração do banco de dados

A string de conexão usada nos arquivos é:

```
postgresql+psycopg2://postgres:masterkey@localhost:5432/dwfinal
```

Se seu PostgreSQL usar usuário, senha ou nome de banco diferentes, alterar essa linha em **ambos os arquivos**:

- `etl_oceanos.py` → seção `# 5. LOAD`
- `dashboard_oceanos.py` → função `carregar_dados()`

---

##  Dataset

| Atributo | Valor |
|----------|-------|
| Arquivo | `world_oceanos_mapeamento_historico_inscritos.csv` |
| Período | 2015 a 2024 (10 edições do prêmio) |
| Registros | 16.799 obras inscritas |
| Colunas | 16 atributos (obra, autor, editora, resultado) |
| Gêneros | Poesia, Romance, Conto, Crônica, Dramaturgia |

---

##  Tecnologias utilizadas

| Ferramenta | Uso |
|------------|-----|
| Python 3 + pandas | ETL e transformação dos dados |
| SQLAlchemy + psycopg2 | Conexão com PostgreSQL |
| PostgreSQL / pgAdmin | Banco de dados analítico (DW) |
| Streamlit | Dashboard interativo |
| Plotly | Gráficos interativos |
