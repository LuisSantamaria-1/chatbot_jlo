'use client';

import { useState, useRef, useEffect } from 'react';

// ============================================================================
// COMPONENTE PRINCIPAL: Portal Ciudadano & Sistema Administrativo MDJLO
// ============================================================================
export default function MunicipalidadJLOApp() {
  // --------------------------------------------------------------------------
  // 1. ESTADOS DE NAVEGACIÓN Y VISTAS
  // --------------------------------------------------------------------------
  const [vistaActual, setVistaActual] = useState('ciudadano'); // 'ciudadano' | 'login' | 'admin'
  const [modoChat, setModoChat] = useState('inmersivo'); // 'inmersivo' | 'flotante'
  const [chatFlotanteAbierto, setChatFlotanteAbierto] = useState(false);

  // --------------------------------------------------------------------------
  // 2. ESTADOS DEL CHATBOT "LEONARDITO"
  // --------------------------------------------------------------------------
  const [mensajes, setMensajes] = useState([
    {
      id: 1,
      rol: 'bot',
      texto: '¡Hola! 👋 Soy Leonardito, el asistente virtual de la Municipalidad Distrital de José Leonardo Ortiz. ¿En qué procedimiento o trámite del TUPA puedo orientarte hoy?',
      datosTramite: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputMensaje, setInputMensaje] = useState('');
  const [estaEscribiendo, setEstaEscribiendo] = useState(false);
  const finDelChatRef = useRef(null);

  // Auto-scroll en el chat
  useEffect(() => {
    finDelChatRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes, estaEscribiendo, vistaActual, modoChat, chatFlotanteAbierto]);

  // Cargar trámites desde la base de datos MySQL (API Flask)
  useEffect(() => {
    cargarTramitesAdmin();
  }, [vistaActual]);

  // Consultas rápidas sugeridas
  const sugerencias = [
    { titulo: 'Licencia Comercial', query: '¿Qué necesito para sacar licencia de funcionamiento?' },
    { titulo: 'Cambio de Giro', query: 'Requisitos para cambio de giro en mi negocio' },
    { titulo: 'Duplicado de Licencia', query: '¿Cómo solicito un duplicado de licencia?' },
    { titulo: 'Acceso a la Información', query: 'Requisitos para solicitud de acceso a la información pública' },
  ];

  // --------------------------------------------------------------------------
  // 3. ESTADOS DEL PANEL ADMINISTRATIVO Y AUTENTICACIÓN
  // --------------------------------------------------------------------------
  const [adminAutenticado, setAdminAutenticado] = useState(false);
  const [credenciales, setCredenciales] = useState({ usuario: '', password: '' });
  const [errorLogin, setErrorLogin] = useState('');
  const [cargandoLogin, setCargandoLogin] = useState(false);

  // Datos del TUPA para el CRUD Admin (con datos iniciales del TUPA MDJLO)
  const [tramites, setTramites] = useState([
    {
      id: 1,
      id_tramite: 'T_001',
      nombre: 'Licencia de Funcionamiento para Edificaciones de Riesgo Bajo (Indefinida)',
      costo: 'S/ 185.50',
      plazo: '3 días hábiles',
      requisitos: [
        'Solicitud de Licencia de Funcionamiento con carácter de Declaración Jurada',
        'Copia de DNI del solicitante o representante legal',
        'Vigencia de poder en caso de persona jurídica (antigüedad máxima 30 días)',
        'Declaración Jurada de Cumplimiento de Condiciones de Seguridad en Edificaciones',
      ],
    },
    {
      id: 2,
      id_tramite: 'T_002',
      nombre: 'Licencia de Funcionamiento para Edificaciones de Riesgo Medio',
      costo: 'S/ 245.00',
      plazo: '5 días hábiles',
      requisitos: [
        'Solicitud - Declaración Jurada formalmente completada',
        'Copia de DNI o Carné de Extranjería',
        'Anexo de condiciones de seguridad en inspección técnica (ITSE)',
        'Pago de la tasa correspondiente en caja municipal',
      ],
    },
    {
      id: 3,
      id_tramite: 'T_003',
      nombre: 'Cambio de Giro en Licencia de Funcionamiento Vigente',
      costo: 'S/ 92.40',
      plazo: '2 días hábiles',
      requisitos: [
        'Solicitud de modificación o cambio de giro administrativo',
        'Copia de la Licencia de Funcionamiento anterior',
        'Declaración jurada de mantener las condiciones de seguridad aprobadas',
      ],
    },
    {
      id: 4,
      id_tramite: 'T_004',
      nombre: 'Duplicado de Licencia de Funcionamiento o Certificado ITSE',
      costo: 'S/ 35.80',
      plazo: '1 día hábil',
      requisitos: [
        'Fut o Solicitud simple dirigida a la Subgerencia de Comercialización',
        'Declaración Jurada por pérdida, deterioro o robo del documento original',
        'Recibo de pago por concepto de duplicado',
      ],
    },
    {
      id: 5,
      id_tramite: 'T_005',
      nombre: 'Cese de Actividades de Comercio o Servicios',
      costo: 'Gratuito',
      plazo: 'Atención inmediata',
      requisitos: [
        'Comunicación escrita con carácter de Declaración Jurada firmada por el titular',
        'Devolución del cartón original de la Licencia de Funcionamiento',
      ],
    },
    {
      id: 6,
      id_tramite: 'T_010',
      nombre: 'Solicitud de Acceso a la Información Pública (Ley N° 27806)',
      costo: 'Gratuito (Solo costo de reproducción)',
      plazo: '10 días hábiles',
      requisitos: [
        'Formulario o solicitud con datos completos del solicitante (DNI, correo, teléfono)',
        'Precisión clara de la información requerida existente en los archivos municipales',
      ],
    },
  ]);

  const [busquedaAdmin, setBusquedaAdmin] = useState('');
  const [modalTramiteAbierto, setModalTramiteAbierto] = useState(false);
  const [tramiteEnEdicion, setTramiteEnEdicion] = useState(null);
  const [formTramite, setFormTramite] = useState({
    id_tramite: '',
    nombre: '',
    costo: '',
    plazo: '',
    requisitos: [''],
  });

  // --------------------------------------------------------------------------
  // 4. LÓGICA DE COMUNICACIÓN CON EL BACKEND FLASK (/api/chat)
  // --------------------------------------------------------------------------
  const enviarMensaje = async (textoAEnviar) => {
    const texto = (textoAEnviar || inputMensaje).trim();
    if (!texto || estaEscribiendo) return;

    const hora = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const mensajeUsuario = {
      id: Date.now(),
      rol: 'usuario',
      texto: texto,
      datosTramite: null,
      timestamp: hora,
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
      if (response.ok && data.status === 'success') {
        mensajeBot = {
          id: Date.now() + 1,
          rol: 'bot',
          texto: data.mensaje || `Información procesada para el trámite: ${data.nombre}`,
          datosTramite: data.datosTramite || {
            nombre: data.nombre,
            costo: data.costo,
            plazo: data.plazo,
            requisitos: data.requisitos || [],
          },
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      } else {
        mensajeBot = {
          id: Date.now() + 1,
          rol: 'bot',
          texto: data.mensaje || 'Solo puedo orientarte sobre los trámites del TUPA de la Municipalidad Distrital de José Leonardo Ortiz. Por favor formula una consulta sobre licencias o trámites.',
          datosTramite: null,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      }
      setMensajes((prev) => [...prev, mensajeBot]);
    } catch (error) {
      console.warn('Backend Flask no disponible en http://localhost:5000. Ejecutando respuesta simulada local.', error);
      // Fallback local por si se prueba de forma independiente
      setTimeout(() => {
        const textoLower = texto.toLowerCase();
        let respuestaSimulada = {
          id: Date.now() + 1,
          rol: 'bot',
          texto: 'Solo puedo orientarte sobre los trámites del TUPA de la Municipalidad Distrital de José Leonardo Ortiz. ¿Tienes alguna pregunta sobre licencias o requisitos?',
          datosTramite: null,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        if (textoLower.includes('bodega') || textoLower.includes('licencia') || textoLower.includes('funcionamiento')) {
          respuestaSimulada = {
            id: Date.now() + 1,
            rol: 'bot',
            texto: 'Para el trámite "Licencia de Funcionamiento para Edificaciones de Riesgo Bajo" necesitas presentar la siguiente documentación:',
            datosTramite: tramites[0],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
        } else if (textoLower.includes('giro') || textoLower.includes('cambio')) {
          respuestaSimulada = {
            id: Date.now() + 1,
            rol: 'bot',
            texto: 'Para la solicitud de "Cambio de Giro en Licencia Vigente" se requieren los siguientes documentos:',
            datosTramite: tramites[2],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
        } else if (textoLower.includes('duplicado')) {
          respuestaSimulada = {
            id: Date.now() + 1,
            rol: 'bot',
            texto: 'Para obtener un "Duplicado de Licencia o Certificado ITSE" debes presentar:',
            datosTramite: tramites[3],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          };
        }

        setMensajes((prev) => [...prev, respuestaSimulada]);
      }, 700);
    } finally {
      setEstaEscribiendo(false);
    }
  };

  // --------------------------------------------------------------------------
  // 5. LÓGICA DE AUTENTICACIÓN Y CRUD ADMIN
  // --------------------------------------------------------------------------
  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorLogin('');
    setCargandoLogin(true);

    try {
      const response = await fetch('http://localhost:5000/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(credenciales),
      });
      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setAdminAutenticado(true);
        setVistaActual('admin');
        cargarTramitesAdmin();
      } else {
        setErrorLogin(data.mensaje || 'Usuario o contraseña incorrectos');
      }
    } catch (err) {
      setErrorLogin('Error de conexión con el servidor. Intente nuevamente.');
    } finally {
      setCargandoLogin(false);
    }
  };

  const cargarTramitesAdmin = async () => {
    try {
      const res = await fetch('http://localhost:5000/api/admin/tramites');
      const data = await res.json();
      if (res.ok && data.tramites) {
        setTramites(data.tramites);
      }
    } catch (e) {
      console.log('Usando trámites de memoria local');
    }
  };

  const abrirModalNuevo = () => {
    setTramiteEnEdicion(null);
    setFormTramite({ id_tramite: '', nombre: '', costo: '', plazo: '', requisitos: [''] });
    setModalTramiteAbierto(true);
  };

  const abrirModalEditar = (item) => {
    setTramiteEnEdicion(item);
    setFormTramite({
      id_tramite: item.id_tramite || '',
      nombre: item.nombre || '',
      costo: item.costo || '',
      plazo: item.plazo || '',
      requisitos: item.requisitos && item.requisitos.length > 0 ? [...item.requisitos] : [''],
    });
    setModalTramiteAbierto(true);
  };

  const guardarTramite = (e) => {
    e.preventDefault();
    const reqFiltrados = formTramite.requisitos.filter((r) => r.trim() !== '');

    if (tramiteEnEdicion) {
      setTramites((prev) =>
        prev.map((t) =>
          t.id === tramiteEnEdicion.id
            ? { ...t, ...formTramite, requisitos: reqFiltrados }
            : t
        )
      );
    } else {
      const nuevo = {
        id: Date.now(),
        ...formTramite,
        requisitos: reqFiltrados,
      };
      setTramites((prev) => [nuevo, ...prev]);
    }
    setModalTramiteAbierto(false);
  };

  const eliminarTramite = (id) => {
    if (confirm('¿Estás seguro de eliminar este trámite del TUPA?')) {
      setTramites((prev) => prev.filter((t) => t.id !== id));
    }
  };

  const tramitesFiltrados = tramites.filter(
    (t) =>
      t.nombre.toLowerCase().includes(busquedaAdmin.toLowerCase()) ||
      t.id_tramite.toLowerCase().includes(busquedaAdmin.toLowerCase())
  );

  // ==========================================================================
  // RENDERIZADO VISUAL PRINCIPAL
  // ==========================================================================
  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 font-sans flex flex-col selection:bg-amber-100 selection:text-amber-900">
      
      {/* -------------------------------------------------------------------- */}
      /* 1. BARRA SUPERIOR INSTITUCIONAL (Oficial MDJLO)                        */
      /* -------------------------------------------------------------------- */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-slate-900/95 border-b border-slate-800 text-white shadow-sm transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Logo Heráldico & Marca de la Municipalidad */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setVistaActual('ciudadano')}>
            {/* Escudo Municipal Vectorial */}
            <div className="w-10 h-11 bg-gradient-to-b from-red-600 to-red-800 rounded-lg p-1 flex flex-col items-center justify-between border border-amber-400/40 shadow-sm transition-transform hover:scale-105">
              <span className="text-[9px] font-black tracking-tighter text-amber-300 uppercase leading-none mt-0.5">MDJLO</span>
              <svg className="w-5 h-5 text-amber-300 my-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-5.45 9-12V7l-9-5z" fill="rgba(251,191,36,0.15)" />
                <path d="M12 8v8m-4-4h8" strokeLinecap="round" />
              </svg>
            </div>

            <div>
              <h1 className="font-bold text-sm sm:text-base tracking-tight text-white flex items-center gap-1.5">
                <span>Municipalidad Distrital de José Leonardo Ortiz</span>
              </h1>
              <p className="text-[11px] font-medium text-slate-400 tracking-wide flex items-center gap-2">
                <span>Chiclayo - Lambayeque</span>
                <span className="text-slate-600">•</span>
                <span className="text-amber-400 font-semibold">Portal Oficial TUPA</span>
              </p>
            </div>
          </div>

          {/* Navegación Derecha */}
          <nav className="flex items-center space-x-2">
            <button
              onClick={() => setVistaActual('ciudadano')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-2 ${
                vistaActual === 'ciudadano'
                  ? 'bg-slate-800 text-amber-400 border border-slate-700 shadow-xs'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span>Atención Ciudadana</span>
            </button>

            <button
              onClick={() => setVistaActual(adminAutenticado ? 'admin' : 'login')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-2 ${
                vistaActual === 'admin' || vistaActual === 'login'
                  ? 'bg-amber-400 text-slate-950 font-bold shadow-xs'
                  : 'bg-slate-800/90 text-slate-200 border border-slate-700/80 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>{adminAutenticado ? 'Panel de Control' : 'Acceso Institucional'}</span>
            </button>
          </nav>

        </div>
      </header>

      {/* -------------------------------------------------------------------- */}
      {/* VISTA 1: PORTAL CIUDADANO E INTERFAZ DEL CHATBOT "LEONARDITO"          */}
      {/* -------------------------------------------------------------------- */}
      {vistaActual === 'ciudadano' && (
        <main className="flex-1 flex flex-col max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 transition-all duration-300">
          
          {/* Banner Institucional Minimalista */}
          <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 mb-6 text-white shadow-sm border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-400/10 border border-amber-400/30 text-amber-300 text-[11px] font-semibold tracking-wide uppercase">
                <span>🤖 Asistente Virtual Cognitivo NLP</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
                Orientación sobre Trámites Procedimentales (TUPA)
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 max-w-2xl">
                Consulta los requisitos, tasas de pago y plazos de atención oficial de la Municipalidad Distrital de José Leonardo Ortiz en tiempo real.
              </p>
            </div>
            
            <div className="flex items-center gap-2 self-stretch md:self-auto justify-end">
              <button
                onClick={() => setModoChat(modoChat === 'inmersivo' ? 'flotante' : 'inmersivo')}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition flex items-center gap-1.5 shadow-xs"
              >
                <span>{modoChat === 'inmersivo' ? '📐 Vista Flotante' : '🖥️ Vista Inmersiva'}</span>
              </button>
            </div>
          </div>

          {/* Chips de Consultas Frecuentes / Accesos Rápidos */}
          <div className="mb-6">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <span>💡 Consultas recomendadas sobre trámites:</span>
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {sugerencias.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => enviarMensaje(item.query)}
                  className="bg-white hover:bg-amber-50/50 border border-slate-200/80 hover:border-amber-300/80 rounded-xl p-3 text-left transition-all duration-200 group shadow-2xs hover:shadow-xs flex flex-col justify-between"
                >
                  <span className="text-xs font-bold text-slate-900 group-hover:text-slate-950 flex items-center justify-between">
                    {item.titulo}
                    <svg className="w-3.5 h-3.5 text-slate-400 group-hover:text-amber-600 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </span>
                  <span className="text-[11px] text-slate-500 mt-1 line-clamp-1 group-hover:text-slate-600">
                    {item.query}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Canvas de Conversación Principal (Modo Inmersivo) */}
          <div className="flex-1 bg-white rounded-2xl border border-slate-200/80 shadow-xs flex flex-col overflow-hidden min-h-[480px]">
            
            {/* Encabezado del Chat */}
            <div className="bg-slate-50/80 border-b border-slate-100 px-5 py-3.5 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="w-9 h-9 rounded-xl bg-slate-900 text-amber-400 flex items-center justify-center font-bold text-sm shadow-xs border border-slate-800">
                    L
                  </div>
                  <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-white rounded-full"></span>
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                    <span>Leonardito</span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-semibold">En Línea</span>
                  </h3>
                  <p className="text-[11px] text-slate-500">Asistente Virtual TUPA • MDJLO</p>
                </div>
              </div>

              <div className="text-right text-[11px] text-slate-400">
                <span>Respuesta Inmediata</span>
              </div>
            </div>

            {/* Área del Historial de Mensajes */}
            <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-4 max-h-[520px]">
              {mensajes.map((m) => (
                <div
                  key={m.id}
                  className={`flex ${m.rol === 'usuario' ? 'justify-end' : 'justify-start'} transition-all duration-300 animate-fadeIn`}
                >
                  <div className={`flex items-start space-x-2.5 max-w-2xl ${m.rol === 'usuario' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    
                    {/* Avatar */}
                    {m.rol === 'bot' && (
                      <div className="w-8 h-8 rounded-lg bg-slate-900 text-amber-300 flex-shrink-0 flex items-center justify-center font-bold text-xs border border-slate-800 shadow-2xs">
                        🤖
                      </div>
                    )}
                    {m.rol === 'usuario' && (
                      <div className="w-8 h-8 rounded-lg bg-amber-400 text-slate-950 flex-shrink-0 flex items-center justify-center font-bold text-xs shadow-2xs">
                        👤
                      </div>
                    )}

                    {/* Burbuja de Mensaje */}
                    <div>
                      <div
                        className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                          m.rol === 'usuario'
                            ? 'bg-slate-900 text-white rounded-tr-xs shadow-2xs'
                            : 'bg-slate-100/90 text-slate-800 rounded-tl-xs border border-slate-200/60'
                        }`}
                      >
                        <p className="whitespace-pre-line">{m.texto}</p>

                        {/* Tarjeta de Detalles de Trámites (Si aplica) */}
                        {m.datosTramite && (
                          <div className="mt-3.5 pt-3 border-t border-slate-200/80 space-y-2.5">
                            
                            {/* Badges de Costo y Plazo */}
                            <div className="flex flex-wrap gap-2">
                              {m.datosTramite.costo && (
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
                                  <span>💰 Costo:</span>
                                  <span>{m.datosTramite.costo}</span>
                                </span>
                              )}
                              {m.datosTramite.plazo && (
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-50 text-blue-800 border border-blue-200 text-xs font-bold">
                                  <span>⏱️ Plazo:</span>
                                  <span>{m.datosTramite.plazo}</span>
                                </span>
                              )}
                            </div>

                            {/* Lista de Requisitos */}
                            {m.datosTramite.requisitos && m.datosTramite.requisitos.length > 0 && (
                              <div className="bg-white rounded-xl p-3 border border-slate-200/70 shadow-2xs space-y-1.5">
                                <p className="text-xs font-bold text-slate-900 border-b border-slate-100 pb-1 flex items-center justify-between">
                                  <span>Requisitos Procedimentales:</span>
                                  <span className="text-[10px] text-slate-400 font-normal">{m.datosTramite.requisitos.length} requisitos</span>
                                </p>
                                <ul className="space-y-1 text-xs text-slate-700">
                                  {m.datosTramite.requisitos.map((req, i) => (
                                    <li key={i} className="flex items-start gap-1.5">
                                      <span className="text-emerald-600 font-bold">•</span>
                                      <span>{req}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      <span className="text-[10px] text-slate-400 px-1 mt-1 block font-medium">
                        {m.timestamp}
                      </span>
                    </div>

                  </div>
                </div>
              ))}

              {/* Indicador de escritura */}
              {estaEscribiendo && (
                <div className="flex items-center space-x-2 text-slate-400 text-xs py-2 px-1">
                  <div className="w-7 h-7 rounded-lg bg-slate-900 text-amber-300 flex items-center justify-center font-bold text-xs">
                    🤖
                  </div>
                  <div className="bg-slate-100 rounded-xl px-3 py-2 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                    <span className="text-[11px] text-slate-500 font-medium ml-1">Leonardito está buscando en el TUPA...</span>
                  </div>
                </div>
              )}

              <div ref={finDelChatRef} />
            </div>

            {/* Input del Chatbot (Flotante / Estilo Perplexity) */}
            <div className="p-3 sm:p-4 bg-white border-t border-slate-100">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  enviarMensaje();
                }}
                className="relative flex items-center bg-slate-50 border border-slate-200/90 rounded-2xl p-1.5 shadow-xs focus-within:border-slate-800 focus-within:ring-2 focus-within:ring-slate-900/10 transition-all"
              >
                <input
                  type="text"
                  value={inputMensaje}
                  onChange={(e) => setInputMensaje(e.target.value)}
                  placeholder="Escribe tu consulta sobre trámites o requisitos (ej. Licencia de funcionamiento)..."
                  className="flex-1 bg-transparent px-3 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none"
                />

                <button
                  type="submit"
                  disabled={!inputMensaje.trim() || estaEscribiendo}
                  className="bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-amber-400 p-2 sm:px-4 sm:py-2 rounded-xl text-xs font-bold transition-all duration-200 flex items-center gap-1.5 shadow-xs"
                >
                  <span>Enviar</span>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              </form>
            </div>

          </div>
        </main>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* VISTA 2: FORMULARIO DE AUTENTICACIÓN (LOGIN ADMIN)                     */}
      {/* -------------------------------------------------------------------- */}
      {vistaActual === 'login' && (
        <main className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200/80 shadow-md p-6 sm:p-8 space-y-6 animate-fadeIn">
            
            {/* Header del Login */}
            <div className="text-center space-y-2">
              <div className="w-12 h-14 bg-gradient-to-b from-red-600 to-red-800 rounded-xl p-1 mx-auto flex flex-col items-center justify-between border border-amber-400/40 shadow-xs">
                <span className="text-[10px] font-black text-amber-300">MDJLO</span>
                <svg className="w-6 h-6 text-amber-300 my-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>

              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Acceso Institucional</h2>
              <p className="text-xs text-slate-500">Panel Administrativo de Gestión del TUPA</p>
            </div>

            {errorLogin && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-xl flex items-center gap-2">
                <span>⚠️</span>
                <span>{errorLogin}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Usuario Administrativo</label>
                <input
                  type="text"
                  required
                  value={credenciales.usuario}
                  onChange={(e) => setCredenciales({ ...credenciales, usuario: e.target.value })}
                  placeholder="Ej. admin_jlo"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Contraseña</label>
                <input
                  type="password"
                  required
                  value={credenciales.password}
                  onChange={(e) => setCredenciales({ ...credenciales, password: e.target.value })}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition"
                />
              </div>

              <button
                type="submit"
                disabled={cargandoLogin}
                className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-amber-400 font-bold rounded-xl text-xs sm:text-sm shadow-xs transition-all duration-200 flex items-center justify-center gap-2"
              >
                {cargandoLogin ? 'Verificando...' : 'Iniciar Sesión'}
              </button>
            </form>

            <div className="pt-2 text-center border-t border-slate-100">
              <button
                onClick={() => setVistaActual('ciudadano')}
                className="text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
              >
                ← Volver a Atención Ciudadana
              </button>
            </div>

          </div>
        </main>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* VISTA 3: DASHBOARD CRUD DE ADMINISTRACIÓN                            */}
      {/* -------------------------------------------------------------------- */}
      {vistaActual === 'admin' && adminAutenticado && (
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
          
          {/* Header Interno del Dashboard */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-md bg-amber-100 text-amber-900 font-bold text-[10px] uppercase">Panel Admin</span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs text-slate-500 font-medium">Gestión del Catálogo TUPA</span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight mt-1">
                Trámites y Requisitos Registrados
              </h2>
            </div>

            <div className="flex items-center gap-3 self-stretch md:self-auto justify-end">
              <button
                onClick={abrirModalNuevo}
                className="px-4 py-2 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold text-xs rounded-xl shadow-xs transition-all flex items-center gap-1.5"
              >
                <span>+ Nuevo Trámite</span>
              </button>

              <button
                onClick={() => {
                  setAdminAutenticado(false);
                  setVistaActual('ciudadano');
                }}
                className="px-3 py-2 bg-slate-100 hover:bg-red-50 hover:text-red-700 text-slate-600 font-semibold text-xs rounded-xl transition"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>

          {/* Barra de Filtro / Búsqueda en Tabla */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
            <div className="relative">
              <input
                type="text"
                value={busquedaAdmin}
                onChange={(e) => setBusquedaAdmin(e.target.value)}
                placeholder="Buscar por código de trámite (ej. T_001) o nombre del procedimiento..."
                className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
              />
              <svg className="w-4 h-4 text-slate-400 absolute left-3 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          {/* Tabla de Datos (Data Table Sin Líneas Verticales) */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200/80 text-slate-500 font-semibold uppercase text-[11px] tracking-wider">
                    <th className="py-3.5 px-4">Código</th>
                    <th className="py-3.5 px-4">Nombre del Trámite</th>
                    <th className="py-3.5 px-4">Costo</th>
                    <th className="py-3.5 px-4">Plazo</th>
                    <th className="py-3.5 px-4">Requisitos</th>
                    <th className="py-3.5 px-4 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-800">
                  {tramitesFiltrados.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="text-center py-8 text-slate-400 text-xs">
                        No se encontraron trámites registrados con la búsqueda dada.
                      </td>
                    </tr>
                  ) : (
                    tramitesFiltrados.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-bold text-slate-900">{t.id_tramite}</td>
                        <td className="py-3.5 px-4 font-medium max-w-xs">{t.nombre}</td>
                        <td className="py-3.5 px-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
                            {t.costo || 'Gratuito'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 text-blue-800 border border-blue-200 text-xs font-semibold">
                            {t.plazo || 'Inmediato'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-500 max-w-xs truncate">
                          {t.requisitos ? `${t.requisitos.length} requisitos` : '0 requisitos'}
                        </td>
                        <td className="py-3.5 px-4 text-right space-x-1">
                          <button
                            onClick={() => abrirModalEditar(t)}
                            className="px-2.5 py-1 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg text-xs font-semibold transition"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => eliminarTramite(t.id)}
                            className="px-2.5 py-1 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg text-xs font-semibold transition"
                          >
                            Eliminar
                          </button>
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

      {/* -------------------------------------------------------------------- */}
      {/* BOTÓN FLOTANTE DEL CHATBOT (Siempre Accesible)                         */}
      {/* -------------------------------------------------------------------- */}
      <div className="fixed bottom-5 right-5 z-50">
        <button
          onClick={() => setChatFlotanteAbierto(!chatFlotanteAbierto)}
          className="w-14 h-14 bg-slate-900 hover:bg-slate-800 text-amber-400 rounded-full shadow-lg border-2 border-amber-400/40 flex items-center justify-center transition-all duration-300 hover:scale-105"
        >
          <span className="text-xl">🤖</span>
        </button>

        {/* Modal / Widget Ventana Flotante */}
        {chatFlotanteAbierto && (
          <div className="absolute bottom-16 right-0 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col h-[450px] animate-scaleUp">
            <div className="bg-slate-900 text-white p-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-amber-400 font-bold">Leonardito</span>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded">TUPA MDJLO</span>
              </div>
              <button onClick={() => setChatFlotanteAbierto(false)} className="text-slate-400 hover:text-white text-sm font-bold">✕</button>
            </div>

            <div className="flex-1 p-3 overflow-y-auto space-y-3 text-xs">
              {mensajes.map((m) => (
                <div key={m.id} className={`flex ${m.rol === 'usuario' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`rounded-xl p-2.5 max-w-[85%] ${m.rol === 'usuario' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-800'}`}>
                    {m.texto}
                  </div>
                </div>
              ))}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                enviarMensaje();
              }}
              className="p-2 border-t border-slate-100 flex gap-1"
            >
              <input
                type="text"
                value={inputMensaje}
                onChange={(e) => setInputMensaje(e.target.value)}
                placeholder="Escribe tu consulta..."
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 text-xs focus:outline-none"
              />
              <button type="submit" className="bg-slate-900 text-amber-400 px-3 py-1.5 rounded-xl text-xs font-bold">
                Enviar
              </button>
            </form>
          </div>
        )}
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* MODAL EDITAR / CREAR TRÁMITE                                         */}
      {/* -------------------------------------------------------------------- */}
      {modalTramiteAbierto && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4 animate-scaleUp">
            <h3 className="font-bold text-lg text-slate-900 border-b border-slate-100 pb-2">
              {tramiteEnEdicion ? 'Editar Trámite del TUPA' : 'Registrar Nuevo Trámite'}
            </h3>

            <form onSubmit={guardarTramite} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Código del Trámite</label>
                <input
                  type="text"
                  required
                  value={formTramite.id_tramite}
                  onChange={(e) => setFormTramite({ ...formTramite, id_tramite: e.target.value })}
                  placeholder="Ej. T_001"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Nombre del Procedimiento</label>
                <input
                  type="text"
                  required
                  value={formTramite.nombre}
                  onChange={(e) => setFormTramite({ ...formTramite, nombre: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Costo (S/)</label>
                  <input
                    type="text"
                    value={formTramite.costo}
                    onChange={(e) => setFormTramite({ ...formTramite, costo: e.target.value })}
                    placeholder="Ej. S/ 185.50 o Gratuito"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Plazo de Atención</label>
                  <input
                    type="text"
                    value={formTramite.plazo}
                    onChange={(e) => setFormTramite({ ...formTramite, plazo: e.target.value })}
                    placeholder="Ej. 3 días hábiles"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalTramiteAbierto(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold rounded-xl shadow-xs"
                >
                  Guardar Trámite
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* FOOTER INSTITUCIONAL                                                 */}
      {/* -------------------------------------------------------------------- */}
      <footer className="bg-slate-900 text-slate-400 text-xs py-6 border-t border-slate-800 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>© 2026 Municipalidad Distrital de José Leonardo Ortiz. Todos los derechos reservados.</p>
          <div className="flex items-center space-x-4 text-[11px]">
            <span>TUPA Vigente</span>
            <span>•</span>
            <span>Mesa de Partes Virtual</span>
            <span>•</span>
            <span className="text-amber-400 font-semibold">Sistema Inteligente NLP</span>
          </div>
        </div>
      </footer>

    </div>
  );
}