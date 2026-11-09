'use strict';

let chatEnCurso = false;
let fichaActual = null;
const contenedoresChat = ['chat-messages', 'widget-messages'];
const TIEMPO_MINIMO_PENSANDO = 3000;

// Se conserva para integraciones existentes. Los mensajes usan textContent.
function escapeHTML(str) {
  if (str === null || str === undefined) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function nodo(tag, clase, texto) {
  const elemento = document.createElement(tag);
  if (clase) elemento.className = clase;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

function actualizarEnvioChat(ocupado) {
  chatEnCurso = ocupado;
  ['chat-submit-btn', 'widget-submit-btn'].forEach(id => { document.getElementById(id).disabled = ocupado; });
  document.querySelectorAll('[data-opcion-chat]').forEach(boton => { boton.disabled = ocupado; });
}

function agregarContenido(burbuja, texto) {
  let lista = null;
  let parrafo = [];
  const cerrarParrafo = () => { if (parrafo.length) { burbuja.appendChild(nodo('p', '', parrafo.join('\n'))); parrafo = []; } };
  for (const linea of String(texto).split('\n')) {
    if (/^\s*(?:-|\d+\.)\s+/.test(linea)) {
      cerrarParrafo();
      if (!lista) { lista = nodo(/^\s*\d+\./.test(linea) ? 'ol' : 'ul'); burbuja.appendChild(lista); }
      lista.appendChild(nodo('li', '', linea.replace(/^\s*(?:-|\d+\.)\s+/, '')));
    } else {
      lista = null;
      if (!linea.trim()) cerrarParrafo(); else parrafo.push(linea);
    }
  }
  cerrarParrafo();
}

function renderizarMensaje(texto, usuario, containerId, opciones = []) {
  const container = document.getElementById(containerId);
  const mensaje = nodo('div', usuario ? 'mensaje mensaje-usuario' : 'mensaje mensaje-bot');
  mensaje.appendChild(nodo('span', 'mensaje-avatar', usuario ? 'Tú' : 'L'));
  const contenido = nodo('div', 'mensaje-contenido');
  const burbuja = nodo('div', 'mensaje-burbuja');
  agregarContenido(burbuja, texto);
  contenido.appendChild(burbuja);
  contenido.appendChild(nodo('time', 'mensaje-hora', new Intl.DateTimeFormat('es-PE', {hour: '2-digit', minute: '2-digit', timeZone: 'America/Lima'}).format(new Date())));
  if (Array.isArray(opciones) && opciones.length) {
    const grupo = nodo('div', 'opciones-seguimiento');
    opciones.forEach(opcion => {
      const boton = nodo('button', 'opcion-chat', opcion.texto);
      boton.type = 'button';
      boton.dataset.opcionChat = 'true';
      boton.addEventListener('click', () => enviarMensaje(String(opcion.valor || ''), containerId));
      grupo.appendChild(boton);
    });
    contenido.appendChild(grupo);
  }
  mensaje.appendChild(contenido);
  container.appendChild(mensaje);
  container.scrollTop = container.scrollHeight;
}

function mensajeCompartido(texto, usuario, opciones = []) {
  contenedoresChat.forEach(id => renderizarMensaje(texto, usuario, id, opciones));
}

function appendUserMessage(texto) { mensajeCompartido(texto, true); }
function appendBotMessage(texto) { mensajeCompartido(texto, false); }

function actualizarFicha(datos) {
  const tramite = datos.datosTramite || datos;
  if (!tramite.id_tramite || !tramite.nombre) return;
  if (!fichaActual || fichaActual.id_tramite !== tramite.id_tramite) fichaActual = {id_tramite: tramite.id_tramite};
  fichaActual.nombre = tramite.nombre;
  if (tramite.costo) fichaActual.costo = tramite.costo;
  if (tramite.plazo) fichaActual.plazo = tramite.plazo;
  document.getElementById('tramite-actual').classList.remove('oculto');
  const nombre = document.getElementById('tramite-actual-nombre');
  nombre.textContent = fichaActual.nombre;
  nombre.title = fichaActual.nombre;
  document.getElementById('tramite-actual-costo').textContent = fichaActual.costo || 'Puedes preguntárselo a Leonardito';
  document.getElementById('tramite-actual-plazo').textContent = fichaActual.plazo || 'Puedes preguntárselo a Leonardito';
}

function showTyping(show) { document.getElementById('typing-indicator').classList.toggle('oculto', !show); }
function showWidgetTyping(show) { document.getElementById('widget-typing-indicator').classList.toggle('oculto', !show); }

async function enviarMensaje(texto, origen = 'chat-messages') {
  texto = texto.trim();
  if (!texto || chatEnCurso) return;
  actualizarEnvioChat(true);
  document.querySelectorAll('[data-opcion-chat]').forEach(boton => boton.remove());
  mensajeCompartido(texto, true);
  showTyping(true);
  showWidgetTyping(true);
  // El servicio consulta de inmediato; la animación comparte esos tres segundos.
  const esperaMinima = new Promise(resolve => setTimeout(resolve, TIEMPO_MINIMO_PENSANDO));
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const respuesta = await fetch('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mensaje: texto}), signal: controller.signal});
    const datos = await respuesta.json().catch(() => ({}));
    await esperaMinima;
    if (!respuesta.ok) {
      mensajeCompartido(datos.mensaje || 'No pude consultar el servicio en este momento. Inténtalo de nuevo en un momento.', false);
      return;
    }
    mensajeCompartido(datos.mensaje || '¿Me cuentas un poco más de lo que necesitas?', false, datos.opciones || []);
    if (datos.status === 'success') actualizarFicha(datos);
    if (['reiniciar_contexto', 'consulta_no_registrada'].includes(datos.intent) || datos.status === 'despedida') {
      fichaActual = null;
      document.getElementById('tramite-actual').classList.add('oculto');
    }
  } catch (error) {
    await esperaMinima;
    mensajeCompartido(error.name === 'AbortError' ? 'La consulta está tardando más de lo esperado. Puedes volver a intentarlo.' : 'Parece que se interrumpió la conexión. Revisa tu conexión e inténtalo nuevamente.', false);
  } finally {
    clearTimeout(timeout);
    showTyping(false);
    showWidgetTyping(false);
    actualizarEnvioChat(false);
    const input = document.getElementById(origen === 'widget-messages' ? 'widget-input' : 'chat-input');
    input.focus({preventScroll: true});
  }
}

function enviarFormulario(evento, flotante) {
  evento.preventDefault();
  const input = document.getElementById(flotante ? 'widget-input' : 'chat-input');
  if (chatEnCurso || !input.value.trim()) return;
  const texto = input.value;
  input.value = '';
  input.style.height = '';
  enviarMensaje(texto, flotante ? 'widget-messages' : 'chat-messages');
}

function handleChatSubmit(evento) { enviarFormulario(evento, false); }
function handleWidgetSubmit(evento) { enviarFormulario(evento, true); }
function enviarConsultaSugerida(texto) { document.getElementById('orientacion').scrollIntoView({behavior: 'smooth'}); enviarMensaje(texto); }

function toggleChatFlotante() {
  const widget = document.getElementById('widget-flotante');
  const abierto = widget.classList.contains('oculto');
  widget.classList.toggle('oculto', !abierto);
  document.getElementById('chat-messages').setAttribute('aria-live', abierto ? 'off' : 'polite');
  document.getElementById('widget-messages').setAttribute('aria-live', abierto ? 'polite' : 'off');
  document.getElementById('abrir-widget').setAttribute('aria-expanded', String(abierto));
  if (abierto) {
    const mensajes = document.getElementById('widget-messages');
    mensajes.scrollTop = mensajes.scrollHeight;
    document.getElementById('widget-input').focus({preventScroll: true});
  } else document.getElementById('abrir-widget').focus({preventScroll: true});
}

document.addEventListener('DOMContentLoaded', () => {
  contenedoresChat.forEach(id => document.getElementById(id).appendChild(nodo('div', 'separador-dia', 'HOY')));
  mensajeCompartido('¡Hola! Soy Leonardito. Cuéntame qué necesitas hacer en la municipalidad y te voy orientando, paso a paso.', false);
  document.getElementById('chat-form').addEventListener('submit', handleChatSubmit);
  document.getElementById('widget-form').addEventListener('submit', handleWidgetSubmit);
  document.getElementById('abrir-widget').addEventListener('click', toggleChatFlotante);
  document.getElementById('cerrar-widget').addEventListener('click', toggleChatFlotante);
  ['chat-input', 'widget-input'].forEach(id => {
    const input = document.getElementById(id);
    input.addEventListener('input', () => { input.style.height = ''; input.style.height = Math.min(130, input.scrollHeight) + 'px'; });
    input.addEventListener('keydown', evento => {
      if (evento.key === 'Enter' && !evento.shiftKey && !evento.isComposing) enviarFormulario(evento, id === 'widget-input');
    });
  });
  document.addEventListener('keydown', evento => {
    if (evento.key === 'Escape' && !document.getElementById('widget-flotante').classList.contains('oculto')) toggleChatFlotante();
  });
});
