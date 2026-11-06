// Funções de mapa usadas pela página inicial e pela plataforma.
window.CityShield = (function () {
  var PILOTO = { centro: [-47.4472, -23.4702], raioM: 800 };
  var COR_GEO = '#6CB6FF';
  var COR_VERDE = '#3DD598';

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
      style: 'https://tiles.openfreemap.org/styles/dark',
      center: opts.center || [-47.46, -23.48],
      zoom: opts.zoom || 11.5,
      cooperativeGestures: !opts.interativo,
      attributionControl: { compact: true }
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

    map.on('load', function () {
      map.addSource('piloto', { type: 'geojson', data: circulo(PILOTO.centro, PILOTO.raioM) });
      map.addLayer({ id: 'piloto-fundo', type: 'fill', source: 'piloto', paint: { 'fill-color': COR_VERDE, 'fill-opacity': 0.08 } });
      map.addLayer({ id: 'piloto-borda', type: 'line', source: 'piloto', paint: { 'line-color': COR_VERDE, 'line-width': 1.5, 'line-dasharray': [3, 2] } });

      map.addSource('ruas', { type: 'geojson', data: opts.dados || 'dados/ruas.geojson' });
      map.addLayer({
        id: 'ruas-halo', type: 'circle', source: 'ruas',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['sqrt', ['get', 'registros']], 1, 8, 4.8, 26],
          'circle-color': COR_GEO, 'circle-opacity': 0.12, 'circle-blur': 0.6
        }
      });
      map.addLayer({
        id: 'ruas', type: 'circle', source: 'ruas',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['sqrt', ['get', 'registros']], 1, 3.5, 4.8, 12],
          'circle-color': COR_GEO, 'circle-opacity': 0.85,
          'circle-stroke-color': '#070E1A', 'circle-stroke-width': 1.5
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

  return { criarMapa: criarMapa, abrirPopup: abrirPopup, PILOTO: PILOTO };
})();
