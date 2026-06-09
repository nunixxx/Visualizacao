import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch

# ── 1. Leitura e limpeza ──────────────────────────────────────────────────────

# Leitura direta do JSON para DataFrame
dados_raw = pd.read_json("data.json")

# A chave do município pode vir com problemas de formatação. 
# Renomeamos a primeira coluna pelo índice para facilitar.
dados_raw.rename(columns={dados_raw.columns[0]: "Municipio"}, inplace=True)

# Trabalharemos com uma cópia para preservar o raw
dados = dados_raw.copy()

# Função equivalente ao parse_pop (remove ponto de milhar e converte para numérico)
def parse_pop(coluna):
    return dados[coluna].astype(str).str.replace('.', '', regex=False).astype(float)

# Mutate: criando as novas colunas
dados['pop2000'] = parse_pop('Demografia Total 2000 (-)')
dados['pop2024'] = parse_pop('Demografia Total 2024 (-)')
dados['variacao_pct'] = (dados['pop2024'] - dados['pop2000']) / dados['pop2000'] * 100

# case_when -> equivalente em Python usando np.select
condicoes = [
    dados['variacao_pct'] > 30,
    (dados['variacao_pct'] > 0) & (dados['variacao_pct'] <= 30),
    (dados['variacao_pct'] >= -10) & (dados['variacao_pct'] <= 0),
    dados['variacao_pct'] < -10
]

niveis_categoria = [
    "Boom (>+30%)",
    "Crescimento (0–30%)",
    "Declínio leve (0 a -10%)",
    "Esvaziamento (<-10%)"
]

dados['categoria'] = np.select(condicoes, niveis_categoria, default="Esvaziamento (<-10%)")

# Transformando em variável categórica ordenada (equivalente ao factor com levels)
dados['categoria'] = pd.Categorical(dados['categoria'], categories=niveis_categoria, ordered=True)


# ── 2. Seleciona os extremos para o gráfico (top/bottom 20) ──────────────────

n_each = 20

# slice_max e slice_min equivalentes
top = dados.nlargest(n_each, 'variacao_pct')
bottom = dados.nsmallest(n_each, 'variacao_pct')

# bind_rows, distinct e arrange
dados_plot = pd.concat([top, bottom]).drop_duplicates(subset=['Municipio'])
dados_plot = dados_plot.sort_values('variacao_pct')


# ── 3. Paleta e tema ──────────────────────────────────────────────────────────

cores = {
    "Boom (>+30%)": "#1D9E75",
    "Crescimento (0–30%)": "#9FE1CB",
    "Declínio leve (0 a -10%)": "#F0997B",
    "Esvaziamento (<-10%)": "#D85A30"
}


# ── 4. Métricas de resumo (para o subtítulo) ──────────────────────────────────

n_crescimento = (dados['variacao_pct'] > 0).sum()
n_declinio = (dados['variacao_pct'] <= 0).sum()

# slice_max e slice_min (n=1)
maior_ganho = dados.loc[dados['variacao_pct'].idxmax()]
maior_perda = dados.loc[dados['variacao_pct'].idxmin()]

# Usando f-strings nativas no lugar de glue::glue
subtitulo = (
    f"{n_crescimento} municípios cresceram · {n_declinio} encolheram | "
    f"Maior ganho: {maior_ganho['Municipio']} (+{maior_ganho['variacao_pct']:.1f}%) · "
    f"Maior perda: {maior_perda['Municipio']} ({maior_perda['variacao_pct']:.1f}%)"
)


# ── 5. Gráfico ────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(10, 8), dpi=150)

# Mapeia as cores de acordo com a categoria de cada linha em dados_plot
cores_barras = dados_plot['categoria'].map(cores)

# geom_col (barras horizontais)
ax.barh(dados_plot['Municipio'], dados_plot['variacao_pct'], color=cores_barras, height=0.75)

# geom_vline no zero
ax.axvline(0, color='grey', linewidth=0.8)

# scale_x_continuous com labels (formatação do +)
def formata_pct(x, pos):
    return f"+{x:.0f}%" if x > 0 else f"{x:.0f}%"
ax.xaxis.set_major_formatter(FuncFormatter(formata_pct))

# Títulos e Eixos
ax.set_xlabel("Variação populacional (%)", fontsize=9, color="dimgrey", labelpad=8)
ax.set_ylabel("") # Remove o título do eixo Y

# Replicando a estilização customizada de texto do ggplot (theme / labs)
plt.figtext(0.125, 0.95, "Municípios que mais cresceram e mais encolheram no RS (2000–2024)", 
            fontsize=13, fontweight='bold')
plt.figtext(0.125, 0.92, subtitulo, fontsize=10, color="dimgrey")

caption = (
    "Fonte: Estimativas Populacionais RIPSA/IBGE.\n"
    f"Exibindo os {n_each} municípios com maior crescimento e os {n_each} com maior declínio.\n"
    "Municípios litorâneos e da Serra lideraram o crescimento; pequenos municípios rurais enfrentaram forte êxodo."
)
plt.figtext(0.125, 0.02, caption, fontsize=8.5, color="dimgrey", ha="left")

# Replicando o "theme_minimal"
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('grey')
ax.tick_params(axis='y', length=0, labelsize=8.5)
ax.tick_params(axis='x', colors='dimgrey', labelsize=8.5)
ax.grid(axis='x', linestyle='-', alpha=0.15) # panel.grid.major.x

# Configurando a legenda baseada nos fatores
elementos_legenda = [Patch(facecolor=cores[cat], label=cat) for cat in niveis_categoria]
ax.legend(handles=elementos_legenda, loc='lower center', bbox_to_anchor=(0.5, -0.15),
          ncol=4, frameon=False, fontsize=8.5)

# Ajuste de margens para não cortar os textos do figtext
plt.subplots_adjust(top=0.88, bottom=0.2, left=0.25, right=0.95)


# ── 6. Salvar ─────────────────────────────────────────────────────────────────

# Equivalente ao ggsave
plt.savefig("grafico_populacao_rs.png", dpi=150, facecolor="white", bbox_inches='tight')

print("✓ Salvo em grafico_populacao_rs.png")