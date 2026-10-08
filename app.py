import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

URL = "https://raw.githubusercontent.com/AlexandreLouzada/Dados-Simulados/main/Simulacao_Vacinacao_COVID_Municipios_2021_2024.xlsx"
ARQUIVO_LOCAL = "data/Simulacao_Vacinacao_COVID_Municipios_2021_2024.xlsx"

COLUNAS = {
    "Município": "municipio",
    "Ano": "ano",
    "População Estimada": "populacao",
    "Pessoas Vacinadas": "vacinados",
    "Internações por COVID-19": "internacoes",
}
AZUL = "#1f77b4"
VERMELHO = "#d62728"
CINZA = "#b0b0b0"

st.set_page_config(page_title="Vacinação COVID-19 e internações", layout="wide")


# ---------- dados ----------
def preparar(df):
    df = df.rename(columns=COLUNAS)
    df["cobertura"] = df["vacinados"] / df["populacao"] * 100
    df["internacoes_100k"] = df["internacoes"] / df["populacao"] * 100000
    df["acima_100"] = df["cobertura"] > 100
    df["faixa_cobertura"] = pd.cut(
        df["cobertura"],
        bins=[0, 60, 80, np.inf],
        labels=["até 60%", "60% a 80%", "acima de 80%"],
    )
    return df.sort_values(["municipio", "ano"]).reset_index(drop=True)


@st.cache_data
def base_padrao():
    # tenta o GitHub do professor, se falhar usa a copia da pasta data
    try:
        df = pd.read_excel(URL)
    except Exception:
        df = pd.read_excel(ARQUIVO_LOCAL)
    return preparar(df)


def ler_upload(arquivo):
    if arquivo.name.lower().endswith(".csv"):
        df = pd.read_csv(arquivo)
    else:
        df = pd.read_excel(arquivo)
    faltando = [c for c in COLUNAS if c not in df.columns]
    if faltando:
        raise ValueError("Colunas que faltam: " + ", ".join(faltando))
    return preparar(df)


# ---------- funcoes de apoio ----------
def correlacao(d, metodo="pearson"):
    if len(d) < 3:
        return np.nan
    x, y = d["cobertura"], d["internacoes_100k"]
    if metodo == "spearman":
        # Spearman = Pearson sobre os rankings (evita depender do scipy)
        x, y = x.rank(), y.rank()
    return x.corr(y)


def fmt(x, casas=2):
    return "—" if pd.isna(x) else f"{x:.{casas}f}".replace(".", ",")


def milhar(x):
    return f"{x:,.0f}".replace(",", ".")


def descricao_corr(r):
    if pd.isna(r):
        return "não pôde ser calculada com esse recorte"
    forca = "fraca" if abs(r) < 0.3 else "moderada" if abs(r) < 0.7 else "forte"
    sentido = "negativa" if r < 0 else "positiva"
    return f"{sentido} {forca} ({fmt(r)})"


def estilo(fig, altura=380):
    fig.update_layout(template="plotly_white", height=altura, margin=dict(l=10, r=10, t=50, b=10))
    return fig


# ---------- barra lateral ----------
base = base_padrao()

st.sidebar.header("Filtros")
arquivo = st.sidebar.file_uploader(
    "Carregar outra base com as mesmas colunas", type=["xlsx", "csv"]
)
if arquivo is not None:
    try:
        base = ler_upload(arquivo)
        st.sidebar.success("Base carregada.")
    except Exception as erro:
        st.sidebar.error(f"Não consegui usar esse arquivo. {erro}")

todos_mun = sorted(base["municipio"].unique())
todos_anos = sorted(base["ano"].unique())

municipios = st.sidebar.multiselect("Municípios", todos_mun, default=todos_mun)
anos = st.sidebar.multiselect("Anos", todos_anos, default=todos_anos)
sem_inconsistentes = st.sidebar.checkbox("Excluir cobertura acima de 100%", value=False)
st.sidebar.caption(
    "Alguns registros têm mais vacinados do que habitantes (cobertura acima de 100%). "
    "Marque a opção para ver a análise sem eles."
)

