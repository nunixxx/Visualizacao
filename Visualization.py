"""
Mapa de Crescimento Demográfico — Rio Grande do Sul (2000–2024)
Fonte: RIPSA/IBGE
"""

import json
import folium
import pandas as pd
import branca.colormap as cm
from folium import MacroElement
from jinja2 import Template
from pathlib import Path


# ── Configurações ──────────────────────────────────────────────────────────────

DATA_PATH  = "datas/demografia_RS.json"
MALHA_PATH = "datas/malha_rs.json"
OUTPUT     = "mapa_crescimento_demografico.html"

MAP_CENTER = [-30.03, -51.22]
MAP_ZOOM   = 7

ANOS = list(range(2000, 2025))  # 2000..2024

JS_PATH = Path(__file__).with_name("Sparkline.js")


# ── 1. Carregar e preparar dados ───────────────────────────────────────────────

def carregar_dados(path: str) -> pd.DataFrame:
    """Lê o JSON de demografia e retorna DataFrame limpo."""
    with open(path, encoding="utf-8") as f:
        df = pd.read_json(f)

    df["ibge"] = df["ibge"].astype(str).str.zfill(7)

    for ano in ANOS:
        col = f"Demografia Total {ano} (-)"
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(".", "", regex=False)
                .astype(float)
            )

    df = df.rename(columns={
        f"Demografia Total {ano} (-)": f"pop_{ano}"
        for ano in ANOS
        if f"Demografia Total {ano} (-)" in df.columns
    })

    df["crescimento"] = (df["pop_2024"] / df["pop_2000"] - 1) * 100
    return df


def carregar_malha(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── 2. Enriquecer GeoJSON com dados demográficos ───────────────────────────────

def enriquecer_geojson(malha: dict, df: pd.DataFrame) -> tuple[dict, int]:
    """
    Anexa crescimento e série temporal (pop_serie) às propriedades de cada feature.
    """
    lookup = df.set_index("ibge").to_dict("index")
    sem_match = 0

    for feature in malha["features"]:
        cod = feature["properties"].get("codarea", "")
        row = lookup.get(cod)

        if row:
            pop_serie = [
                int(row[f"pop_{ano}"])
                for ano in ANOS
                if f"pop_{ano}" in row and row[f"pop_{ano}"] == row[f"pop_{ano}"]
            ]
            feature["properties"].update({
                "Município":    row["Município"],
                "crescimento":  round(row["crescimento"], 2),
                "pop_2000":     int(row["pop_2000"]),
                "pop_2024":     int(row["pop_2024"]),
                "cresc_fmt":    f"{row['crescimento']:+.2f}%",
                "pop_2024_fmt": f"{int(row['pop_2024']):,}".replace(",", "."),
                "pop_2000_fmt": f"{int(row['pop_2000']):,}".replace(",", "."),
                "pop_serie":    pop_serie,
                "tem_dados":    True,
            })
        else:
            feature["properties"]["tem_dados"] = False
            sem_match += 1

    return malha, sem_match


# ── 3. Construir escala de cores divergente ────────────────────────────────────

def criar_colormap(df: pd.DataFrame) -> cm.LinearColormap:
    vmin = df["crescimento"].min()
    vmax = df["crescimento"].max()
    return cm.LinearColormap(
        colors=["#d73027", "#fee08b", "#1a9850"],
        index=[vmin, 0, vmax],
        vmin=vmin,
        vmax=vmax,
        caption="Crescimento Demográfico 2000–2024 (%)",
    )


# ── 4. MacroElement: tooltip com sparkline ────────────────────────────────────

class SparklineTooltip(MacroElement):
    """
    Injeta o conteúdo de sparkline_tooltip.js no HTML final do Folium,
    substituindo os placeholders __GEOJSON_VAR__ e __ANOS__ pelos valores
    concretos do layer e do intervalo de anos.
    """

    _template = Template("""
    {% macro script(this, kwargs) %}
    {{ this.js_code }}
    {% endmacro %}
    """)

    def __init__(self, geojson_varname: str, anos: list[int], js_path: Path = JS_PATH):
        super().__init__()
        self._name = "Sparkline"

        raw = js_path.read_text(encoding="utf-8")
        self.js_code = (
            raw
            .replace("__GEOJSON_VAR__", geojson_varname)
            .replace("__ANOS__",        json.dumps(anos))
        )


# ── 5. Montar o mapa ───────────────────────────────────────────────────────────

def construir_mapa(malha: dict, colormap: cm.LinearColormap) -> folium.Map:
    m = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM, tiles="CartoDB positron")

    def estilo(feature):
        props = feature["properties"]
        cor = colormap(props["crescimento"]) if props.get("tem_dados") else "#cccccc"
        return {"fillColor": cor, "color": "#555555", "weight": 0.4, "fillOpacity": 0.75}

    def highlight(feature):
        return {"weight": 2, "color": "#333333", "fillOpacity": 0.9}

    gj = folium.GeoJson(malha, style_function=estilo, highlight_function=highlight)
    gj.add_to(m)

    SparklineTooltip(geojson_varname=gj.get_name(), anos=ANOS).add_to(m)
    colormap.add_to(m)
    return m


# ── 6. Execução principal ──────────────────────────────────────────────────────

def main():
    print("Carregando dados...")
    df    = carregar_dados(DATA_PATH)
    malha = carregar_malha(MALHA_PATH)

    print(f"  {len(df)} municípios | crescimento: "
          f"{df['crescimento'].min():.1f}% a {df['crescimento'].max():.1f}%")

    malha, sem_match = enriquecer_geojson(malha, df)
    if sem_match:
        print(f"  ⚠️  {sem_match} features no GeoJSON sem correspondência no CSV")

    colormap = criar_colormap(df)
    mapa     = construir_mapa(malha, colormap)

    mapa.save(OUTPUT)
    print(f"Mapa salvo em '{OUTPUT}' ✓")


if __name__ == "__main__":
    main()
