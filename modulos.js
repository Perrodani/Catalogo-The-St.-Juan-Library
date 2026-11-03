function normalizarTexto(txt) {
  return (txt || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

function formatearDuracion(segundos) {
  if (!segundos || isNaN(segundos)) return '';
  var hrs = Math.floor(segundos / 3600);
  var min = Math.floor((segundos % 3600) / 60);
  if (hrs > 0) return hrs + ' h ' + (min > 0 ? min + ' min' : '');
  return min + ' min';
}

function formatearDuracionTotal(segundos) {
  if (!segundos || isNaN(segundos)) return '';
  var dias = Math.floor(segundos / 86400);
  var horas = Math.floor((segundos % 86400) / 3600);
  if (dias > 0) return dias + ' días y ' + horas + ' horas';
  return horas + ' horas';
}

function poblarSagas() {
  var sel = document.getElementById('sagaSel');
  if (!sel || typeof DATOS_AUDIOLIBROS === 'undefined') return;
  var sagas = new Set();
  for (var i = 0; i < DATOS_AUDIOLIBROS.length; i++) {
    var s = (DATOS_AUDIOLIBROS[i].series || '').trim();
    if (s && s.toLowerCase() !== 'independiente') sagas.add(s);
  }
  var actual = sel.value;
  sel.innerHTML = '<option value="">Todas las sagas</option>';
  var arr = Array.from(sagas).sort(function(a, b) { return a.localeCompare(b); });
  for (var j = 0; j < arr.length; j++) {
    var opt = document.createElement('option');
    opt.value = arr[j];
    opt.textContent = arr[j];
    sel.appendChild(opt);
  }
  if (actual) sel.value = actual;
}

window.abrirModalLibro = function(index) {
  if (typeof DATOS_AUDIOLIBROS === 'undefined' || !DATOS_AUDIOLIBROS[index]) return;
  var libro = DATOS_AUDIOLIBROS[index];
  
  var overlay = document.getElementById('modalOverlay');
  var mTitle = document.getElementById('modalTitle');
  var mAuthor = document.getElementById('modalAuthor');
  var mSeries = document.getElementById('modalSeries');
  var mSummary = document.getElementById('modalSummary');
  var mTags = document.getElementById('modalTags');
  var mAward = document.getElementById('modalAward');
  
  if (mTitle) mTitle.textContent = libro.title || 'Sin título';
  if (mAuthor) mAuthor.textContent = libro.author || 'Autor desconocido';
  if (mSeries) {
    mSeries.textContent = libro.series ? 'Saga: ' + libro.series : '';
    mSeries.style.display = libro.series ? 'block' : 'none';
  }
  if (mSummary) {
    mSummary.textContent = libro.summary || libro.description || 'Sin descripción disponible.';
  }
  if (mAward) {
    mAward.textContent = libro.award || '';
    mAward.style.display = libro.award ? 'block' : 'none';
  }
  if (mTags) {
    mTags.innerHTML = '';
    var generos = libro.genres || [];
    if (typeof generos === 'string') generos = [generos];
    for (var g = 0; g < generos.length; g++) {
      var tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = generos[g];
      mTags.appendChild(tag);
    }
  }

  if (overlay) {
    overlay.style.display = 'flex';
    overlay.classList.add('active');
  }
};

window.cerrarModal = function() {
  var overlay = document.getElementById('modalOverlay');
  if (overlay) {
    overlay.style.display = 'none';
    overlay.classList.remove('active');
  }
};

function renderizarCatalogo() {
  var grid = document.getElementById('audiobookGrid') || document.querySelector('.grid');
  var stats = document.getElementById('stats');
  
  if (typeof DATOS_AUDIOLIBROS === 'undefined' || !DATOS_AUDIOLIBROS.length) {
    if (stats) stats.textContent = 'Cargando biblioteca...';
    return;
  }

  var inputBusqueda = document.getElementById('searchInput');
  var selSaga = document.getElementById('sagaSel');
  
  var q = inputBusqueda ? normalizarTexto(inputBusqueda.value) : '';
  var sagaFiltro = selSaga ? selSaga.value : '';

  var duracionTotal = 0;
  var filtrados = [];
  
  for (var idx = 0; idx < DATOS_AUDIOLIBROS.length; idx++) {
    var b = DATOS_AUDIOLIBROS[idx];
    if (b.duration) duracionTotal += b.duration;
    var t = normalizarTexto(b.title);
    var a = normalizarTexto(b.author);
    var s = (b.series || '').trim();
    
    var coincideTexto = !q || t.indexOf(q) !== -1 || a.indexOf(q) !== -1;
    var coincideSaga = !sagaFiltro || s === sagaFiltro;
    
    if (coincideTexto && coincideSaga) {
      filtrados.push({ libro: b, originalIndex: idx });
    }
  }

  if (stats) {
    var tiempoStr = formatearDuracionTotal(duracionTotal);
    stats.textContent = filtrados.length + ' de ' + DATOS_AUDIOLIBROS.length + ' audiolibros' + (tiempoStr ? ' • ' + tiempoStr : '');
  }

  if (!grid) return;

  var html = '';
  for (var i = 0; i < filtrados.length; i++) {
    var item = filtrados[i];
    var libro = item.libro;
    var origIdx = item.originalIndex;
    var portada = libro.cover || 'covers/default.jpg';
    var dur = libro.duration ? formatearDuracion(libro.duration) : '';
    
    html += '<div class="card" onclick="abrirModalLibro(' + origIdx + ')">';
    html += '  <div class="cover-wrapper">';
    html += '    <img src="' + portada + '" alt="' + (libro.title || '') + '" onerror="this.parentElement.innerHTML=\'<div class=\\\'placeholder-cover\\\'><span>🎧</span><div>Sin portada</div></div>\'" loading="lazy">';
    html += '  </div>';
    html += '  <div class="card-body">';
    html += '    <div class="title" style="font-weight: 600; font-size: 1rem; margin-bottom: 6px; line-height: 1.3;" title="' + (libro.title || '') + '">' + (libro.title || 'Sin título') + '</div>';
    html += '    <div class="author" style="color: var(--text-muted, #94a3b8); font-size: 0.85rem; margin-bottom: 4px;">' + (libro.author || 'Autor desconocido') + '</div>';
    if (libro.series) {
      html += '    <div class="series" style="color: #fbbf24; font-size: 0.8rem; margin-top: 2px;">' + libro.series + '</div>';
    }
    if (dur) {
      html += '    <div style="color: var(--text-muted, #64748b); font-size: 0.75rem; margin-top: 6px;">⏱ ' + dur + '</div>';
    }
    html += '  </div>';
    html += '</div>';
  }

  if (filtrados.length === 0) {
    html = '<div style="grid-column: 1/-1; padding: 40px; text-align: center; color: var(--text-muted, #888);">No se encontraron audiolibros.</div>';
  }

  grid.innerHTML = html;
}

window.filtrarCatalogo = renderizarCatalogo;

function inicializarTodo() {
  poblarSagas();
  renderizarCatalogo();
  
  var sea = document.getElementById('searchInput');
  if (sea && !sea.dataset.escuchando) {
    sea.addEventListener('input', renderizarCatalogo);
    sea.dataset.escuchando = 'true';
  }
  
  var sel = document.getElementById('sagaSel');
  if (sel && !sel.dataset.escuchando) {
    sel.addEventListener('change', renderizarCatalogo);
    sel.dataset.escuchando = 'true';
  }

  var btnCerrar = document.getElementById('modalClose');
  if (btnCerrar) {
    btnCerrar.onclick = window.cerrarModal;
  }
  
  var overlay = document.getElementById('modalOverlay');
  if (overlay) {
    overlay.onclick = function(e) {
      if (e.target === overlay) window.cerrarModal();
    };
  }
}

window.addEventListener('DOMContentLoaded', inicializarTodo);
setTimeout(inicializarTodo, 150);
setTimeout(inicializarTodo, 800);