d = base[base["municipio"].isin(municipios) & base["ano"].isin(anos)]
if sem_inconsistentes:
    d = d[~d["acima_100"]]

# ---------- topo ----------
st.title("Análise da Vacinação contra COVID-19 e das Internações")
st.caption(
    "Linguagens de Programação · Professor: Alexandre Louzada · Aluno: André Luiz dos Santos Ferreira"
)
st.markdown(
    "**Problema:** verificar se os municípios e anos com maior cobertura vacinal tiveram menos "
    "internações por COVID-19, para apoiar a decisão de onde reforçar as campanhas de vacinação."
)

if d.empty:
    st.warning("Nenhum registro com os filtros escolhidos.")
    st.stop()

media_mun = d.groupby("municipio")[["cobertura", "internacoes_100k"]].mean()

k = st.columns(6)
k[0].metric("Cobertura vacinal média", f"{d['cobertura'].mean():.1f}%".replace(".", ","))
k[1].metric("Internações por 100 mil", milhar(d["internacoes_100k"].mean()))
k[2].metric("Total de internações", milhar(d["internacoes"].sum()))
k[3].metric("Maior cobertura", media_mun["cobertura"].idxmax())
k[4].metric("Menor taxa de internação", media_mun["internacoes_100k"].idxmin())
k[5].metric("Correlação (Pearson)", fmt(correlacao(d)))

anos_txt = f"{d['ano'].min()} a {d['ano'].max()}"
st.caption(
    f"Recorte: {d['municipio'].nunique()} município(s), {anos_txt}, {len(d)} registros. "
    "Internações por 100 mil = internações ÷ população × 100.000."
)

# ---------- evolucao ----------
st.subheader("Evolução temporal")
visao = st.radio("Visão", ["Média dos municípios", "Cada município"], horizontal=True)

col1, col2 = st.columns(2)
if visao == "Média dos municípios":
    por_ano = d.groupby("ano")[["cobertura", "internacoes_100k"]].mean().reset_index()
    f1 = px.line(por_ano, x="ano", y="cobertura", markers=True,
                 labels={"ano": "Ano", "cobertura": "Cobertura (%)"})
    f1.update_traces(line_color=AZUL)
    f2 = px.line(por_ano, x="ano", y="internacoes_100k", markers=True,
                 labels={"ano": "Ano", "internacoes_100k": "Internações por 100 mil hab."})
    f2.update_traces(line_color=VERMELHO)
else:
    f1 = px.line(d, x="ano", y="cobertura", color="municipio", markers=True,
                 labels={"ano": "Ano", "cobertura": "Cobertura (%)", "municipio": "Município"})
    f2 = px.line(d, x="ano", y="internacoes_100k", color="municipio", markers=True,
                 labels={"ano": "Ano", "internacoes_100k": "Internações por 100 mil hab.",
                         "municipio": "Município"})
f1.update_layout(title="Cobertura vacinal por ano", xaxis=dict(dtick=1))
f2.update_layout(title="Internações por 100 mil hab. por ano", xaxis=dict(dtick=1))
col1.plotly_chart(estilo(f1), width="stretch")
col2.plotly_chart(estilo(f2), width="stretch")

# ---------- comparacao entre municipios ----------
st.subheader("Comparação entre municípios")
col1, col2 = st.columns(2)

m1 = media_mun["cobertura"].sort_values()
f3 = px.bar(x=m1.values, y=m1.index, orientation="h",
            labels={"x": "Cobertura média (%)", "y": "Município"})
f3.update_traces(marker_color=AZUL)
f3.update_layout(title="Cobertura vacinal média por município")
col1.plotly_chart(estilo(f3), width="stretch")

