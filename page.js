'use client';

import { useState, useRef, useEffect } from 'react';

// ============================================================================
// SISTEMA WEB MUNICIPAL - MDJLO (SaaS Enterprise / Premium UI Redesign)
// Stack: Next.js (App Router), React, Tailwind CSS
// Visual Language: Inspired by shadcn/ui & Radix UI Design Systems
// ============================================================================

export default function ChatbotMDJLOPage() {
  // --------------------------------------------------------------------------
  // ESTADOS DE LA APLICACIÓN
  // --------------------------------------------------------------------------
  const [vistaActual, setVistaActual] = useState('chat'); // 'chat' | 'login' | 'admin'
  const [adminAutenticado, setAdminAutenticado] = useState(false);
  const [usuarioAdmin, setUsuarioAdmin] = useState('');

  // Estados del Chat
  const [mensajes, setMensajes] = useState([
    {
      id: 1,
      rol: 'bot',
      texto: '¡Hola! Soy Leonardito, el asistente virtual de la Municipalidad Distrital de José Leonardo Ortiz. ¿Sobre qué trámite o requisito del TUPA deseas consultar hoy?',
      datosTramite: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputMensaje, setInputMensaje] = useState('');
  const [estaEscribiendo, setEstaEscribiendo] = useState(false);
  const finDelChatRef = useRef(null);

  // Estados de Autenticación Admin
  const [inputUsuario, setInputUsuario] = useState('');
  const [inputPassword, setInputPassword] = useState('');
  const [errorLogin, setErrorLogin] = useState('');
  const [cargandoLogin, setCargandoLogin] = useState(false);

  // Estados del Dashboard CRUD
  const [tramites, setTramites] = useState([]);
  const [cargandoTramites, setCargandoTramites] = useState(false);
  const [busquedaTramite, setBusquedaTramite] = useState('');
  const [modalAbierto, setModalAbierto] = useState(false);
  const [tramiteEditando, setTramiteEditando] = useState(null); // null = Crear, objeto = Editar
  const [formData, setFormData] = useState({
    id_tramite: '',
    nombre: '',
    costo: '',
    plazo: '',
    requisitos: [''],
  });
  const [notificacion, setNotificacion] = useState(null); // { tipo: 'success'|'error', texto: '' }

  // --------------------------------------------------------------------------
  // EFECTOS
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (vistaActual === 'chat') {
      finDelChatRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [mensajes, estaEscribiendo, vistaActual]);

  useEffect(() => {
    if (vistaActual === 'admin' && adminAutenticado) {
      cargarTramitesBackend();
    }
  }, [vistaActual, adminAutenticado]);

  const mostrarNotificacion = (texto, tipo = 'success') => {
    setNotificacion({ texto, tipo });
    setTimeout(() => setNotificacion(null), 4000);
  };

  // --------------------------------------------------------------------------
  // LÓGICA DE API - CHAT
  // --------------------------------------------------------------------------
  const enviarMensajeChat = async (textoAEnviar) => {
    const texto = (textoAEnviar || inputMensaje).trim();
    if (!texto || estaEscribiendo) return;

    const horaActual = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const mensajeUsuario = {
      id: Date.now(),
      rol: 'usuario',
      texto,
      datosTramite: null,
      timestamp: horaActual,
    };

    setMensajes((prev) => [...prev, mensajeUsuario]);
    setInputMensaje('');
    setEstaEscribiendo(true);

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ mensaje: texto }),
      });

      const data = await response.json();
      let mensajeBot;

      if (response.ok && (data.status === 'success' || data.status === 'saludo' || data.status === 'charla_casual')) {
        mensajeBot = {
          id: Date.now() + 1,
          rol: 'bot',
          texto: data.mensaje || `Información encontrada para: ${data.nombre}`,
          datosTramite: data.datosTramite || (data.nombre ? {
            id_tramite: data.id_tramite,
            nombre: data.nombre,
            costo: data.costo,
            plazo: data.plazo,
            requisitos: Array.isArray(data.requisitos) ? data.requisitos : [],
          } : null),
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      } else {
        mensajeBot = {
          id: Date.now() + 1,
          rol: 'bot',
          texto: data.mensaje || 'Solo puedo orientarte sobre trámites del TUPA municipal (licencias comerciales, cambio de giro, duplicados, etc.). Por favor reformula tu pregunta.',
          datosTramite: null,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      }

      setMensajes((prev) => [...prev, mensajeBot]);
    } catch (error) {
      console.warn('Backend local no disponible, simulando respuesta:', error);
      // Fallback amigable si el servidor Flask no está encendido
      setTimeout(() => {
        setMensajes((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            rol: 'bot',
            texto: `Información sobre la consulta: "${texto}". (Nota: El backend Flask local en http://localhost:5000 no respondió, asegurate de ejecutar python app.py para ver datos reales del TUPA).`,
            datosTramite: {
              id_tramite: 'T_DEMO',
              nombre: 'Consulta Procedimental TUPA',
              costo: 'S/ 48.50',
              plazo: '5 días hábiles',
              requisitos: [
                'FUT (Formulario Único de Trámite) firmado por el solicitante.',
                'Copia simple de DNI vigente o RUC de la empresa.',
                'Croquis de ubicación del establecimiento a escala.',
                'Declaración jurada de condiciones de seguridad.'
              ]
            },
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }, 700);
    } finally {
      setEstaEscribiendo(false);
    }
  };

  // --------------------------------------------------------------------------
  // LÓGICA DE API - LOGIN ADMIN
  // --------------------------------------------------------------------------
  const ejecutarLogin = async (e) => {
    e.preventDefault();
    setErrorLogin('');
    setCargandoLogin(true);

    try {
      const response = await fetch('http://localhost:5000/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ usuario: inputUsuario, password: inputPassword }),
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setAdminAutenticado(true);
        setUsuarioAdmin(data.username || inputUsuario);
        setVistaActual('admin');
        mostrarNotificacion(`Bienvenido, ${data.username || inputUsuario}`);
      } else {
        setErrorLogin(data.mensaje || 'Usuario o contraseña incorrectos.');
      }
    } catch (err) {
      // Mock Login si Flask está offline para demostración en UI
      if (inputUsuario === 'admin' && inputPassword === 'admin123') {
        setAdminAutenticado(true);
        setUsuarioAdmin('admin');
        setVistaActual('admin');
        mostrarNotificacion('Autenticado (Modo Demo sin backend)');
      } else {
        setErrorLogin('Credenciales inválidas. Prueba con usuario: admin / clave: admin123');
      }
    } finally {
      setCargandoLogin(false);
    }
  };

  const cerrarSesionAdmin = () => {
    setAdminAutenticado(false);
    setUsuarioAdmin('');
    setVistaActual('chat');
    mostrarNotificacion('Sesión cerrada correctamente', 'error');
  };

  // --------------------------------------------------------------------------
  // LÓGICA DE API - CRUD TRÁMITES
  // --------------------------------------------------------------------------
  const cargarTramitesBackend = async () => {
    setCargandoTramites(true);
    try {
      const res = await fetch('http://localhost:5000/api/admin/tramites');
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setTramites(data.tramites || []);
      }
    } catch (err) {
      console.warn('Usando datos de respaldo para la tabla de trámites:', err);
      setTramites([
        { id: 1, id_tramite: 'T_001', nombre: 'Licencia de Funcionamiento Indefinida para Establecimientos', costo: 'S/ 120.00', plazo: '3 días hábiles', requisitos: ['Solicitud de Licencia de Funcionamiento (FUT)', 'Copia simple de DNI o RUC', 'Declaración Jurada de observancia de condiciones de seguridad en Defensa Civil'] },
        { id: 2, id_tramite: 'T_002', nombre: 'Cambio de Giro Comercial de Establecimiento', costo: 'S/ 45.00', plazo: '2 días hábiles', requisitos: ['FUT detallando el nuevo giro', 'Copia de Licencia de Funcionamiento anterior'] },
        { id: 3, id_tramite: 'T_003', nombre: 'Duplicado de Licencia Municipal de Funcionamiento', costo: 'S/ 25.00', plazo: '1 día hábil', requisitos: ['Solicitud motivada', 'Declaración jurada de pérdida o deterioro'] },
        { id: 4, id_tramite: 'T_004', nombre: 'Acceso a la Información Pública Institucional', costo: 'Gratuito', plazo: '10 días hábiles', requisitos: ['Formulario de solicitud de acceso a la información pública', 'Copia de DNI del solicitante'] },
        { id: 5, id_tramite: 'T_005', nombre: 'Certificado de Jurisdicción y Numeración Finca', costo: 'S/ 38.00', plazo: '5 días hábiles', requisitos: ['Copia simple de título de propiedad o escritura', 'Plano de ubicación emitido por profesional colegiado'] },
      ]);
    } finally {
      setCargandoTramites(false);
    }
  };

  const abrirModalNuevo = () => {
    setTramiteEditando(null);
    setFormData({ id_tramite: '', nombre: '', costo: '', plazo: '', requisitos: [''] });
    setModalAbierto(true);
  };

  const abrirModalEditar = (t) => {
    setTramiteEditando(t);
    setFormData({
      id_tramite: t.id_tramite || '',
      nombre: t.nombre || '',
      costo: t.costo || '',
      plazo: t.plazo || '',
      requisitos: Array.isArray(t.requisitos) && t.requisitos.length > 0 ? [...t.requisitos] : [''],
    });
    setModalAbierto(true);
  };

  const guardarTramite = async (e) => {
    e.preventDefault();
    if (!formData.id_tramite.trim() || !formData.nombre.trim()) return;

    const payload = {
      id_tramite: formData.id_tramite.trim(),
      nombre: formData.nombre.trim(),
      costo: formData.costo.trim() || 'Gratuito',
      plazo: formData.plazo.trim() || 'Inmediato',
      requisitos: formData.requisitos.map((r) => r.trim()).filter(Boolean),
    };

    try {
      const url = tramiteEditando
        ? `http://localhost:5000/api/admin/tramites/${tramiteEditando.id || tramiteEditando.id_tramite}`
        : 'http://localhost:5000/api/admin/tramites';
      const method = tramiteEditando ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        mostrarNotificacion(tramiteEditando ? 'Trámite actualizado con éxito' : 'Trámite registrado correctamente');
        setModalAbierto(false);
        cargarTramitesBackend();
      } else {
        throw new Error('Falló respuesta API');
      }
    } catch (err) {
      // Modificación local simulada
      if (tramiteEditando) {
        setTramites((prev) => prev.map((item) => (item.id_tramite === tramiteEditando.id_tramite ? { ...item, ...payload } : item)));
        mostrarNotificacion('Trámite actualizado (Modo Demo)');
      } else {
        setTramites((prev) => [...prev, { id: Date.now(), ...payload }]);
        mostrarNotificacion('Trámite creado (Modo Demo)');
      }
      setModalAbierto(false);
    }
  };

  const eliminarTramite = async (id_tramite) => {
    if (!confirm(`¿Estás seguro de eliminar el trámite "${id_tramite}"?`)) return;

    try {
      const res = await fetch(`http://localhost:5000/api/admin/tramites/${id_tramite}`, { method: 'DELETE' });
      if (res.ok) {
        mostrarNotificacion('Trámite eliminado con éxito');
        cargarTramitesBackend();
      } else {
        throw new Error();
      }
    } catch (err) {
      setTramites((prev) => prev.filter((item) => item.id_tramite !== id_tramite));
      mostrarNotificacion('Trámite eliminado (Modo Demo)');
    }
  };

  // Sugerencias rápidas para el chat
  const sugerencias = [
    'Requisitos para licencia de bodega',
    '¿Cuánto cuesta el cambio de giro?',
    'Duplicado de licencia municipal',
    'Acceso a la información pública',
  ];

  const tramitesFiltrados = tramites.filter(
    (t) =>
      t.nombre.toLowerCase().includes(busquedaTramite.toLowerCase()) ||
      t.id_tramite.toLowerCase().includes(busquedaTramite.toLowerCase())
  );

  // ==========================================================================
  // RENDERIZADO VISUAL
  // ==========================================================================
  return (
    <div className="min-h-screen bg-slate-50/50 text-slate-900 font-sans selection:bg-amber-100 selection:text-amber-900 flex flex-col">
      
      {/* ---------------------------------------------------------------------- */}
      {/* A. NAVBAR GLOBAL - GLASSMORPHISM ENTERPRISE                             */}
      {/* ---------------------------------------------------------------------- */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-white/80 border-b border-slate-200/80 transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Logo & Identidad Institucional */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-slate-900 flex items-center justify-center text-white shadow-sm ring-1 ring-slate-900/5">
              <svg className="w-5 h-5 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 21h18" />
                <path d="M5 21V7l7-4 7 4v14" />
                <path d="M9 10a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v11H9z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900 tracking-tight text-sm">MDJLO</span>
                <span className="text-[10px] font-medium uppercase tracking-wider bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full border border-slate-200">
                  Gobierno Digital
                </span>
              </div>
              <p className="text-xs text-slate-500 font-normal">Municipalidad Distrital de José Leonardo Ortiz</p>
            </div>
          </div>

          {/* Navegador de Vistas Estilo Radix Tabs */}
          <nav className="flex items-center gap-1 bg-slate-100/80 p-1 rounded-xl border border-slate-200/60 text-xs font-medium">
            <button
              onClick={() => setVistaActual('chat')}
              className={`px-3.5 py-1.5 rounded-lg transition-all duration-200 flex items-center gap-2 ${
                vistaActual === 'chat'
                  ? 'bg-white text-slate-900 shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
              }`}
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <span>Atención Ciudadana</span>
            </button>

            <button
              onClick={() => setVistaActual(adminAutenticado ? 'admin' : 'login')}
              className={`px-3.5 py-1.5 rounded-lg transition-all duration-200 flex items-center gap-2 ${
                vistaActual === 'admin' || vistaActual === 'login'
                  ? 'bg-slate-900 text-white shadow-xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
              }`}
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              <span>{adminAutenticado ? `Admin (${usuarioAdmin})` : 'Panel Admin'}</span>
            </button>
          </nav>
        </div>
      </header>

      {/* Toast Notificación */}
      {notificacion && (
        <div className="fixed top-20 right-6 z-50 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className={`px-4 py-3 rounded-xl shadow-lg border text-xs font-medium flex items-center gap-2.5 ${
            notificacion.tipo === 'error'
              ? 'bg-red-50 text-red-900 border-red-200'
              : 'bg-slate-900 text-white border-slate-800'
          }`}>
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
            <span>{notificacion.texto}</span>
          </div>
        </div>
      )}

      {/* ---------------------------------------------------------------------- */}
      {/* B. VISTA 1: CHATBOT CIUDADANO (ESTILO CHATGPT / PERPLEXITY INMERSIVO)   */}
      {/* ---------------------------------------------------------------------- */}
      {vistaActual === 'chat' && (
        <main className="flex-1 flex flex-col max-w-3xl w-full mx-auto px-4 py-6">
          
          {/* Conversación / Mensajes */}
          <div className="flex-1 space-y-6 pb-28">
            
            {/* Estado Inicial (Hero / Empty State) */}
            {mensajes.length === 1 && (
              <div className="text-center py-10 space-y-4 animate-in fade-in duration-500">
                <div className="w-12 h-12 rounded-2xl bg-amber-400/10 text-amber-600 border border-amber-400/20 mx-auto flex items-center justify-center">
                  <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2a10 10 0 1 0 10 10H12V2z" />
                    <path d="M12 12L2.5 7.5" />
                    <path d="M12 12v9.5" />
                  </svg>
                </div>
                <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">
                  Orientación Procedimental TUPA
                </h1>
                <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
                  Haz tus consultas en lenguaje natural sobre requisitos, tarifas y plazos de los trámites municipales en José Leonardo Ortiz.
                </p>

                {/* Sugerencias en Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-4 text-left max-w-xl mx-auto">
                  {sugerencias.map((sug, idx) => (
                    <button
                      key={idx}
                      onClick={() => enviarMensajeChat(sug)}
                      className="p-3.5 rounded-xl bg-white border border-slate-200/80 hover:border-slate-300 hover:shadow-xs text-xs text-slate-700 hover:text-slate-900 transition-all duration-200 flex items-center justify-between group"
                    >
                      <span>{sug}</span>
                      <svg className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-900 transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M5 12h14" />
                        <path d="M12 5l7 7-7 7" />
                      </svg>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Lista de Mensajes del Chat */}
            {mensajes.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 text-sm animate-in fade-in duration-300 ${
                  m.rol === 'usuario' ? 'justify-end' : 'justify-start'
                }`}
              >
                {/* Avatar del Bot */}
                {m.rol === 'bot' && (
                  <div className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center shrink-0 text-xs font-semibold shadow-xs">
                    L
                  </div>
                )}

                {/* Contenido del Mensaje */}
                <div className={`space-y-3 max-w-xl ${m.rol === 'usuario' ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      m.rol === 'usuario'
                        ? 'bg-slate-900 text-white rounded-tr-xs shadow-xs'
                        : 'bg-white border border-slate-200/80 text-slate-800 rounded-tl-xs shadow-xs'
                    }`}
                  >
                    <p className="whitespace-pre-line leading-relaxed text-[13.5px]">{m.texto}</p>
                  </div>

                  {/* Card Estructurado de Datos del Trámite (si aplica) */}
                  {m.datosTramite && (
                    <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-3 text-xs animate-in zoom-in-95 duration-200">
                      <div className="flex items-start justify-between border-b border-slate-100 pb-2.5">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200/60">
                            {m.datosTramite.id_tramite || 'Trámite TUPA'}
                          </span>
                          <h4 className="font-semibold text-slate-900 text-sm mt-1">
                            {m.datosTramite.nombre}
                          </h4>
                        </div>
                      </div>

                      {/* Badges de Costo y Plazo */}
                      <div className="flex flex-wrap gap-2 text-xs">
                        {m.datosTramite.costo && (
                          <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200/60 px-2.5 py-1 rounded-lg">
                            <span className="font-medium">Costo:</span>
                            <span className="font-semibold">{m.datosTramite.costo}</span>
                          </div>
                        )}
                        {m.datosTramite.plazo && (
                          <div className="flex items-center gap-1.5 bg-blue-50 text-blue-800 border border-blue-200/60 px-2.5 py-1 rounded-lg">
                            <span className="font-medium">Plazo:</span>
                            <span className="font-semibold">{m.datosTramite.plazo}</span>
                          </div>
                        )}
                      </div>

                      {/* Lista de Requisitos */}
                      {Array.isArray(m.datosTramite.requisitos) && m.datosTramite.requisitos.length > 0 && (
                        <div className="space-y-1.5 pt-1">
                          <span className="font-medium text-slate-500 block text-[11px] uppercase tracking-wider">
                            Requisitos Presentar:
                          </span>
                          <ul className="space-y-1 pl-1">
                            {m.datosTramite.requisitos.map((req, i) => (
                              <li key={i} className="flex items-start gap-2 text-slate-700">
                                <span className="text-amber-500 font-bold">•</span>
                                <span className="leading-snug">{req}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  <span className="text-[10px] text-slate-400 block px-1">{m.timestamp}</span>
                </div>
              </div>
            ))}

            {/* Indicador de Escritura / Pensando */}
            {estaEscribiendo && (
              <div className="flex gap-3 text-sm items-center text-slate-400 animate-pulse">
                <div className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-semibold">
                  L
                </div>
                <div className="bg-white border border-slate-200 px-4 py-2.5 rounded-2xl rounded-tl-xs flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0.4s]"></span>
                </div>
              </div>
            )}

            <div ref={finDelChatRef} />
          </div>

          {/* Floating Input Bar (Estilo Perplexity/ChatGPT Premium) */}
          <div className="fixed bottom-6 inset-x-4 max-w-3xl mx-auto z-30">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                enviarMensajeChat();
              }}
              className="relative flex items-center bg-white rounded-2xl border border-slate-200 shadow-lg shadow-slate-900/5 p-1.5 focus-within:ring-2 focus-within:ring-slate-900/10 focus-within:border-slate-300 transition-all duration-300"
            >
              <input
                type="text"
                value={inputMensaje}
                onChange={(e) => setInputMensaje(e.target.value)}
                placeholder="Escribe tu consulta sobre requisitos, costo o plazo..."
                className="w-full px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 bg-transparent border-0 focus:outline-none"
              />
              <button
                type="submit"
                disabled={!inputMensaje.trim() || estaEscribiendo}
                className="w-9 h-9 rounded-xl bg-slate-900 hover:bg-slate-800 text-white flex items-center justify-center transition-all duration-200 disabled:opacity-30 disabled:hover:bg-slate-900 shrink-0"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 2L11 13" />
                  <path d="M22 2l-7 20-4-9-9-4 20-7z" />
                </svg>
              </button>
            </form>
            <p className="text-[11px] text-center text-slate-400 mt-2">
              Información oficial del TUPA de la Municipalidad Distrital de José Leonardo Ortiz.
            </p>
          </div>
        </main>
      )}

      {/* ---------------------------------------------------------------------- */}
      {/* C. VISTA 2: AUTENTICACIÓN ADMIN (MINIMALISTA SAAS PREMIUM)              */}
      {/* ---------------------------------------------------------------------- */}
      {vistaActual === 'login' && (
        <main className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-white p-8 rounded-2xl border border-slate-200/80 shadow-sm space-y-6 animate-in zoom-in-95 duration-300">
            
            <div className="text-center space-y-2">
              <div className="w-10 h-10 rounded-xl bg-slate-900 text-amber-400 mx-auto flex items-center justify-center shadow-xs">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-slate-900 tracking-tight">Panel Administrativo</h2>
              <p className="text-xs text-slate-500">Ingresa tus credenciales para gestionar el TUPA</p>
            </div>

            {errorLogin && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200/80 text-xs text-red-700 font-medium">
                {errorLogin}
              </div>
            )}

            <form onSubmit={ejecutarLogin} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700 block">Usuario</label>
                <input
                  type="text"
                  required
                  value={inputUsuario}
                  onChange={(e) => setInputUsuario(e.target.value)}
                  placeholder="admin"
                  className="w-full px-3.5 py-2 text-sm bg-slate-50/50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700 block">Contraseña</label>
                <input
                  type="password"
                  required
                  value={inputPassword}
                  onChange={(e) => setInputPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2 text-sm bg-slate-50/50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={cargandoLogin}
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium py-2.5 rounded-xl text-sm transition-all duration-200 shadow-sm hover:shadow active:scale-[0.99] disabled:opacity-50"
              >
                {cargandoLogin ? 'Verificando...' : 'Iniciar Sesión'}
              </button>
            </form>

            <div className="pt-2 border-t border-slate-100 text-center">
              <p className="text-[11px] text-slate-400">
                Credenciales por defecto: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">admin</code> / <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">admin123</code>
              </p>
            </div>
          </div>
        </main>
      )}

      {/* ---------------------------------------------------------------------- */}
      {/* D. VISTA 3: DASHBOARD ADMINISTRACIÓN CRUD (ENTERPRISE DATA TABLE)      */}
      {/* ---------------------------------------------------------------------- */}
      {vistaActual === 'admin' && adminAutenticado && (
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
          
          {/* Header Interno del Dashboard */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200/80">
            <div>
              <h1 className="text-xl font-semibold text-slate-900 tracking-tight">Catálogo de Trámites TUPA</h1>
              <p className="text-xs text-slate-500 mt-0.5">Gestión de trámites, costos, plazos y requisitos oficiales</p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={abrirModalNuevo}
                className="bg-slate-900 hover:bg-slate-800 text-white font-medium px-4 py-2 rounded-xl text-xs transition-all duration-200 shadow-xs flex items-center gap-2 hover:shadow active:scale-[0.99]"
              >
                <svg className="w-3.5 h-3.5 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 5v14M5 12h14" />
                </svg>
                <span>+ Nuevo Trámite</span>
              </button>

              <button
                onClick={cerrarSesionAdmin}
                className="text-xs font-medium text-slate-500 hover:text-red-600 px-3 py-2 rounded-xl border border-slate-200 hover:bg-red-50/50 transition-colors"
              >
                Salir
              </button>
            </div>
          </div>

          {/* Controles de Búsqueda y Stats Rápidas */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="relative max-w-xs w-full">
              <svg className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
              <input
                type="text"
                value={busquedaTramite}
                onChange={(e) => setBusquedaTramite(e.target.value)}
                placeholder="Buscar por código o nombre..."
                className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
            </div>

            <div className="text-xs text-slate-500">
              Total Trámites Registrados: <span className="font-semibold text-slate-900">{tramites.length}</span>
            </div>
          </div>

          {/* Tabla de Datos Enterprise (Sin bordes verticales, líneas horizontales sutiles) */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50/70 border-b border-slate-200/80 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="py-3.5 px-4 w-24">Código</th>
                    <th className="py-3.5 px-4">Denominación del Trámite</th>
                    <th className="py-3.5 px-4 w-32">Costo</th>
                    <th className="py-3.5 px-4 w-36">Plazo</th>
                    <th className="py-3.5 px-4 w-28 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {cargandoTramites ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-slate-400 text-xs">
                        Cargando trámites desde la base de datos...
                      </td>
                    </tr>
                  ) : tramitesFiltrados.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="py-8 text-center text-slate-400 text-xs">
                        No se encontraron trámites registrados.
                      </td>
                    </tr>
                  ) : (
                    tramitesFiltrados.map((t) => (
                      <tr key={t.id || t.id_tramite} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-semibold text-slate-900">
                          {t.id_tramite}
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-900 max-w-md">
                          {t.nombre}
                          {Array.isArray(t.requisitos) && (
                            <span className="block text-[10px] font-normal text-slate-400 mt-0.5">
                              {t.requisitos.length} requisito(s) asociados
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`inline-flex px-2 py-0.5 rounded-md text-[11px] font-medium border ${
                            t.costo === 'Gratuito' || !t.costo
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200/60'
                              : 'bg-slate-100 text-slate-700 border-slate-200'
                          }`}>
                            {t.costo || 'Gratuito'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-slate-600">
                          {t.plazo || 'Inmediato'}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {/* Botones Tipo Ghost */}
                            <button
                              onClick={() => abrirModalEditar(t)}
                              title="Editar"
                              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                            >
                              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                              </svg>
                            </button>

                            <button
                              onClick={() => eliminarTramite(t.id_tramite)}
                              title="Eliminar"
                              className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                            >
                              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="3 6 5 6 21 6" />
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      )}

      {/* ---------------------------------------------------------------------- */}
      {/* MODAL CREAR / EDITAR TRÁMITE (ESTILO RADIX DIALOG)                     */}
      {/* ---------------------------------------------------------------------- */}
      {modalAbierto && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white max-w-lg w-full rounded-2xl border border-slate-200 p-6 shadow-xl space-y-5 animate-in zoom-in-95 duration-200 my-8">
            
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-semibold text-slate-900 text-base">
                {tramiteEditando ? 'Editar Trámite TUPA' : 'Nuevo Trámite Municipal'}
              </h3>
              <button
                onClick={() => setModalAbierto(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            <form onSubmit={guardarTramite} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700 block">Código Trámite *</label>
                  <input
                    type="text"
                    required
                    disabled={!!tramiteEditando}
                    value={formData.id_tramite}
                    onChange={(e) => setFormData({ ...formData, id_tramite: e.target.value })}
                    placeholder="T_011"
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900 disabled:opacity-60"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700 block">Costo (S/)</label>
                  <input
                    type="text"
                    value={formData.costo}
                    onChange={(e) => setFormData({ ...formData, costo: e.target.value })}
                    placeholder="Gratuito o S/ 50.00"
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700 block">Denominación del Trámite *</label>
                <input
                  type="text"
                  required
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  placeholder="Licencia de..."
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-700 block">Plazo de Atención</label>
                <input
                  type="text"
                  value={formData.plazo}
                  onChange={(e) => setFormData({ ...formData, plazo: e.target.value })}
                  placeholder="3 días hábiles"
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              {/* Lista dinámica de requisitos */}
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-slate-700 block">Requisitos Procedimentales</label>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, requisitos: [...formData.requisitos, ''] })}
                    className="text-[11px] text-amber-600 font-semibold hover:underline"
                  >
                    + Agregar Requisito
                  </button>
                </div>

                {formData.requisitos.map((req, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={req}
                      onChange={(e) => {
                        const copia = [...formData.requisitos];
                        copia[idx] = e.target.value;
                        setFormData({ ...formData, requisitos: copia });
                      }}
                      placeholder={`Requisito #${idx + 1}`}
                      className="flex-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-slate-900"
                    />
                    {formData.requisitos.length > 1 && (
                      <button
                        type="button"
                        onClick={() => {
                          const copia = formData.requisitos.filter((_, i) => i !== idx);
                          setFormData({ ...formData, requisitos: copia });
                        }}
                        className="text-slate-400 hover:text-red-600 p-1 text-xs"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalAbierto(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium shadow-xs"
                >
                  Guardar Trámite
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Footer Mínimo */}
      <footer className="border-t border-slate-200/60 py-4 text-center text-xs text-slate-400 mt-auto">
        MDJLO © 2026 • Sistema Inteligente de Atención Ciudadana
      </footer>
    </div>
  );
}
