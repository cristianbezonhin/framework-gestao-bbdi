// Helpers compartilhados entre paginas.

async function apiGet(url) {
  const r = await fetch(url, { credentials: 'same-origin' });
  if (r.status === 401) { location.href = '/login'; throw new Error('unauthenticated'); }
  if (!r.ok) throw new Error(`GET ${url} -> ${r.status}`);
  return r.json();
}

async function apiSend(method, url, body) {
  const r = await fetch(url, {
    method,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: body == null ? null : JSON.stringify(body),
  });
  if (r.status === 401) { location.href = '/login'; throw new Error('unauthenticated'); }
  if (!r.ok) {
    let detail = '';
    try { detail = (await r.json()).detail || ''; } catch (_) {}
    throw new Error(detail || `${method} ${url} -> ${r.status}`);
  }
  return r.json();
}

const api = {
  get: apiGet,
  post: (url, body) => apiSend('POST', url, body),
  patch: (url, body) => apiSend('PATCH', url, body),
  put: (url, body) => apiSend('PUT', url, body),
  delete: (url) => apiSend('DELETE', url, null),
};

function fmtData(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }); }
  catch { return iso; }
}

function fmtDataCurta(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleDateString('pt-BR'); }
  catch { return iso; }
}

function trimestreAtual() {
  return Math.floor(new Date().getMonth() / 3) + 1;
}

function anoAtual() {
  return new Date().getFullYear();
}

const NIVEL_LABEL = {
  objetivo_anual: 'Objetivo Anual',
  key_result: 'Key Result',
  meta: 'Meta',
  desafio: 'Desafio',
};

const STATUS_LABEL = {
  ativo: 'Ativo', concluido: 'Concluido', em_risco: 'Em risco', cancelado: 'Cancelado',
  nao_iniciado: 'Nao iniciado', em_andamento: 'Em andamento', bloqueado: 'Bloqueado',
  a_fazer: 'A fazer', fazendo: 'Fazendo', revisao: 'Em revisao', feito: 'Feito',
};

function statusBadgeClass(status) {
  if (['concluido', 'feito'].includes(status)) return 'badge badge-ok';
  if (['em_risco', 'bloqueado'].includes(status)) return 'badge badge-err';
  if (['fazendo', 'em_andamento', 'revisao'].includes(status)) return 'badge badge-warn';
  return 'badge badge-neutral';
}

window.api = api;
window.fmtData = fmtData;
window.fmtDataCurta = fmtDataCurta;
window.trimestreAtual = trimestreAtual;
window.anoAtual = anoAtual;
window.NIVEL_LABEL = NIVEL_LABEL;
window.STATUS_LABEL = STATUS_LABEL;
window.statusBadgeClass = statusBadgeClass;
