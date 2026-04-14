# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
from sqlalchemy import create_engine


# =============================================================================
# 1. EXTRACT
# =============================================================================

dados = pd.read_csv(
    "data/world_oceanos_mapeamento_historico_inscritos.csv",
    encoding="utf-8"
)

print(f"[ETL] Arquivo carregado — {len(dados)} linhas brutas.")



# =============================================================================
# 2. TRANSFORM
# =============================================================================

# --- 2.1 Normalização de strings (remover espaços extras) ---
str_cols = dados.select_dtypes(include="object").columns
dados[str_cols] = dados[str_cols].apply(lambda col: col.str.strip())

# --- 2.2 Preencher nulos com categorias explícitas ---
dados["genero_autor"]       = dados["genero_autor"].fillna("Não informado")
dados["faixa_etaria_autor"] = dados["faixa_etaria_autor"].fillna("Não informado")
dados["nome_pais_autor"]    = dados["nome_pais_autor"].fillna("Não informado")
dados["nacionaldade_autor"] = dados["nacionaldade_autor"].fillna("Não informado")
dados["sede_editora"]       = dados["sede_editora"].fillna("Não informado")
dados["site_editora"]       = dados["site_editora"].fillna("")
dados["sigla_pais_iso2"]    = dados["sigla_pais_iso2"].fillna("XX")

# --- 2.3 Converter indicadores "Sim"/"Não" para 1/0 ---
for col in ["indicador_vencedor", "indicador_finalista", "indicador_semifinalista"]:
    dados[col] = (dados[col].str.lower() == "sim").astype(int)

# --- 2.4 Derivar nível de seleção (nível máximo atingido no funil) ---
def nivel_selecao(row):
    if row["indicador_vencedor"] == 1:
        return "Vencedor"
    if row["indicador_finalista"] == 1:
        return "Finalista"
    if row["indicador_semifinalista"] == 1:
        return "Semifinalista"
    return "Inscrito"

dados["nivel_selecao"] = dados.apply(nivel_selecao, axis=1)

# --- 2.5 Derivar tipo de publicação ---
dados["tipo_publicacao"] = dados["nome_editora"].apply(
    lambda x: "Autopublicação" if str(x).strip().lower() == "autopublicação"
    else "Editora Tradicional"
)

print(f"[ETL] Transform concluído — {dados['nivel_selecao'].value_counts().to_dict()}")


# =============================================================================
# 3. DIMENSÕES
# =============================================================================

# DIM_TEMPO
dim_tempo = pd.DataFrame({"ano": sorted(dados["ano"].unique())})
dim_tempo["decada"]  = dim_tempo["ano"].apply(lambda a: "2010s" if a < 2020 else "2020s")
dim_tempo["periodo"] = dim_tempo["ano"].apply(
    lambda a: "Início (2015-2018)"      if a <= 2018
    else      "Crescimento (2019-2021)" if a <= 2021
    else      "Consolidação (2022-2024)"
)
dim_tempo.insert(0, "id_tempo", range(1, len(dim_tempo) + 1))

# DIM_AUTOR
# Um autor pode inscrever obras em vários anos — usa os dados do ano mais recente
dim_autor = (
    dados.sort_values("ano", ascending=False)
    .drop_duplicates(subset=["nome_autor"])
    [["nome_autor", "genero_autor", "faixa_etaria_autor",
      "nacionaldade_autor", "nome_pais_autor", "sigla_pais_iso2"]]
    .reset_index(drop=True)
)
dim_autor.insert(0, "id_autor", range(1, len(dim_autor) + 1))

# DIM_LIVRO
dim_livro = (
    dados[["titulo_livro", "genero_livro", "pais_primeira_edicao", "nome_autor"]]
    .drop_duplicates(subset=["titulo_livro", "nome_autor"])
    .reset_index(drop=True)
)
dim_livro.insert(0, "id_livro", range(1, len(dim_livro) + 1))

# DIM_EDITORA
dim_editora = (
    dados[["nome_editora", "sede_editora", "site_editora", "tipo_publicacao"]]
    .drop_duplicates(subset=["nome_editora"])
    .reset_index(drop=True)
)
dim_editora.insert(0, "id_editora", range(1, len(dim_editora) + 1))


# =============================================================================
# 4. FATO
# =============================================================================

fato = (
    dados
    .merge(dim_tempo[["id_tempo", "ano"]],
           on="ano", how="left")
    .merge(dim_autor[["id_autor", "nome_autor"]],
           on="nome_autor", how="left")
    .merge(dim_livro[["id_livro", "titulo_livro", "nome_autor"]],
           on=["titulo_livro", "nome_autor"], how="left")
    .merge(dim_editora[["id_editora", "nome_editora"]],
           on="nome_editora", how="left")
)

fato_inscricao = fato[[
    "id_tempo", "id_autor", "id_livro", "id_editora",
    "indicador_vencedor", "indicador_finalista", "indicador_semifinalista",
    "nivel_selecao"
]].copy()

fato_inscricao.insert(0, "id_inscricao", range(1, len(fato_inscricao) + 1))


# =============================================================================
# 5. LOAD
# =============================================================================

conn = create_engine('postgresql+psycopg2://postgres:masterkey@localhost:5432/dwfinal')


dim_tempo.to_sql("dim_tempo",           conn, index=False, if_exists="replace")
dim_autor.to_sql("dim_autor",           conn, index=False, if_exists="replace")
dim_livro.to_sql("dim_livro",           conn, index=False, if_exists="replace")
dim_editora.to_sql("dim_editora",       conn, index=False, if_exists="replace")
fato_inscricao.to_sql("fato_inscricao", conn, index=False, if_exists="replace")


print("[ETL] Carga concluída com sucesso!")
print(f"  dim_tempo      : {len(dim_tempo)} registros")
print(f"  dim_autor      : {len(dim_autor)} registros")
print(f"  dim_livro      : {len(dim_livro)} registros")
print(f"  dim_editora    : {len(dim_editora)} registros")
print(f"  fato_inscricao : {len(fato_inscricao)} registros")
