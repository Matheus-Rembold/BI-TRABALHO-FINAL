-- =============================================================================
-- CONSULTAS ANALÍTICAS — Data Warehouse do Prêmio Oceanos
-- Banco: oceanos_dw.db (SQLite)
-- =============================================================================


-- =============================================================================
-- TEMA 1 — EVOLUÇÃO TEMPORAL
-- =============================================================================


-- Q01: Inscrições por ano
-- Mostra o crescimento do prêmio ao longo dos 10 anos
-- -----------------------------------------------------------------------------
SELECT
    t.ano,
    t.periodo,
    COUNT(*) AS total_inscricoes
FROM fato_inscricao f
JOIN dim_tempo t ON f.id_tempo = t.id_tempo
GROUP BY t.ano, t.periodo
ORDER BY t.ano;


-- Q02: Distribuição de gêneros literários por ano
-- Permite identificar quais gêneros crescem ou perdem espaço com o tempo
-- -----------------------------------------------------------------------------
SELECT
    t.ano,
    l.genero_livro,
    COUNT(*) AS total
FROM fato_inscricao f
JOIN dim_tempo      t ON f.id_tempo  = t.id_tempo
JOIN dim_livro      l ON f.id_livro  = l.id_livro
GROUP BY t.ano, l.genero_livro
ORDER BY t.ano, total DESC;


-- Q03: Evolução da participação feminina por ano
-- Compara inscrições de autoras mulheres versus autores homens ao longo do tempo
-- -----------------------------------------------------------------------------
SELECT
    t.ano,
    a.genero_autor,
    COUNT(*)                                          AS total,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY t.ano), 1) AS pct
FROM fato_inscricao f
JOIN dim_tempo t ON f.id_tempo = t.id_tempo
JOIN dim_autor a ON f.id_autor = a.id_autor
WHERE a.genero_autor IN ('Feminino', 'Masculino')
GROUP BY t.ano, a.genero_autor
ORDER BY t.ano, a.genero_autor;


-- =============================================================================
-- TEMA 2 — FUNIL DE SELEÇÃO
-- =============================================================================


-- Q04: Funil completo por ano (inscritos → semi → final → vencedor)
-- Mostra quantas obras passaram em cada etapa a cada edição do prêmio
-- -----------------------------------------------------------------------------
SELECT
    t.ano,
    COUNT(*)                          AS inscritos,
    SUM(f.indicador_semifinalista)    AS semifinalistas,
    SUM(f.indicador_finalista)        AS finalistas,
    SUM(f.indicador_vencedor)         AS vencedores,
    ROUND(100.0 * SUM(f.indicador_semifinalista) / COUNT(*), 1) AS taxa_semi_pct,
    ROUND(100.0 * SUM(f.indicador_finalista)     / COUNT(*), 2) AS taxa_final_pct,
    ROUND(100.0 * SUM(f.indicador_vencedor)      / COUNT(*), 3) AS taxa_vitoria_pct
FROM fato_inscricao f
JOIN dim_tempo t ON f.id_tempo = t.id_tempo
GROUP BY t.ano
ORDER BY t.ano;


-- Q05: Taxa de conversão para vencedor por gênero literário
-- Revela quais gêneros têm mais chance de vencer
-- -----------------------------------------------------------------------------
SELECT
    l.genero_livro,
    COUNT(*)                                                       AS inscritos,
    SUM(f.indicador_semifinalista)                                 AS semifinalistas,
    SUM(f.indicador_finalista)                                     AS finalistas,
    SUM(f.indicador_vencedor)                                      AS vencedores,
    ROUND(100.0 * SUM(f.indicador_vencedor) / COUNT(*), 2)        AS taxa_vitoria_pct
FROM fato_inscricao f
JOIN dim_livro l ON f.id_livro = l.id_livro
GROUP BY l.genero_livro
ORDER BY taxa_vitoria_pct DESC;


-- Q06: Concentração de vitórias por país de publicação
-- Quais países dominam as premiações?
-- -----------------------------------------------------------------------------
SELECT
    l.pais_primeira_edicao,
    COUNT(*)                       AS inscricoes,
    SUM(f.indicador_vencedor)      AS vitorias,
    ROUND(100.0 * SUM(f.indicador_vencedor) / COUNT(*), 2) AS taxa_vitoria_pct
FROM fato_inscricao f
JOIN dim_livro l ON f.id_livro = l.id_livro
GROUP BY l.pais_primeira_edicao
HAVING inscricoes >= 10
ORDER BY vitorias DESC;


