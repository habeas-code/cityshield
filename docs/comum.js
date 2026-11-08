// Funções de mapa usadas pela página inicial e pela plataforma.
window.CityShield = (function () {
  var PILOTO = { centro: [-47.4472, -23.4702], raioM: 800 };
  var COR_GEO = '#6CB6FF';
  var COR_VERDE = '#3DD598';
  var COR_ALAG = '#4C8FE8';   // mais alagamentos (água da chuva acumulada na rua)
  var COR_INUND = '#D9772A';  // mais inundações (rio ou córrego que transbordou)

  // Polígono aproximado de um círculo (raio em metros) para desenhar a área-piloto.
  function circulo(centro, raioM, passos) {
    passos = passos || 72;
    var lon = centro[0], lat = centro[1], pts = [];
    var dLat = raioM / 111320;
    var dLon = raioM / (111320 * Math.cos(lat * Math.PI / 180));
    for (var i = 0; i <= passos; i++) {
      var a = (i / passos) * 2 * Math.PI;
      pts.push([lon + dLon * Math.cos(a), lat + dLat * Math.sin(a)]);
    }
    return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [pts] } };
  }

  function texto(rua, registros, relatorios) {
    var div = document.createElement('div');
    div.className = 'pop';
    var b = document.createElement('b'); b.textContent = rua;
    var s = document.createElement('span');
    s.textContent = registros + (registros == 1 ? ' registro' : ' registros') + ' · ' + relatorios + ' de 15 relatórios';
    div.appendChild(b); div.appendChild(s);
    return div;
  }

  function criarMapa(id, opts) {
    opts = opts || {};
    var el = document.getElementById(id);
    if (!window.maplibregl) { el.textContent = 'Não foi possível carregar o mapa.'; return null; }

    var map = new maplibregl.Map({
      container: id,
      style: opts.estilo || ('https://tiles.openfreemap.org/styles/' + (opts.claro ? 'positron' : 'dark')),
      center: opts.center || [-47.46, -23.48],
      zoom: opts.zoom || 11.5,
      cooperativeGestures: !opts.interativo,
      pitch: opts.pitch || 0,
      bearing: opts.bearing || 0,
      maxPitch: 70,
      attributionControl: { compact: true }
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), opts.posControles || 'top-right');
    if (opts.escala) map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), opts.posControles || 'top-right');

    map.on('load', function () {
      // Créditos começam fechados (só o botão ⓘ); abrem ao clicar.
      function fecharCreditos() {
        var cred = map.getContainer().querySelector('.maplibregl-ctrl-attrib');
        if (cred) { cred.classList.remove('maplibregl-compact-show'); cred.removeAttribute('open'); }
      }
      fecharCreditos();
      map.once('idle', fecharCreditos);
      // No mapa escuro: troca o preto por azul-marinho e destaca rios e represas.
      if (!opts.claro && !opts.estilo) map.getStyle().layers.forEach(function (l) {
        try {
          if (l.type === 'background') map.setPaintProperty(l.id, 'background-color', '#0B1A2E');
          else if (l.type === 'fill' && /water/.test(l.id)) map.setPaintProperty(l.id, 'fill-color', '#123A63');
          else if (l.type === 'line' && /waterway/.test(l.id)) map.setPaintProperty(l.id, 'line-color', '#1F5A92');
          else if (l.type === 'fill' && /landuse|landcover|park/.test(l.id)) map.setPaintProperty(l.id, 'fill-color', '#10233A');
        } catch (e) { /* camada sem essa propriedade: ignora */ }
      });

      // Prédios em 3D (altura do OpenStreetMap; 6 m quando não informada)
      if (opts.tresD) {
        var primeiroRotulo = (map.getStyle().layers.filter(function (l) { return l.type === 'symbol'; })[0] || {}).id;
        map.addLayer({
          id: 'predios-3d', type: 'fill-extrusion', source: 'openmaptiles', 'source-layer': 'building', minzoom: 13,
          paint: {
            'fill-extrusion-color': ['interpolate', ['linear'], ['coalesce', ['get', 'render_height'], 6], 0, '#16263D', 40, '#2A4466'],
            'fill-extrusion-height': ['interpolate', ['linear'], ['zoom'], 13, 0, 14.5, ['coalesce', ['get', 'render_height'], 6]],
            'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
            'fill-extrusion-opacity': 0.85
          }
        }, primeiroRotulo);
        if (map.getLayer('building')) map.setLayoutProperty('building', 'visibility', 'none');
      }

      map.addSource('piloto', { type: 'geojson', data: circulo(PILOTO.centro, PILOTO.raioM) });
      map.addLayer({ id: 'piloto-fundo', type: 'fill', source: 'piloto', paint: { 'fill-color': COR_VERDE, 'fill-opacity': 0.08 } });
      map.addLayer({ id: 'piloto-borda', type: 'line', source: 'piloto', paint: { 'line-color': COR_VERDE, 'line-width': 1.5, 'line-dasharray': [3, 2] } });

      var corPonto = opts.corPorTipo
        ? ['case', ['>', ['get', 'inundacoes'], ['get', 'alagamentos']], COR_INUND, COR_ALAG]
        : COR_GEO;
      var verdePiloto = opts.claro ? '#0E8F5B' : COR_VERDE;
      map.setPaintProperty('piloto-fundo', 'fill-color', verdePiloto);
      map.setPaintProperty('piloto-borda', 'line-color', verdePiloto);
      if (opts.claro) { map.setPaintProperty('piloto-fundo', 'fill-opacity', 0.1); map.setPaintProperty('piloto-borda', 'line-width', 2); }

      var rotulo = document.createElement('div');
      rotulo.className = 'rotulo-piloto';
      rotulo.innerHTML = '<b>Área-piloto: Núcleo Norte</b><span>raio de 800 m</span>';
      map._rotuloPiloto = new maplibregl.Marker({ element: rotulo, anchor: 'bottom', offset: [0, -4] })
        .setLngLat([PILOTO.centro[0], PILOTO.centro[1] + PILOTO.raioM / 111320]).addTo(map);

      map.addSource('ruas', { type: 'geojson', data: opts.dados || 'dados/ruas.geojson' });
      if (opts.calor) {
        map.addLayer({
          id: 'calor', type: 'heatmap', source: 'ruas', maxzoom: 15,
          paint: {
            'heatmap-weight': ['interpolate', ['linear'], ['get', 'registros'], 1, 0.25, 23, 1],
            'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 10, 0.8, 14, 1.6],
            'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 10, 18, 14, 40],
            'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 12.5, 0.75, 15, 0],
            'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'],
              0, 'rgba(0,0,0,0)', 0.2, 'rgba(46,92,170,0.35)', 0.45, 'rgba(76,143,232,0.6)', 0.7, 'rgba(140,196,255,0.8)', 1, 'rgba(225,240,255,0.95)']
          }
        });
      }
      map.addLayer({
        id: 'ruas-halo', type: 'circle', source: 'ruas',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['sqrt', ['get', 'registros']], 1, 8, 4.8, 26],
          'circle-color': corPonto, 'circle-opacity': opts.claro ? 0 : 0.12, 'circle-blur': 0.6
        }
      });
      map.addLayer({
        id: 'ruas', type: 'circle', source: 'ruas',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['sqrt', ['get', 'registros']], 1, 3.5, 4.8, 12],
          'circle-color': corPonto, 'circle-opacity': opts.claro ? 0.8 : 0.85,
          'circle-stroke-color': opts.claro ? '#FFFFFF' : '#070E1A', 'circle-stroke-width': 1.5
        }
      });

      map.on('click', 'ruas', function (e) {
        var p = e.features[0].properties;
        abrirPopup(map, e.features[0].geometry.coordinates, p);
      });
      map.on('mouseenter', 'ruas', function () { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', 'ruas', function () { map.getCanvas().style.cursor = ''; });

      if (opts.aoCarregar) opts.aoCarregar(map);
    });
    return map;
  }

  var popupAtual = null;
  function abrirPopup(map, coords, p) {
    if (popupAtual) popupAtual.remove();
    popupAtual = new maplibregl.Popup({ closeButton: false, offset: 10 })
      .setLngLat(coords).setDOMContent(texto(p.rua, p.registros, p.relatorios)).addTo(map);
  }

  return { criarMapa: criarMapa, abrirPopup: abrirPopup, PILOTO: PILOTO, COR_ALAG: COR_ALAG, COR_INUND: COR_INUND };
})();