m2 = media_mun["internacoes_100k"].sort_values()
f4 = px.bar(x=m2.values, y=m2.index, orientation="h",
            labels={"x": "Internações por 100 mil hab. (média)", "y": "Município"})
f4.update_traces(marker_color=VERMELHO)
f4.update_layout(title="Internações por 100 mil hab. por município")
col2.plotly_chart(estilo(f4), width="stretch")

# ---------- relacao ----------
st.subheader("Relação entre vacinação e internações")
ate100 = d[~d["acima_100"]]
acima = d[d["acima_100"]]

col1, col2 = st.columns([3, 2])

f5 = go.Figure()
for dados, nome, cor in [(ate100, "Cobertura até 100%", AZUL), (acima, "Cobertura acima de 100%", CINZA)]:
    if not dados.empty:
        f5.add_trace(go.Scatter(
            x=dados["cobertura"], y=dados["internacoes_100k"], mode="markers", name=nome,
            marker=dict(color=cor, size=9),
            customdata=dados[["municipio", "ano"]],
            hovertemplate="%{customdata[0]} (%{customdata[1]})<br>Cobertura: %{x:.1f}%<br>"
                          "Internações por 100 mil: %{y:.0f}<extra></extra>",
        ))
if len(ate100) >= 3:
    a, b = np.polyfit(ate100["cobertura"], ate100["internacoes_100k"], 1)
    xs = np.linspace(ate100["cobertura"].min(), ate100["cobertura"].max(), 50)
    f5.add_trace(go.Scatter(x=xs, y=a * xs + b, mode="lines", name="Tendência (até 100%)",
                            line=dict(color=AZUL, width=2)))
f5.update_layout(title="Cobertura vacinal x internações por 100 mil hab.",
                 xaxis_title="Cobertura vacinal (%)", yaxis_title="Internações por 100 mil hab.",
                 legend=dict(orientation="h", y=-0.2))
col1.plotly_chart(estilo(f5, 420), width="stretch")

with col2:
    c1, c2 = st.columns(2)
    c1.metric("Pearson", fmt(correlacao(d)))
    c2.metric("Spearman", fmt(correlacao(d, "spearman")))
    st.caption(
        "Pearson mede a relação em linha reta. Spearman usa só a ordem dos valores. "
        "Valores negativos indicam que mais cobertura anda junto com menos internações."
    )
    faixa = d.groupby("faixa_cobertura", observed=True)["internacoes_100k"].mean().reset_index()
    f6 = px.bar(faixa, x="faixa_cobertura", y="internacoes_100k", text_auto=".0f",
                labels={"faixa_cobertura": "Faixa de cobertura",
                        "internacoes_100k": "Internações por 100 mil hab."})
    f6.update_traces(marker_color=AZUL)
    f6.update_layout(title="Internações médias por faixa de cobertura")
    st.plotly_chart(estilo(f6, 300), width="stretch")

por_mun = d.groupby("municipio").filter(lambda g: len(g) >= 3)
if por_mun.empty:
    st.info("Escolha pelo menos 3 anos para ver a correlação dentro de cada município.")
else:
    corr_mun = por_mun.groupby("municipio")[["cobertura", "internacoes_100k"]].apply(
        lambda g: g["cobertura"].corr(g["internacoes_100k"])
    ).dropna().sort_values()
    f7 = px.bar(x=corr_mun.values, y=corr_mun.index, orientation="h",
                labels={"x": "Correlação de Pearson", "y": "Município"})
    f7.update_traces(marker_color=[AZUL if v < 0 else VERMELHO for v in corr_mun.values])
    f7.update_layout(title="Correlação entre cobertura e internações em cada município")
    st.plotly_chart(estilo(f7, 350), width="stretch")
    st.caption(
        "Azul: mais vacinação anda junto com menos internações. Vermelho: o contrário. "
        "Cada município tem no máximo 4 anos, então os valores são sensíveis."
    )

