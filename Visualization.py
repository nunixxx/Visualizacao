import folium
import pandas as pd
import json
import branca.colormap as cm

# 1. Carregar e limpar dados
with open('datas/demografia_RS.json', 'r', encoding='utf-8') as f:
    df = pd.read_json(f) 

# Conversão de tipos
df['ibge'] = df['ibge'].astype(str).str.zfill(7)
df['pop_2000'] = df['Demografia Total 2000 (-)'].str.replace('.', '', regex=False).astype(float)
df['pop_2024'] = df['Demografia Total 2024 (-)'].str.replace('.', '', regex=False).astype(float)
df['crescimento'] = ((df['pop_2024'] / df['pop_2000']) - 1) * 100

# 2. Carregar a malha (certifique-se que malha_rs.json está na pasta)
with open('datas/malha_rs.json', 'r', encoding='utf-8') as f:
    malha_rs = json.load(f)

# 3. Criar dicionário para busca rápida
data_dict = df.set_index('ibge').to_dict('index')

# 4. Criar o Mapa
m = folium.Map(location=[-30.0346, -51.2177], zoom_start=7)

# Definir escala de cores (Colormap)
min_val = df['crescimento'].min()
max_val = df['crescimento'].max()
colormap = cm.LinearColormap(colors=['red', 'yellow', 'green'], vmin=min_val, vmax=max_val)

# 5. Adicionar camada GeoJson com Tooltip e Cores
for feature in malha_rs['features']:
    cod = feature['properties']['codarea']
    if cod in data_dict:
        row = data_dict[cod]
        feature['properties']['Município'] = row['Município']
        feature['properties']['cresc_format'] = f"{row['crescimento']:.2f}%"
        feature['properties']['pop_format'] = f"{row['pop_2024']:.0f}"
        feature['properties']['cor'] = colormap(row['crescimento'])
    else:
        feature['properties']['cor'] = 'gray'

folium.GeoJson(
    malha_rs,
    style_function=lambda x: {
        'fillColor': x['properties'].get('cor', 'gray'),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['Município', 'cresc_format', 'pop_format'],
        aliases=['Município:', 'Crescimento:', 'População 2024:'],
        localize=True
    )
).add_to(m)

# Adicionar legenda
colormap.caption = 'Crescimento Demográfico (%)'
colormap.add_to(m)

m.save("mapa_crescimento_demografico.html")
print("Mapa final gerado com sucesso!")