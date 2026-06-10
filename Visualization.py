"""
Mapa de Crescimento Demográfico — Rio Grande do Sul (2000–2024)
Fonte: RIPSA/IBGE
"""

import json
import folium
import pandas as pd
import branca.colormap as cm
from   branca.element import Element


# ── Configurações ──────────────────────────────────────────────────────────────

DATA_PATH  = "datas/demografia_RS.json"
MALHA_PATH = "datas/malha_rs.json"
OUTPUT     = "mapa_crescimento_demografico.html"

MAP_CENTER = [-30.03, -51.22]
MAP_ZOOM   = 7


# ── 1. Carregar e preparar dados ───────────────────────────────────────────────

def carregar_dados(path: str) -> pd.DataFrame:
    """Lê o JSON de demografia e retorna DataFrame limpo."""
    with open(path, encoding="utf-8") as f:
        df = pd.read_json(f)

    # Garante IBGE como string de 7 dígitos
    df["ibge"] = df["ibge"].astype(str).str.zfill(7)

    # Converte populações (formato BR: ponto como separador de milhar)
    for col in ["Demografia Total 2000 (-)", "Demografia Total 2024 (-)"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(".", "", regex=False)
            .astype(float)
        )

    df = df.rename(columns={
        "Demografia Total 2000 (-)": "pop_2000",
        "Demografia Total 2024 (-)": "pop_2024",
    })

    # Crescimento percentual 2000–2024
    df["crescimento"] = (df["pop_2024"] / df["pop_2000"] - 1) * 100

    return df


def carregar_malha(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── 2. Enriquecer GeoJSON com dados demográficos ───────────────────────────────

def enriquecer_geojson(malha: dict, df: pd.DataFrame) -> tuple[dict, int]:
    """
    Anexa dados de crescimento às propriedades de cada feature.
    Retorna a malha enriquecida e a contagem de municípios sem match.
    """
    lookup = df.set_index("ibge").to_dict("index")
    sem_match = 0
    anos = [str(a) for a in range(2000, 2024)]

    for feature in malha["features"]:
        cod = feature["properties"].get("codarea", "")
        row = lookup.get(cod)

        if row:

            serie = [
                float(str(row[f"Demografia Total {ano} (-)"]).replace(".", ""))
                for ano in anos
            ]

            feature["properties"].update({
                "Município":     row["Município"],
                "crescimento":   round(row["crescimento"], 2),
                "pop_2000":      int(row["pop_2000"]),
                "pop_2024":      int(row["pop_2024"]),
                "cresc_fmt":     f"{row['crescimento']:+.2f}%",
                "pop_2024_fmt":  f"{int(row['pop_2024']):,}".replace(",", "."),
                "pop_2000_fmt":  f"{int(row['pop_2000']):,}".replace(",", "."),
                "serie_demo":    ",".join(map(str, serie)),
                "tem_dados":     True,
            })
            
            feature["properties"]["tooltip_html"] = f"""
                    <b>{row['Município']}</b><br>
                    Crescimento: {row['crescimento']:+.2f}%<br>
                    Pop. 2000: {int(row['pop_2000']):,}<br>
                    Pop. 2024: {int(row['pop_2024']):,}<br>
                    <br>
                    <div
                        class="sparkline"
                        data-values="{feature['properties']['serie_demografica']}"
                        style="width:220px;height:50px">
                    </div>
                    """
        else:
            feature["properties"]["tem_dados"] = False
            sem_match += 1

    return malha, sem_match


# ── 3. Construir escala de cores divergente ────────────────────────────────────

def criar_colormap(df: pd.DataFrame) -> cm.LinearColormap:
    """
    Escala divergente centrada em 0%:
      vermelho  → crescimento negativo
      amarelo   → estável (~0%)
      verde     → crescimento positivo
    """
    vmin = df["crescimento"].min()
    vmax = df["crescimento"].max()

    # Normaliza o ponto médio (0%) na escala
    total = vmax - vmin
    mid   = (0 - vmin) / total if total > 0 else 0.5

    colormap = cm.LinearColormap(
        colors=["#d73027", "#fee08b", "#1a9850"],  # vermelho → amarelo → verde
        index=[vmin, 0, vmax],
        vmin=vmin,
        vmax=vmax,
        caption="Crescimento Demográfico 2000–2024 (%)",
    )
    return colormap


# ── 4. Montar o mapa ───────────────────────────────────────────────────────────

def construir_mapa(malha: dict, colormap: cm.LinearColormap) -> folium.Map:
    m = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM, tiles="CartoDB positron")

    spark_js = """
    <script>

    function drawSparkline(el){

        const values =
            el.dataset.values.split(',').map(Number);

        const w = 220;
        const h = 50;
        const pad = 4;

        const min = Math.min(...values);
        const max = Math.max(...values);

        let pts = "";

        values.forEach((v,i)=>{

            const x =
                pad +
                i*(w-2*pad)/(values.length-1);

            const y =
                h-pad -
                ((v-min)/(max-min || 1))*(h-2*pad);

            pts += x + "," + y + " ";
        });

        el.innerHTML =
            `<svg width="${w}" height="${h}">
                <polyline
                    points="${pts}"
                    fill="none"
                    stroke="#1a9850"
                    stroke-width="2"/>
            </svg>`;
    }

    document.addEventListener("mouseover", () => {

        document
            .querySelectorAll(".sparkline")
            .forEach(el => {

                if(!el.dataset.rendered){

                    drawSparkline(el);

                    el.dataset.rendered = "1";
                }
            });
    });

    </script>
    """

    m.get_root().html.add_child(
        Element(spark_js)
    )

    def estilo(feature):
        props = feature["properties"]
        if props.get("tem_dados"):
            cor = colormap(props["crescimento"])
        else:
            cor = "#cccccc"
        return {
            "fillColor":   cor,
            "color":       "#555555",
            "weight":      0.4,
            "fillOpacity": 0.75,
        }

    def highlight(feature):
        return {"weight": 2, "color": "#333333", "fillOpacity": 0.9}

    folium.GeoJson(
        malha,
        style_function=estilo,
        highlight_function=highlight,
        tooltip=folium.GeoJsonTooltip(
                fields=["tooltip_html"],
                aliases=[""],
                labels=False,
                sticky=True
            )
    ).add_to(m)

    colormap.add_to(m)
    return m


# ── 5. Execução principal ──────────────────────────────────────────────────────

def main():
    print("Carregando dados...")
    df    = carregar_dados(DATA_PATH)
    malha = carregar_malha(MALHA_PATH)

    print(f"  {len(df)} municípios no CSV | crescimento: "
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