# ---------- mapa de calor ----------
st.subheader("Mapa de calor por município e ano")
indicador = st.selectbox(
    "Indicador", ["Internações por 100 mil hab.", "Cobertura vacinal (%)"]
)
coluna = "internacoes_100k" if indicador.startswith("Internações") else "cobertura"
tabela_calor = d.pivot_table(index="municipio", columns="ano", values=coluna)
f8 = px.imshow(tabela_calor, text_auto=".0f", aspect="auto",
               color_continuous_scale="Blues" if coluna == "cobertura" else "Reds",
               labels={"x": "Ano", "y": "Município", "color": indicador})
f8.update_xaxes(type="category")
f8.update_layout(title=indicador + " por município e ano")
st.plotly_chart(estilo(f8, 420), width="stretch")

# ---------- tabela ----------
st.subheader("Resumo por município e ano")
resumo = d[["municipio", "ano", "populacao", "vacinados", "internacoes",
            "cobertura", "internacoes_100k"]].copy()
resumo.columns = ["Município", "Ano", "População", "Vacinados", "Internações",
                  "Cobertura (%)", "Internações por 100 mil"]
st.dataframe(
    resumo,
    hide_index=True,
    width="stretch",
    column_config={
        "Ano": st.column_config.NumberColumn(format="%d"),
        "População": st.column_config.NumberColumn(format="%d"),
        "Vacinados": st.column_config.NumberColumn(format="%d"),
        "Internações": st.column_config.NumberColumn(format="%d"),
        "Cobertura (%)": st.column_config.NumberColumn(format="%.1f"),
        "Internações por 100 mil": st.column_config.NumberColumn(format="%.0f"),
    },
)

# ---------- interpretacao ----------
st.subheader("Interpretação e conclusão executiva")

ano_cob = d.groupby("ano")["cobertura"].mean()
ano_int = d.groupby("ano")["internacoes_100k"].mean()
texto = (
    f"Neste recorte, {media_mun['cobertura'].idxmax()} tem a maior cobertura média "
    f"({fmt(media_mun['cobertura'].max(), 1)}%) e {media_mun['internacoes_100k'].idxmin()} tem a menor "
    f"taxa de internação ({milhar(media_mun['internacoes_100k'].min())} por 100 mil). "
    f"O ano de maior cobertura é {ano_cob.idxmax()} e o de menor taxa de internação é {ano_int.idxmin()}. "
    f"A correlação entre cobertura e internações é {descricao_corr(correlacao(d))}."
)
if not sem_inconsistentes and d["acima_100"].any():
    texto += (
        f" Atenção: {int(d['acima_100'].sum())} registro(s) têm cobertura acima de 100%, "
        "o que distorce a correlação. Marque a opção da barra lateral para ver sem eles."
    )
st.info(texto)

# conclusao geral do trabalho (sempre a base padrao completa)
ref = base_padrao()
ref_sem = ref[~ref["acima_100"]]
ref_ano = ref.groupby("ano")["internacoes_100k"].mean()
queda = (1 - ref_ano[2022] / ref_ano[2021]) * 100
st.markdown(
    f"**Conclusão do trabalho (base completa):** com todos os registros a correlação é "
    f"{descricao_corr(correlacao(ref))}. Sem os {int(ref['acima_100'].sum())} registros com cobertura "
    f"acima de 100%, ela é {descricao_corr(correlacao(ref_sem))}. Em 2022, ano de maior cobertura, as "
    f"internações caíram cerca de {queda:.0f}% em relação a 2021. Vitória e Serra vão no sentido contrário "
    "da hipótese. Existe uma tendência de menos internações onde a cobertura foi maior, mas ela é moderada "
    "e não prova causa e efeito. A base é simulada e tem só 32 observações."
)
st.caption("Dados: repositório Dados-Simulados do professor Alexandre Louzada (base simulada).")
