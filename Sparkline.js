/**
 * Tooltip com Sparkline SVG — Mapa Demográfico RS
 *
 * Vinculado ao layer GeoJson via MacroElement (Folium).
 * A string "__GEOJSON_VAR__" é substituída em runtime pelo nome
 * da variável JS gerada pelo Folium (ex: geo_json_abc123).
 * O array "__ANOS__" é substituído pela lista de anos do dataset.
 */

(function () {

  // ── Constantes de layout ──────────────────────────────────────────────────
  var W   = 220, H   = 60, PAD = 8;
  var xMin = PAD,  xMax = W - PAD;
  var yMin = PAD,  yMax = H - PAD;

  // ── Escala ────────────────────────────────────────────────────────────────
  function sx(i, n)  { return xMin + (i / (n - 1)) * (xMax - xMin); }
  function sy(v, lo, range) { return yMax - ((v - lo) / range) * (yMax - yMin); }

  // ── Formata valores populacionais (k / M) ─────────────────────────────────
  function fmtK(v) {
    if (v >= 1e6) return (v / 1e6).toFixed(1) + "M";
    if (v >= 1e3) return (v / 1e3).toFixed(0) + "k";
    return String(v);
  }

  // ── Constrói o SVG da sparkline ───────────────────────────────────────────
  function buildSparkline(serie, color) {
    var n     = serie.length;
    var lo    = Math.min.apply(null, serie);
    var hi    = Math.max.apply(null, serie);
    var range = hi - lo || 1;
    var anos  = __ANOS__;

    // Polyline points
    var pts = serie.map(function (v, i) {
      return sx(i, n) + "," + sy(v, lo, range);
    }).join(" ");

    // Área preenchida (fechada na base)
    var areaPts = sx(0, n) + "," + yMax + " " + pts + " " + sx(n - 1, n) + "," + yMax;

    // Linha de referência no nível de pop_2000
    var yRef    = sy(serie[0], lo, range);
    var refLine = (yRef >= yMin && yRef <= yMax)
      ? '<line x1="' + xMin + '" y1="' + yRef + '" x2="' + xMax + '" y2="' + yRef +
        '" stroke="#aaa" stroke-width="0.8" stroke-dasharray="3,2"/>'
      : "";

    // Pontos inicial e final
    var fx = sx(0, n),     fy = sy(serie[0],     lo, range);
    var lx = sx(n - 1, n), ly = sy(serie[n - 1], lo, range);

    // Labels de ano (eixo X)
    var dyLabel = String(H - yMax + 1);
    var anoInicio = anos[0];
    var anoFim    = anos[anos.length - 1];

    return (
      '<svg xmlns="http://www.w3.org/2000/svg" width="' + W + '" height="' + H + '">' +
        '<polygon points="'  + areaPts + '" fill="' + color + '" fill-opacity="0.12"/>' +
        refLine +
        '<polyline points="' + pts + '" fill="none" stroke="' + color +
          '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>' +
        '<circle cx="' + fx + '" cy="' + fy + '" r="3"   fill="' + color + '" fill-opacity="0.6"/>' +
        '<circle cx="' + lx + '" cy="' + ly + '" r="3.5" fill="' + color + '"/>' +
        // Labels eixo Y
        '<text x="' + PAD + '" y="' + (H - 1)   + '" font-size="9" fill="#888">' + fmtK(lo) + '</text>' +
        '<text x="' + PAD + '" y="' + (PAD + 6) + '" font-size="9" fill="#888">' + fmtK(hi) + '</text>' +
        // Labels eixo X
        '<text x="' + xMin + '" y="' + (H - 1) + '" font-size="9" fill="#aaa" text-anchor="start" dy="-' + dyLabel + '">' + anoInicio + '</text>' +
        '<text x="' + xMax + '" y="' + (H - 1) + '" font-size="9" fill="#aaa" text-anchor="end"   dy="-' + dyLabel + '">' + anoFim    + '</text>' +
      '</svg>'
    );
  }

  // ── Constrói o HTML completo do tooltip ───────────────────────────────────
  function buildTooltip(props) {
    var color = props.crescimento >= 0 ? "#1a9850" : "#d73027";
    var svg   = buildSparkline(props.pop_serie, color);

    return (
      '<div style="font-family:sans-serif;font-size:12px;min-width:230px;padding:4px 6px">' +
        '<div style="font-weight:700;font-size:13px;margin-bottom:4px;color:#222">' +
          (props["Município"] || "") +
        "</div>" +
        '<table style="border-collapse:collapse;width:100%;margin-bottom:6px">' +
          "<tr>" +
            '<td style="color:#555;padding:1px 4px 1px 0">Crescimento:</td>' +
            '<td style="font-weight:600;color:' + color + '">' + (props.cresc_fmt    || "") + "</td>" +
          "</tr><tr>" +
            '<td style="color:#555;padding:1px 4px 1px 0">Pop. 2024:</td>' +
            "<td>" + (props.pop_2024_fmt || "") + "</td>" +
          "</tr><tr>" +
            '<td style="color:#555;padding:1px 4px 1px 0">Pop. 2000:</td>' +
            '<td style="color:#888">' + (props.pop_2000_fmt || "") + "</td>" +
          "</tr>" +
        "</table>" +
        '<div style="margin-top:2px">' + svg + "</div>" +
      "</div>"
    );
  }

  // ── Vincula tooltip a cada feature ────────────────────────────────────────
  __GEOJSON_VAR__.eachLayer(function (layer) {
    var props = layer.feature.properties;
    if (!props.tem_dados) return;
    layer.bindTooltip(buildTooltip(props), { sticky: true, opacity: 0.97, maxWidth: 280 });
  });

})();
