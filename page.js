'use client';

import { useState, useRef, useEffect } from 'react';

export default function ChatbotMDJLOPage() {
  // 1. Estado del historial de mensajes
  const [mensajes, setMensajes] = useState([
    {
      id: 1,
      rol: 'bot',
      texto: '¡Hola! Soy Leonardito, el asistente virtual de la MDJLO. ¿Sobre qué trámite municipal deseas consultar?',
      datosTramite: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  // Estados auxiliares
  const [inputMensaje, setInputMensaje] = useState('');
  const [estaEscribiendo, setEstaEscribiendo] = useState(false);
  const finDelChatRef = useRef(null);

  // Auto-scroll al recibir o enviar un mensaje
  useEffect(() => {
    finDelChatRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes, estaEscribiendo]);

  // Consultas sugeridas para el usuario
  const sugerencias = [
    'Licencia para abrir una bodega',
    'Requisitos para cambio de giro',
    'Duplicado de licencia municipal',
    'Acceso a la información pública',
  ];

  // 2. Función para enviar mensaje al backend en Flask
  const enviarMensaje = async (textoAEnviar) => {
    const texto = (textoAEnviar || inputMensaje).trim();
    if (!texto || estaEscribiendo) return;

    const horaActual = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Mensaje del usuario
    const mensajeUsuario = {
      id: Date.now(),
      rol: 'usuario',
      texto: texto,
      datosTramite: null,
      timestamp: horaActual,
    };

    setMensajes((prev) => [...prev, mensajeUsuario]);
    setInputMensaje('');
    setEstaEscribiendo(true);

    try {
      const response = await fetch('http://127.0.0.1:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mensaje: texto }),
      });

      const data = await response.json();

      let mensajeBot;
      if (response.ok && data.status === 'success') {
        // Respuesta exitosa con datos estructurados del trámite
        mensajeBot = {
          id: Date.now() + 1,
          rol: 'bot',
          texto: data.mensaje || `Información encontrada para: ${data.nombre}`,
          datosTramite: {
            nombre: data.nombre,
            costo: data.costo,
            plazo: data.plazo,
            requisitos: Array.isArray(data.requisitos) ? data.requisitos : [],
          },
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      } else {
        // Fallback o trámite no encontrado
        mensajeBot = {
          id: Date.now() + 1,
          rol: 'bot',
          texto: data.mensaje || 'No pude encontrar información para tu consulta. Por favor, intenta reformular tu pregunta.',
          datosTramite: null,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      }

      setMensajes((prev) => [...prev, mensajeBot]);
    } catch (error) {
      console.error('Error de conexión con el backend:', error);
      const mensajeError = {
        id: Date.now() + 1,
        rol: 'bot',
        texto: '⚠️ No se pudo conectar con el servidor local de la municipalidad (http://127.0.0.1:5000). Asegúrate de que el script app.py esté corriendo.',
        datosTramite: null,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMensajes((prev) => [...prev, mensajeError]);
    } finally {
      setEstaEscribiendo(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviarMensaje();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f4f6f9] text-gray-800 font-sans">
      
      {/* ------------------------------------------------------------- */}
      {/* 1. BARRA SUPERIOR AMARILLA (SISGEDO Y ACCESOS DIRECTOS)       */}
      {/* ------------------------------------------------------------- */}
      <header className="bg-[#fbc02d] text-[#0d3b66] text-xs font-semibold py-1.5 px-4 sm:px-8 border-b border-yellow-500 shadow-sm">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          {/* Logo / Título SISGEDO */}
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-[#0d3b66]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <span className="font-black text-sm tracking-tight text-[#0a2540]">SISGEDO</span>
              <span className="ml-2 hidden sm:inline font-normal text-[#1e3a5f]">Sistema de Gestión Documentario</span>
            </div>
          </div>

          {/* Enlaces de trámites superiores */}
          <nav className="flex items-center space-x-3 sm:space-x-5 text-xs text-[#0a2540]">
            <span className="hover:underline cursor-pointer">Consulte su Trámite</span>
            <span className="text-yellow-600">|</span>
            <span className="hover:underline cursor-pointer">Mesa de Partes Virtual</span>
            <span className="text-yellow-600">|</span>
            <span className="hover:underline cursor-pointer">Tramifacil</span>
            <span className="text-yellow-600">|</span>
            <span className="hover:underline cursor-pointer">Rendición de Cuentas</span>
          </nav>
        </div>
      </header>

      {/* ------------------------------------------------------------- */}
      {/* 2. ENCABEZADO INSTITUCIONAL BLANCO CON ESCUDO Y LOGOS         */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-white border-b border-gray-200 py-3 px-4 sm:px-8 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-4">
          
          {/* Escudo y Nombre Oficial de la Municipalidad */}
          <div className="flex items-center space-x-4">
            {/* Escudo Distrital Estilizado */}
            <div className="w-14 h-16 sm:w-16 sm:h-20 bg-gradient-to-b from-amber-400 to-red-600 rounded-b-full p-0.5 shadow-md flex items-center justify-center flex-shrink-0">
              <div className="w-full h-full bg-white rounded-b-full flex flex-col items-center justify-center p-1 text-center">
                <span className="text-[7px] font-black text-red-700 leading-tight">MDJLO</span>
                <div className="w-6 h-6 rounded-full bg-blue-900 border border-amber-400 flex items-center justify-center my-0.5">
                  <span className="text-[9px] text-white font-bold">🏛️</span>
                </div>
                <span className="text-[6px] font-semibold text-gray-700 uppercase">Chiclayo</span>
              </div>
            </div>

            {/* Título en tipografía azul con relieve característico */}
            <div>
              <h1 className="text-xl sm:text-3xl font-extrabold text-[#113f8a] tracking-tight leading-tight drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">
                Municipalidad Distrital
              </h1>
              <h2 className="text-xl sm:text-3xl font-extrabold text-[#113f8a] tracking-tight leading-tight">
                de José Leonardo Ortiz
              </h2>
            </div>
          </div>

          {/* Sello de Portal de Transparencia Estándar (PTE) */}
          <div className="flex items-center space-x-2 bg-blue-50/60 border border-blue-200 rounded-lg px-3 py-1.5">
            <div className="text-right">
              <span className="block text-[11px] font-semibold text-[#0284c7] uppercase tracking-wider">Portal de</span>
              <span className="block text-sm font-black text-[#0369a1] leading-none">Transparencia</span>
              <span className="text-[9px] text-gray-500 italic">estándar</span>
            </div>
            <div className="w-8 h-8 rounded-full border-2 border-[#0284c7] flex items-center justify-center text-[#0284c7] font-black text-xs bg-white shadow-inner">
              PTE
            </div>
          </div>

        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 3. BARRA DE NAVEGACIÓN AMARILLA INSTITUCIONAL                  */}
      {/* ------------------------------------------------------------- */}
      <nav className="bg-[#fbc02d] border-b-2 border-yellow-600 px-4 sm:px-8 py-2 text-white font-bold text-xs uppercase tracking-wide shadow">
        <div className="max-w-7xl mx-auto flex items-center space-x-2 sm:space-x-4 overflow-x-auto whitespace-nowrap scrollbar-none">
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">INICIO</span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">DISTRITO</span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">DOCUMENTOS DE GESTIÓN</span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">NORMAS</span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">MANUALES</span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">TRANSPARENCIA</span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">CONVOCATORIAS</span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="text-[#0d3b66] bg-yellow-400/80 px-2 py-0.5 rounded shadow-sm">CHATBOT LEONARDITO</span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">CONTACTO</span>
        </div>
      </nav>

      {/* ------------------------------------------------------------- */}
      {/* 4. CINTA NEGRA: BARRA DE ESTADO / BUSCADOR                     */}
      {/* ------------------------------------------------------------- */}
      <div className="bg-black text-white px-4 sm:px-8 py-1.5 flex items-center justify-between text-xs font-semibold">
        <div className="max-w-7xl mx-auto w-full flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="bg-[#113f8a] text-[10px] px-2 py-0.5 rounded text-yellow-300 font-extrabold uppercase">
              En Línea
            </span>
            <span className="tracking-wide">ATENCIÓN AL VECINO - ASISTENTE VIRTUAL</span>
          </div>
          <div className="flex items-center bg-[#0d3b66] px-2 py-1 rounded text-white text-[11px] gap-1 cursor-pointer hover:bg-blue-800 transition">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="hidden sm:inline">Buscar trámites</span>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 5. ÁREA PRINCIPAL CON LA INTERFAZ DEL CHATBOT                 */}
      {/* ------------------------------------------------------------- */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 flex flex-col">
        
        {/* Título de sección con subrayado amarillo característico (como en imagen 1) */}
        <div className="mb-4">
          <h2 className="text-lg sm:text-xl font-bold text-gray-800 uppercase tracking-tight flex items-center gap-2">
            <span>ASISTENTE VIRTUAL DE TRÁMITES MUNICIPALES</span>
          </h2>
          {/* Línea amarilla de acento bajo el título */}
          <div className="w-48 h-1 bg-[#fbc02d] mt-1 rounded-full"></div>
        </div>

        {/* CONTENEDOR DEL CHAT ESTILO PORTAL */}
        <div className="bg-white rounded-lg border border-gray-300 shadow-md flex-1 flex flex-col overflow-hidden min-h-[520px]">
          
          {/* Cabecera del Chat */}
          <div className="bg-gradient-to-r from-[#113f8a] to-[#1e5bb8] text-white p-3 sm:px-5 sm:py-3 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-full bg-white text-[#113f8a] font-black flex items-center justify-center border-2 border-yellow-400 shadow">
                  🏛️
                </div>
                <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></span>
              </div>
              <div>
                <h3 className="font-bold text-sm sm:text-base leading-tight">Leonardito</h3>
                <p className="text-[11px] text-blue-200">Asistente Municipal Inteligente - MDJLO</p>
              </div>
            </div>

            <span className="text-[11px] bg-blue-900/60 border border-blue-400/40 text-yellow-300 px-2.5 py-1 rounded-full font-medium">
              TUPA 2026
            </span>
          </div>

          {/* Chips de Consultas Sugeridas Rápidas */}
          <div className="bg-[#f8fafc] border-b border-gray-200 px-4 py-2 flex items-center gap-2 overflow-x-auto whitespace-nowrap text-xs">
            <span className="text-gray-500 font-semibold flex-shrink-0">Sugerencias:</span>
            {sugerencias.map((sug, idx) => (
              <button
                key={idx}
                onClick={() => enviarMensaje(sug)}
                disabled={estaEscribiendo}
                className="bg-white hover:bg-yellow-50 text-blue-900 border border-blue-200 hover:border-yellow-400 px-2.5 py-1 rounded-full transition-all text-[11px] shadow-sm flex-shrink-0"
              >
                {sug}
              </button>
            ))}
          </div>

          {/* ÁREA DE MENSAJES CON AUTO-SCROLL */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/70">
            {mensajes.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.rol === 'usuario' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`flex gap-2.5 max-w-[92%] sm:max-w-[80%] ${
                    msg.rol === 'usuario' ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  {/* Avatar circular */}
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs flex-shrink-0 shadow-sm ${
                      msg.rol === 'usuario'
                        ? 'bg-[#113f8a] text-white font-bold'
                        : 'bg-yellow-400 text-blue-950 font-black border border-amber-500'
                    }`}
                  >
                    {msg.rol === 'usuario' ? 'Tú' : '🤖'}
                  </div>

                  {/* Burbuja de chat */}
                  <div
                    className={`rounded-xl px-4 py-3 text-sm shadow-sm leading-relaxed ${
                      msg.rol === 'usuario'
                        ? 'bg-[#113f8a] text-white rounded-tr-none'
                        : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none'
                    }`}
                  >
                    {/* Mensaje de texto principal */}
                    <p className="whitespace-pre-wrap">{msg.texto}</p>

                    {/* TARJETA FORMATEADA DEL TRÁMITE (Estilo Municipal Imagen 2) */}
                    {msg.datosTramite && (
                      <div className="mt-3 pt-3 border-t border-gray-200 space-y-3">
                        
                        {/* Cabecera estilo píldora azul clara con borde lateral grueso (idéntica a NORMAS EMITIDAS) */}
                        <div className="bg-[#f0f7fd] border-l-4 border-[#0284c7] px-3 py-1.5 rounded-r">
                          <span className="text-[10px] text-[#0284c7] uppercase font-bold tracking-wider block">Trámite Oficial</span>
                          <h4 className="text-[#0c4a6e] font-extrabold text-sm sm:text-base leading-snug">
                            {msg.datosTramite.nombre}
                          </h4>
                        </div>

                        {/* Renderizado condicional: Solo se muestra si el backend envía explícitamente el costo o el plazo */}
                        <div className="flex flex-col sm:flex-row gap-2 text-xs mt-2">
                          {msg.datosTramite?.costo && (
                            <div className="flex-1 bg-emerald-50 border border-emerald-200 rounded p-2 flex items-center space-x-2">
                              <span className="text-emerald-700 font-bold text-base">💰</span>
                              <div>
                                <span className="text-gray-500 block text-[10px] uppercase font-semibold">Costo del trámite</span>
                                <span className="font-bold text-emerald-800 text-xs sm:text-sm">
                                  {msg.datosTramite.costo}
                                </span>
                              </div>
                            </div>
                          )}

                          {msg.datosTramite?.plazo && (
                            <div className="flex-1 bg-amber-50 border border-amber-200 rounded p-2 flex items-center space-x-2">
                              <span className="text-amber-700 font-bold text-base">⏱️</span>
                              <div>
                                <span className="text-gray-500 block text-[10px] uppercase font-semibold">Plazo de atención</span>
                                <span className="font-bold text-amber-900 text-xs sm:text-sm">
                                  {msg.datosTramite.plazo}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Lista con viñetas limpias para los requisitos */}
                        {msg.datosTramite.requisitos?.length > 0 && (
                          <div className="mt-2 bg-gray-50 p-3 rounded border border-gray-200">
                            <span className="font-bold text-xs text-gray-700 block mb-2 uppercase tracking-wide">
                              📋 Requisitos requeridos:
                            </span>
                            <ul className="space-y-1.5 pl-1">
                              {msg.datosTramite.requisitos.map((req, i) => (
                                <li key={i} className="flex items-start text-xs text-gray-700 leading-normal">
                                  {/* Viñeta circular azul institucional */}
                                  <span className="w-1.5 h-1.5 rounded-full bg-[#0284c7] mt-1.5 mr-2.5 flex-shrink-0"></span>
                                  <span>{req}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Timestamp */}
                    <span
                      className={`block text-[10px] mt-1 text-right ${
                        msg.rol === 'usuario' ? 'text-blue-200' : 'text-gray-400'
                      }`}
                    >
                      {msg.timestamp}
                    </span>
                  </div>
                </div>
              </div>
            ))}

            {/* Indicador de "Escribiendo..." */}
            {estaEscribiendo && (
              <div className="flex items-start gap-2.5">
                <div className="w-8 h-8 rounded-full bg-yellow-400 text-blue-950 font-black border border-amber-500 flex items-center justify-center text-xs flex-shrink-0">
                  🤖
                </div>
                <div className="bg-white border border-gray-200 rounded-xl rounded-tl-none px-4 py-2.5 text-xs text-gray-600 flex items-center space-x-2 shadow-sm">
                  <span className="font-medium text-[#113f8a]">Leonardito está escribiendo</span>
                  <div className="flex space-x-1">
                    <span className="w-1.5 h-1.5 bg-[#113f8a] rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-[#113f8a] rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-1.5 h-1.5 bg-[#113f8a] rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={finDelChatRef} />
          </div>

          {/* ------------------------------------------------------------- */}
          {/* INPUT Y BOTÓN DE ENVÍO INFERIOR                               */}
          {/* ------------------------------------------------------------- */}
          <footer className="p-3 sm:p-4 bg-white border-t border-gray-200">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                enviarMensaje();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputMensaje}
                onChange={(e) => setInputMensaje(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Escribe tu consulta sobre trámites aquí... (ej. ¿cuánto cuesta la licencia de bodega?)"
                disabled={estaEscribiendo}
                className="flex-1 bg-gray-50 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#113f8a] focus:bg-white transition-all disabled:opacity-50"
              />

              <button
                type="submit"
                disabled={!inputMensaje.trim() || estaEscribiendo}
                className="bg-[#113f8a] hover:bg-[#0c2f68] text-white px-4 sm:px-5 py-2.5 rounded-lg font-bold text-sm transition-colors flex items-center gap-2 shadow disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Consultar</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </form>

            <div className="mt-2 text-center">
              <span className="text-[11px] text-gray-500">
                La información provista corresponde al Texto Único de Procedimientos Administrativos (TUPA) de la MDJLO.
              </span>
            </div>
          </footer>

        </div>
      </main>

      {/* ------------------------------------------------------------- */}
      {/* 6. PIE DE PÁGINA INSTITUCIONAL NEGRO (COMO EN LA IMAGEN 2)     */}
      {/* ------------------------------------------------------------- */}
      <footer className="bg-[#1a1a1a] text-gray-300 text-xs py-3.5 px-4 sm:px-8 border-t border-gray-800 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span className="font-semibold text-white">2026 OFICINA DE TECNOLOGÍAS DE LA INFORMACIÓN Y COMUNICACIÓN</span>
          </div>
          <div className="flex items-center space-x-4 text-gray-400">
            <span className="hover:text-white cursor-pointer transition">Contacto</span>
            <span>•</span>
            <span className="hover:text-white cursor-pointer transition">Términos de uso</span>
            <span>•</span>
            <span className="hover:text-white cursor-pointer transition">Portal del Estado Peruano (Gob.pe)</span>
          </div>
        </div>
      </footer>

      {/* Botón flotante para volver arriba (idéntico al de la imagen 2) */}
      <button
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        className="fixed bottom-14 right-4 sm:right-6 bg-[#262626] hover:bg-black text-white p-2.5 rounded shadow-lg border border-gray-700 transition-all hover:-translate-y-0.5"
        title="Subir"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 15l7-7 7 7" />
        </svg>
      </button>

    </div>
  );
}
