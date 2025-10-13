(function (w) {
  if (w.imgFallback) return; // evita redefinição
  function svgData(wd, ht, text) {
    const size = Math.max(16, Math.round((Math.min(wd, ht) || 300) * 0.12));
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${wd||300}" height="${ht||300}">
      <rect width="100%" height="100%" fill="#f0f0f0"/>
      <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
            font-family="Arial, sans-serif" font-size="${size}" fill="#666">${text||'Sem Imagem'}</text>
    </svg>`;
    return 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg);
  }
  w.imgFallback = function (el, wpx, hpx, text) {
    try {
      if (!el) return;
      el.onerror = null;                 // evita loop
      el.src = svgData(wpx||800, hpx||800, text||'Sem Imagem');
      el.alt = el.alt || (text||'Sem Imagem');
    } catch (_) { /* noop */ }
  };
})(window);