-- =============================================================================
-- TEMA 3 — DIVERSIDADE E REPRESENTATIVIDADE
-- =============================================================================


-- Q07: Distribuição de gênero dos autores — inscritos vs premiados
-- Compara se a premiação é proporcional à participação por gênero
-- -----------------------------------------------------------------------------
SELECT
    a.genero_autor,
    COUNT(*)                                                       AS inscritos,
    SUM(f.indicador_vencedor)                                      AS vencedores,
    ROUND(100.0 * COUNT(*)               / SUM(COUNT(*))   OVER (), 1) AS pct_inscritos,
    ROUND(100.0 * SUM(f.indicador_vencedor) / SUM(SUM(f.indicador_vencedor)) OVER (), 1) AS pct_vencedores
FROM fato_inscricao f
JOIN dim_autor a ON f.id_autor = a.id_autor
GROUP BY a.genero_autor
ORDER BY inscritos DESC;


-- Q08: Perfil etário — inscritos vs vencedores
-- Revela se o prêmio favorece autores de determinada faixa de idade
-- -----------------------------------------------------------------------------
SELECT
    a.faixa_etaria_autor,
    COUNT(*)                                                      AS inscritos,
    SUM(f.indicador_vencedor)                                     AS vencedores,
    ROUND(100.0 * SUM(f.indicador_vencedor) / COUNT(*), 2)       AS taxa_vitoria_pct
FROM fato_inscricao f
JOIN dim_autor a ON f.id_autor = a.id_autor
WHERE a.faixa_etaria_autor != 'Não informado'
GROUP BY a.faixa_etaria_autor
ORDER BY inscritos DESC;


-- Q09: Ranking de países por inscrições e vitórias
-- Panorama geográfico completo do prêmio
-- -----------------------------------------------------------------------------
SELECT
    a.nome_pais_autor                                             AS pais_autor,
    COUNT(*)                                                      AS inscricoes,
    SUM(f.indicador_semifinalista)                                AS semifinalistas,
    SUM(f.indicador_finalista)                                    AS finalistas,
    SUM(f.indicador_vencedor)                                     AS vitorias
FROM fato_inscricao f
JOIN dim_autor a ON f.id_autor = a.id_autor
WHERE a.nome_pais_autor != 'Não informado'
GROUP BY a.nome_pais_autor
HAVING inscricoes >= 5
ORDER BY inscricoes DESC;


-- =============================================================================
-- TEMA 4 — MERCADO EDITORIAL
-- =============================================================================


-- Q10: Top 15 editoras por volume de inscrições
-- Mostra quais editoras mais apostam no prêmio
-- -----------------------------------------------------------------------------
SELECT
    e.nome_editora,
    e.tipo_publicacao,
    e.sede_editora,
    COUNT(*)                       AS inscricoes,
    SUM(f.indicador_semifinalista) AS semifinalistas,
    SUM(f.indicador_finalista)     AS finalistas,
    SUM(f.indicador_vencedor)      AS vitorias
FROM fato_inscricao f
JOIN dim_editora e ON f.id_editora = e.id_editora
GROUP BY e.nome_editora, e.tipo_publicacao, e.sede_editora
ORDER BY inscricoes DESC
LIMIT 15;


-- Q11: Editoras com vitórias — concentração editorial
-- Revela se poucas editoras dominam as premiações
-- -----------------------------------------------------------------------------
SELECT
    e.nome_editora,
    e.sede_editora,
    COUNT(*)                       AS inscricoes,
    SUM(f.indicador_finalista)     AS finalistas,
    SUM(f.indicador_vencedor)      AS vitorias
FROM fato_inscricao f
JOIN dim_editora e ON f.id_editora = e.id_editora
GROUP BY e.nome_editora, e.sede_editora
HAVING vitorias > 0
ORDER BY vitorias DESC;


-- Q12: Autopublicação vs editora tradicional por ano
-- Mostra o crescimento da publicação independente ao longo do tempo
-- -----------------------------------------------------------------------------
SELECT
    t.ano,
    e.tipo_publicacao,
    COUNT(*)                                                           AS inscricoes,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY t.ano), 1) AS pct_do_ano
FROM fato_inscricao f
JOIN dim_tempo   t ON f.id_tempo   = t.id_tempo
JOIN dim_editora e ON f.id_editora = e.id_editora
GROUP BY t.ano, e.tipo_publicacao
ORDER BY t.ano, e.tipo_publicacao;