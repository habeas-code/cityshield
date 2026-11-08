# web/

Saída do pipeline: `web/public/dados/` recebe as camadas geradas por `python -m pipeline`.

O site **não fica aqui**: ele está em `docs/` (HTML, CSS e JavaScript puros), publicado pelo GitHub Pages. A ideia inicial de um app React + Vite foi cancelada; o porquê está em [D14](../docs/decisoes.md#d14-site-em-html-css-e-javascript-puros-sem-react).

As cópias que o site lê ficam em `docs/dados/` (o GitHub Pages só publica a pasta `docs/`).
