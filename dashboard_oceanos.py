# -*- coding: utf-8 -*-
"""
Dashboard — Prêmio Oceanos de Literatura
========================================
Execução:
    pip install streamlit plotly pandas psycopg2-binary sqlalchemy
    streamlit run dashboard_oceanos.py
"""

from sqlalchemy import create_engine
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ------------------------------------CONFIGURAÇÃO DA PÁGINA------------------------------------

st.set_page_config(
    page_title="Prêmio Oceanos · Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------CSS personalizado------- ----------------------------- 
st.markdown("""
<style>
    /* Fundo e tipografia geral */
    [data-testid="stAppViewContainer"] {
        background-color: #0f1117;
    }
    [data-testid="stSidebar"] {
        background-color: #161b27;
        border-right: 1px solid #2a3045;
    }

    /* Cards de KPI */
    .kpi-card {
        background: linear-gradient(135deg, #1a2035 0%, #1e2540 100%);
        border: 1px solid #2a3a5c;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
    }
    .kpi-value {
        font-size: 2.4rem;
        font-weight: 700;
        color: #e8c97e;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #8899bb;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 4px;
    }

    /* Título principal */
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: #e8c97e;
        letter-spacing: -0.02em;
    }
    .main-subtitle {
        font-size: 1rem;
        color: #8899bb;
        margin-top: -6px;
    }

    /* Cabeçalhos de seção */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #c5d3f0;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-bottom: 1px solid #2a3a5c;
        padding-bottom: 8px;
        margin-bottom: 4px;
    }

    /* Remove padding excessivo */
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------CONEXÃO E CACHE DE DADOS------------------------------------

@st.cache_data
def carregar_dados():
    conn = create_engine("postgresql+psycopg2://postgres:masterkey@localhost:5432/dwfinal")

    inscricoes_ano = pd.read_sql("""
        SELECT t.ano, t.periodo, COUNT(*) AS total,
               SUM(f.indicador_semifinalista) AS semifinalistas,
               SUM(f.indicador_finalista)     AS finalistas,
               SUM(f.indicador_vencedor)      AS vencedores
        FROM fato_inscricao f
        JOIN dim_tempo t ON f.id_tempo = t.id_tempo
        GROUP BY t.ano, t.periodo ORDER BY t.ano
    """, conn)

    genero_literario_ano = pd.read_sql("""
        SELECT t.ano, l.genero_livro, COUNT(*) AS total
        FROM fato_inscricao f
        JOIN dim_tempo t ON f.id_tempo = t.id_tempo
        JOIN dim_livro  l ON f.id_livro  = l.id_livro
        GROUP BY t.ano, l.genero_livro ORDER BY t.ano
    """, conn)

    genero_autor_ano = pd.read_sql("""
        SELECT t.ano, a.genero_autor, COUNT(*) AS total
        FROM fato_inscricao f
        JOIN dim_tempo t ON f.id_tempo = t.id_tempo
        JOIN dim_autor  a ON f.id_autor  = a.id_autor
        WHERE a.genero_autor IN ('Feminino', 'Masculino')
        GROUP BY t.ano, a.genero_autor ORDER BY t.ano
    """, conn)

    funil_genero = pd.read_sql("""
        SELECT l.genero_livro,
               COUNT(*) AS inscritos,
               SUM(f.indicador_semifinalista) AS semifinalistas,
               SUM(f.indicador_finalista)     AS finalistas,
               SUM(f.indicador_vencedor)      AS vencedores,
               ROUND(100.0 * SUM(f.indicador_vencedor) / COUNT(*), 2) AS taxa_pct
        FROM fato_inscricao f
        JOIN dim_livro l ON f.id_livro = l.id_livro
        GROUP BY l.genero_livro ORDER BY COUNT(*) DESC
    """, conn)

    paises = pd.read_sql("""
        SELECT l.pais_primeira_edicao AS pais,
               COUNT(*) AS inscricoes,
               SUM(f.indicador_vencedor) AS vitorias
        FROM fato_inscricao f
        JOIN dim_livro l ON f.id_livro = l.id_livro
        GROUP BY l.pais_primeira_edicao
        HAVING COUNT(*) >= 5
        ORDER BY inscricoes DESC
    """, conn)

    genero_autor_total = pd.read_sql("""
        SELECT a.genero_autor,
               COUNT(*) AS inscritos,
               SUM(f.indicador_vencedor) AS vencedores
        FROM fato_inscricao f
        JOIN dim_autor a ON f.id_autor = a.id_autor
        GROUP BY a.genero_autor ORDER BY COUNT(*) DESC
    """, conn)

    faixa_etaria = pd.read_sql("""
        SELECT a.faixa_etaria_autor AS faixa,
               COUNT(*) AS inscritos,
               SUM(f.indicador_vencedor) AS vencedores
        FROM fato_inscricao f
        JOIN dim_autor a ON f.id_autor = a.id_autor
        WHERE a.faixa_etaria_autor != 'Não informado'
        GROUP BY a.faixa_etaria_autor ORDER BY COUNT(*) DESC
    """, conn)

    top_editoras = pd.read_sql("""
        SELECT e.nome_editora, e.tipo_publicacao,
               COUNT(*) AS inscricoes,
               SUM(f.indicador_vencedor) AS vitorias
        FROM fato_inscricao f
        JOIN dim_editora e ON f.id_editora = e.id_editora
        GROUP BY e.nome_editora, e.tipo_publicacao ORDER BY COUNT(*) DESC LIMIT 15
    """, conn)

    autopublicacao_ano = pd.read_sql("""
        SELECT t.ano, e.tipo_publicacao, COUNT(*) AS inscricoes
        FROM fato_inscricao f
        JOIN dim_tempo   t ON f.id_tempo   = t.id_tempo
        JOIN dim_editora e ON f.id_editora = e.id_editora
        GROUP BY t.ano, e.tipo_publicacao ORDER BY t.ano
    """, conn)

    editoras_vitorias = pd.read_sql("""
        SELECT e.nome_editora, e.sede_editora,
               COUNT(*) AS inscricoes,
               SUM(f.indicador_finalista) AS finalistas,
               SUM(f.indicador_vencedor)  AS vitorias
        FROM fato_inscricao f
        JOIN dim_editora e ON f.id_editora = e.id_editora
        GROUP BY e.nome_editora, e.sede_editora
        HAVING SUM(f.indicador_vencedor) > 0 ORDER BY SUM(f.indicador_vencedor) DESC
    """, conn)

    # conexão gerenciada pelo SQLAlchemy
    return (inscricoes_ano, genero_literario_ano, genero_autor_ano,
            funil_genero, paises, genero_autor_total, faixa_etaria,
            top_editoras, autopublicacao_ano, editoras_vitorias)


(df_ano, df_gen_lit, df_gen_autor_ano, df_funil,
 df_paises, df_gen_autor, df_faixa, df_editoras,
 df_autopub, df_edit_vit) = carregar_dados()


# ------------------------------------ PALETA DE CORES------------------------------------ 

CORES_GENERO  = {"Poesia": "#e8c97e", "Romance": "#7eb8e8",
                 "Conto": "#a8e87e",  "Crônica": "#e87eb8", "Dramaturgia": "#b87ee8"}
CORES_AUTOR   = {"Feminino": "#e87eb8", "Masculino": "#7eb8e8",
                 "Não informado": "#4a5568", "Prefiro não informar": "#a0aec0"}
TEMPLATE      = "plotly_dark"
COR_DESTAQUE  = "#e8c97e"
COR_SECUNDARIA = "#7eb8e8"


# ------------------------------------ SIDEBAR — FILTROS ------------------------------------ 

with st.sidebar:
    st.markdown("## 📚 Prêmio Oceanos")
    st.markdown("---")

    anos_disponiveis = sorted(df_ano["ano"].unique())
    ano_min, ano_max = st.select_slider(
        "Período",
        options=anos_disponiveis,
        value=(anos_disponiveis[0], anos_disponiveis[-1]),
    )

    generos_disponiveis = sorted(df_gen_lit["genero_livro"].unique())
    generos_sel = st.multiselect(
        "Gêneros literários",
        options=generos_disponiveis,
        default=generos_disponiveis,
    )

    st.markdown("---")
    st.caption("Fonte: Histórico de inscrições do Prêmio Oceanos · 2015–2024")

# ------------------------------------ Aplicar filtros ------------------------------------
anos_range = list(range(ano_min, ano_max + 1))
df_ano_f        = df_ano[df_ano["ano"].isin(anos_range)]
df_gen_lit_f    = df_gen_lit[df_gen_lit["ano"].isin(anos_range) & df_gen_lit["genero_livro"].isin(generos_sel)]
df_gen_autor_f  = df_gen_autor_ano[df_gen_autor_ano["ano"].isin(anos_range)]
df_autopub_f    = df_autopub[df_autopub["ano"].isin(anos_range)]


# ------------------------------------ CABEÇALHO------------------------------------
st.markdown('<p class="main-title">📚 Prêmio Oceanos de Literatura</p>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">Análise histórica das inscrições · 2015–2024</p>', unsafe_allow_html=True)
st.markdown("")


#------------------------------------  KPIs------------------------------------
total_ins  = int(df_ano_f["total"].sum())
total_semi = int(df_ano_f["semifinalistas"].sum())
total_fin  = int(df_ano_f["finalistas"].sum())
total_venc = int(df_ano_f["vencedores"].sum())

k1, k2, k3, k4 = st.columns(4)
for col, valor, label in [
    (k1, f"{total_ins:,}".replace(",", "."), "Inscrições"),
    (k2, str(total_semi), "Semifinalistas"),
    (k3, str(total_fin),  "Finalistas"),
    (k4, str(total_venc), "Vencedores"),
]:
    col.markdown(
        f'<div class="kpi-card"><div class="kpi-value">{valor}</div>'
        f'<div class="kpi-label">{label}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("")

# ------------------------------------ LINHA 1 — Evolução temporal + Gêneros literários------------------------------------ 

st.markdown('<p class="section-title">Evolução temporal</p>', unsafe_allow_html=True)
col1, col2 = st.columns([1.1, 1])

with col1:
    fig = px.bar(
        df_ano_f, x="ano", y="total",
        color="periodo",
        color_discrete_sequence=[COR_DESTAQUE, COR_SECUNDARIA, "#a8e87e"],
        title="Inscrições por ano",
        labels={"total": "Inscrições", "ano": "Ano", "periodo": "Período"},
        template=TEMPLATE,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=40, b=10, l=10, r=10),
        title_font_color=COR_DESTAQUE,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_pivot = df_gen_lit_f.groupby(["ano", "genero_livro"])["total"].sum().reset_index()
    fig = px.area(
        df_pivot, x="ano", y="total", color="genero_livro",
        color_discrete_map=CORES_GENERO,
        title="Gêneros literários por ano",
        labels={"total": "Inscrições", "ano": "Ano", "genero_livro": "Gênero"},
        template=TEMPLATE,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=40, b=10, l=10, r=10),
        title_font_color=COR_DESTAQUE,
    )
    st.plotly_chart(fig, use_container_width=True)



# ------------------------------------ LINHA 2 — Funil de seleção + Participação feminina ------------------------------------

st.markdown('<p class="section-title">Funil de seleção & Diversidade de gênero</p>', unsafe_allow_html=True)
col3, col4 = st.columns(2)

with col3:
    # Funil por gênero literário
    df_funil_sel = df_funil[df_funil["genero_livro"].isin(generos_sel)]
    fig = go.Figure()
    for col_nome, cor, label in [
        ("inscritos",      "#4a5568",    "Inscritos"),
        ("semifinalistas", "#7eb8e8",    "Semifinalistas"),
        ("finalistas",     COR_DESTAQUE, "Finalistas"),
        ("vencedores",     "#a8e87e",    "Vencedores"),
    ]:
        fig.add_trace(go.Bar(
            name=label,
            x=df_funil_sel["genero_livro"],
            y=df_funil_sel[col_nome],
            marker_color=cor,
        ))
    fig.update_layout(
        barmode="group",
        title="Funil por gênero literário",
        template=TEMPLATE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=40, b=10, l=10, r=10),
        title_font_color=COR_DESTAQUE,
        xaxis_title="Gênero",
        yaxis_title="Obras",
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    # Evolução feminina vs masculina
    df_pct = df_gen_autor_f.copy()
    total_por_ano = df_pct.groupby("ano")["total"].transform("sum")
    df_pct["pct"] = (df_pct["total"] / total_por_ano * 100).round(1)

    fig = px.line(
        df_pct, x="ano", y="pct", color="genero_autor",
        color_discrete_map={"Feminino": "#e87eb8", "Masculino": COR_SECUNDARIA},
        markers=True,
        title="Participação por gênero do autor (%)",
        labels={"pct": "%", "ano": "Ano", "genero_autor": "Gênero"},
        template=TEMPLATE,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=40, b=10, l=10, r=10),
        title_font_color=COR_DESTAQUE,
        yaxis=dict(range=[0, 100]),
    )
    fig.add_hline(y=50, line_dash="dot", line_color="#4a5568",
                  annotation_text="50%", annotation_position="right")
    st.plotly_chart(fig, use_container_width=True)





# ------------------------------------ LINHA 3 — Países + Faixa etária ------------------------------------

st.markdown('<p class="section-title">Diversidade & Representatividade</p>', unsafe_allow_html=True)
col5, col6 = st.columns(2)

with col5:
    df_paises_top = df_paises.head(8)
    fig = px.bar(
        df_paises_top, x="inscricoes", y="pais",
        orientation="h",
        color="vitorias",
        color_continuous_scale=["#1a2035", COR_DESTAQUE],
        title="Países — inscrições e vitórias",
        labels={"inscricoes": "Inscrições", "pais": "", "vitorias": "Vitórias"},
        template=TEMPLATE,
        text="inscricoes",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=10, l=10, r=10),
        title_font_color=COR_DESTAQUE,
        yaxis=dict(autorange="reversed"),
        coloraxis_colorbar=dict(title="Vitórias"),
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with col6:
    # Ordem de faixas etárias
    ordem_faixas = [
        "menos de 20 anos", "de 20 a 30 anos", "de 30 a 40 anos",
        "de 40 a 50 anos", "de 50 a 60 anos", "de 60 a 70 anos",
        "de 70 a 80 anos", "de 80 a 90 anos", "mais de 90 anos",
    ]
    df_faixa_ord = df_faixa.copy()
    df_faixa_ord["faixa"] = pd.Categorical(df_faixa_ord["faixa"], categories=ordem_faixas, ordered=True)
    df_faixa_ord = df_faixa_ord.sort_values("faixa")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Inscritos", x=df_faixa_ord["faixa"], y=df_faixa_ord["inscritos"],
        marker_color=COR_SECUNDARIA, opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        name="Vencedores", x=df_faixa_ord["faixa"], y=df_faixa_ord["vencedores"],
        marker_color=COR_DESTAQUE,
    ))
    fig.update_layout(
        barmode="overlay",
        title="Perfil etário — inscritos vs vencedores",
        template=TEMPLATE,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.25),
        margin=dict(t=40, b=10, l=10, r=10),
        title_font_color=COR_DESTAQUE,
        xaxis_tickangle=-35,
        xaxis_title="",
        yaxis_title="Obras",
    )
    st.plotly_chart(fig, use_container_width=True)





# ------------------------------------ LINHA 4 — Mercado editorial ------------------------------------

st.markdown('<p class="section-title">Mercado editorial</p>', unsafe_allow_html=True)
col7, col8 = st.columns([1.2, 1])

with col7:
    fig = px.bar(
        df_editoras.head(12), x="inscricoes", y="nome_editora",
        orientation="h",
        color="tipo_publicacao",
        color_discrete_map={
            "Autopublicação":     "#e87eb8",
            "Editora Tradicional": COR_SECUNDARIA,
        },
        title="Top 12 editoras por inscrições",
        labels={"inscricoes": "Inscrições", "nome_editora": "",
                "tipo_publicacao": "Tipo"},
        template=TEMPLATE,
        text="inscricoes",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=10, l=10, r=10),
        title_font_color=COR_DESTAQUE,
        yaxis=dict(autorange="reversed"),
        legend=dict(orientation="h", y=-0.15),
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with col8:
    # Autopublicação vs Tradicional por ano
    df_auto_pct = df_autopub_f.copy()
    total_ano_pub = df_auto_pct.groupby("ano")["inscricoes"].transform("sum")
    df_auto_pct["pct"] = (df_auto_pct["inscricoes"] / total_ano_pub * 100).round(1)

    fig = px.area(
        df_auto_pct, x="ano", y="pct", color="tipo_publicacao",
        color_discrete_map={
            "Autopublicação":     "#e87eb8",
            "Editora Tradicional": COR_SECUNDARIA,
        },
        title="Autopublicação vs editora tradicional (%)",
        labels={"pct": "%", "ano": "Ano", "tipo_publicacao": "Tipo"},
        template=TEMPLATE,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=10, l=10, r=10),
        title_font_color=COR_DESTAQUE,
        legend=dict(orientation="h", y=-0.2),
        yaxis=dict(range=[0, 100]),
    )
    st.plotly_chart(fig, use_container_width=True)




#  ------------------------------------ LINHA 5 — Editoras com vitórias (tabela detalhada) ------------------------------------

st.markdown('<p class="section-title">Editoras premiadas</p>', unsafe_allow_html=True)

df_edit_show = df_edit_vit.rename(columns={
    "nome_editora": "Editora",
    "sede_editora": "Sede",
    "inscricoes":   "Inscrições",
    "finalistas":   "Finalistas",
    "vitorias":     "Vitórias",
})

st.dataframe(
    df_edit_show,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Vitórias":    st.column_config.NumberColumn(format="%d 🏆"),
        "Finalistas":  st.column_config.NumberColumn(format="%d"),
        "Inscrições":  st.column_config.NumberColumn(format="%d"),
    },
)


# RODAPÉ

st.markdown("")
st.caption("Projeto Data Warehouse e BI — Prêmio Oceanos de Literatura · Análise e Desenvolvimento de Sistemas")
