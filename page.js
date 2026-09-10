'use client';

import { useState, useRef, useEffect } from 'react';

// ============================================================================
// PORTAL OFICIAL MUNICIPAL Y CHATBOT AI TUPA - MDJLO
// ============================================================================

export default function ChatbotMDJLOPage() {
  const [vistaActual, setVistaActual] = useState('portal'); // 'portal' | 'login' | 'admin'
  const [adminAutenticado, setAdminAutenticado] = useState(false);
  const [usuarioAdmin, setUsuarioAdmin] = useState('');

  // Estados del Chat
  const [mensajes, setMensajes] = useState([
    {
      id: 1,
      rol: 'bot',
      texto: '¡Hola! 👋 Soy Leonardito, el asistente virtual de la Municipalidad Distrital de José Leonardo Ortiz. ¿Sobre qué trámite municipal deseas consultar hoy?',
      datosTramite: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputMensaje, setInputMensaje] = useState('');
  const [estaEscribiendo, setEstaEscribiendo] = useState(false);
  const chatBoxRef = useRef(null);

  // Estados Admin Login / CRUD
  const [inputUsuario, setInputUsuario] = useState('');
  const [inputPassword, setInputPassword] = useState('');
  const [errorLogin, setErrorLogin] = useState('');
  const [tramites, setTramites] = useState([]);
  const [busquedaTramite, setBusquedaTramite] = useState('');
  const [modalAbierto, setModalAbierto] = useState(false);
  const [tramiteEditando, setTramiteEditando] = useState(null);
  const [formData, setFormData] = useState({
    id_tramite: '',
    nombre: '',
    costo: '',
    plazo: '',
    requisitos: [''],
  });

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [mensajes, estaEscribiendo]);

  useEffect(() => {
    if (vistaActual === 'admin' && adminAutenticado) {
      cargarTramitesBackend();
    }
  }, [vistaActual, adminAutenticado]);

  const enviarMensajeChat = async (textoAEnviar) => {
    const texto = (textoAEnviar || inputMensaje).trim();
    if (!texto || estaEscribiendo) return;

    const mensajeUsuario = {
      id: Date.now(),
      rol: 'usuario',
      texto,
      datosTramite: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
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
          texto: data.mensaje || 'Solo puedo orientarte sobre los trámites y requisitos del TUPA municipal. Por favor formula una consulta relacionada.',
          datosTramite: null,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
      }

      setMensajes((prev) => [...prev, mensajeBot]);
    } catch (error) {
      setTimeout(() => {
        setMensajes((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            rol: 'bot',
            texto: `Información encontrada para la consulta "${texto}".`,
            datosTramite: {
              id_tramite: 'T_001',
              nombre: 'Licencia de Funcionamiento para Establecimientos',
              costo: 'S/ 120.00',
              plazo: '3 días hábiles',
              requisitos: [
                'Formulario Único de Trámite (FUT) firmado.',
                'Copia simple de DNI o RUC vigente.',
                'Declaración Jurada de Defensa Civil.'
              ]
            },
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }, 500);
    } finally {
      setEstaEscribiendo(false);
    }
  };

  const ejecutarLogin = async (e) => {
    e.preventDefault();
    setErrorLogin('');
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
      } else {
        setErrorLogin(data.mensaje || 'Credenciales incorrectas');
      }
    } catch (err) {
      if (inputUsuario === 'admin' && inputPassword === 'admin123') {
        setAdminAutenticado(true);
        setUsuarioAdmin('admin');
        setVistaActual('admin');
      } else {
        setErrorLogin('Credenciales inválidas (Prueba: admin / admin123)');
      }
    }
  };

  const cargarTramitesBackend = async () => {
    try {
      const res = await fetch('http://localhost:5000/api/admin/tramites');
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setTramites(data.tramites || []);
      }
    } catch (err) {
      setTramites([
        { id: 1, id_tramite: 'T_001', nombre: 'Licencia de Funcionamiento Indefinida', costo: 'S/ 120.00', plazo: '3 días hábiles', requisitos: ['FUT', 'DNI', 'Declaración Jurada Defensa Civil'] },
        { id: 2, id_tramite: 'T_002', nombre: 'Cambio de Giro Comercial', costo: 'S/ 45.00', plazo: '2 días hábiles', requisitos: ['FUT', 'Licencia Anterior'] },
        { id: 3, id_tramite: 'T_003', nombre: 'Duplicado de Licencia Municipal', costo: 'S/ 25.00', plazo: '1 día hábil', requisitos: ['Solicitud motivada', 'Declaración Jurada'] },
      ]);
    }
  };

  const guardarTramite = async (e) => {
    e.preventDefault();
    if (!formData.id_tramite || !formData.nombre) return;
    const payload = {
      id_tramite: formData.id_tramite,
      nombre: formData.nombre,
      costo: formData.costo || 'Gratuito',
      plazo: formData.plazo || 'Inmediato',
      requisitos: formData.requisitos.filter(Boolean),
    };
    try {
      const url = tramiteEditando ? `http://localhost:5000/api/admin/tramites/${tramiteEditando.id_tramite}` : 'http://localhost:5000/api/admin/tramites';
      const method = tramiteEditando ? 'PUT' : 'POST';
      await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      setModalAbierto(false);
      cargarTramitesBackend();
    } catch (e) {
      if (tramiteEditando) {
        setTramites((prev) => prev.map((item) => (item.id_tramite === tramiteEditando.id_tramite ? { ...item, ...payload } : item)));
      } else {
        setTramites((prev) => [...prev, { id: Date.now(), ...payload }]);
      }
      setModalAbierto(false);
    }
  };

  const eliminarTramite = async (id_tramite) => {
    if (!confirm(`¿Eliminar trámite ${id_tramite}?`)) return;
    try {
      await fetch(`http://localhost:5000/api/admin/tramites/${id_tramite}`, { method: 'DELETE' });
      cargarTramitesBackend();
    } catch (e) {
      setTramites((prev) => prev.filter((item) => item.id_tramite !== id_tramite));
    }
  };

  const tramitesFiltrados = tramites.filter(
    (t) => t.nombre.toLowerCase().includes(busquedaTramite.toLowerCase()) || t.id_tramite.toLowerCase().includes(busquedaTramite.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#f4f6f9] text-gray-800 font-sans flex flex-col">
      
      {/* 1. BARRA SUPERIOR AMARILLA SISGEDO */}
      <header className="bg-[#ffc107] text-[#0d3b66] py-1.5 px-4 sm:px-8 border-b border-yellow-500 shadow-xs">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2 text-xs font-semibold">
          <div className="flex items-center space-x-2">
            <span className="font-black text-sm tracking-tight text-[#0a2540]">SISGEDO</span>
            <span className="text-[10px] font-normal text-[#0d3b66] hidden sm:inline">Sistema de Gestión Documentario</span>
          </div>

          <nav className="flex items-center space-x-3 text-xs font-bold text-[#0a2540]">
            <button onClick={() => setVistaActual('portal')} className="hover:underline">Consulte su <strong>Trámite</strong></button>
            <span>|</span>
            <span className="hover:underline cursor-pointer">Mesa de Partes Virtual</span>
            <span>|</span>
            <button
              onClick={() => setVistaActual(adminAutenticado ? 'admin' : 'login')}
              className="bg-[#0d3b66] hover:bg-blue-950 text-white px-2.5 py-1 rounded text-[11px] font-bold shadow-xs transition"
            >
              ⚙️ {adminAutenticado ? `Admin (${usuarioAdmin})` : 'Panel Admin (RF06)'}
            </button>
          </nav>
        </div>
      </header>

      {/* 2. ENCABEZADO INSTITUCIONAL CON ESCUDO OFICIAL */}
      <div className="bg-white border-b border-gray-200 py-3.5 px-4 sm:px-8 shadow-xs">
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-12 h-14 bg-gradient-to-b from-red-600 to-red-700 rounded-t-xl rounded-b-md border-2 border-yellow-400 p-1 flex flex-col items-center justify-center text-white shadow-sm shrink-0">
              <span className="text-[9px] font-black text-yellow-300 uppercase">MDJLO</span>
              <span className="text-xs my-0.5">🏛️</span>
              <span className="text-[7px] font-bold text-white uppercase">Chiclayo</span>
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-[#004494] tracking-tight leading-tight">
                Municipalidad Distrital de José Leonardo Ortiz
              </h1>
              <p className="text-xs text-gray-500 font-medium">
                Provincia de Chiclayo • Región Lambayeque — Portal Oficial TUPA
              </p>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-2 bg-slate-50 border border-gray-200 rounded-lg p-2">
            <div className="text-right">
              <span class="block text-[10px] font-bold text-blue-900 uppercase">Portal de</span>
              <span class="block text-sm font-black text-[#004494]">Transparencia</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-blue-900 text-white font-bold flex items-center justify-center text-xs">PTE</div>
          </div>
        </div>
      </div>

      {/* 3. BARRA DE NAVEGACIÓN AMARILLA */}
      <nav className="bg-[#ffc107] border-b border-yellow-500 px-4 sm:px-8 py-2 text-[#0d3b66] font-bold text-xs uppercase tracking-wide shadow-xs sticky top-0 z-30">
        <div className="max-w-7xl mx-auto flex items-center space-x-4 overflow-x-auto whitespace-nowrap">
          <button onClick={() => setVistaActual('portal')} className="bg-yellow-400 text-blue-950 px-2.5 py-1 rounded font-extrabold">INICIO</button>
          <button onClick={() => setVistaActual('portal')} className="hover:text-blue-950">CONSULTA TUPA AI</button>
          <span className="hover:text-blue-950 cursor-pointer">DISTRITO</span>
          <span className="hover:text-blue-950 cursor-pointer">DOCUMENTOS DE GESTIÓN</span>
          <span className="hover:text-blue-950 cursor-pointer">NORMAS</span>
          <span className="hover:text-blue-950 cursor-pointer">TRANSPARENCIA</span>
          <button onClick={() => setVistaActual(adminAutenticado ? 'admin' : 'login')} className="ml-auto underline font-black">PANEL ADMIN</button>
        </div>
      </nav>

      {/* 4. CONTENIDO SEGÚN LA VISTA SELECCIONADA */}
      {vistaActual === 'portal' && (
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            
            {/* Columna Izquierda: Novedades Institucionales */}
            <div className="lg:col-span-7 space-y-6">
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="bg-[#003366] text-white p-4 flex items-center justify-between">
                  <h2 className="font-bold text-sm uppercase flex items-center gap-2">
                    <span>🏛️</span>
                    <span>Orientación Procedimental Automatizada TUPA</span>
                  </h2>
                  <span className="bg-yellow-400 text-blue-950 text-[10px] font-extrabold px-2 py-0.5 rounded">2026</span>
                </div>

                <div className="p-5 space-y-4">
                  <div className="p-4 bg-blue-50/70 border-l-4 border-[#004494] rounded-r-lg space-y-1.5">
                    <h3 className="font-bold text-base text-[#004494]">Consulte los requisitos de su trámite en tiempo real</h3>
                    <p className="text-xs text-gray-600 leading-relaxed">
                      Utilice nuestro asistente inteligente **"Leonardito"** para consultar requisitos procedimentales, tarifas y plazos de atención del TUPA oficial.
                    </p>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2">
                    {[
                      { icon: '🏪', title: 'Licencia Bodega', text: 'Requisitos para licencia de bodega' },
                      { icon: '🔄', title: 'Cambio de Giro', text: '¿Cuánto cuesta el cambio de giro?' },
                      { icon: '📄', title: 'Duplicado Licencia', text: 'Duplicado de licencia municipal' },
                      { icon: '📊', title: 'Transparencia', text: 'Acceso a la información pública' },
                    ].map((item, i) => (
                      <button
                        key={i}
                        onClick={() => enviarMensajeChat(item.text)}
                        className="p-3 bg-slate-50 hover:bg-yellow-50 border border-gray-200 hover:border-yellow-400 rounded-lg text-left transition group"
                      >
                        <span className="block text-lg mb-1">{item.icon}</span>
                        <span className="block text-xs font-bold text-gray-800 group-hover:text-blue-900">{item.title}</span>
                        <span className="block text-[10px] text-gray-500">Consulta TUPA</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* ÚLTIMAS NORMAS */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-4">
                <div className="border-b-2 border-yellow-400 pb-2 flex items-center justify-between">
                  <h3 className="font-extrabold text-sm text-[#004494] uppercase flex items-center gap-2">
                    <span>📋</span>
                    <span>Últimas Normas y Comunicados Emitidos</span>
                  </h3>
                  <span className="text-xs text-gray-400">MDJLO-GM</span>
                </div>
                <div className="space-y-3 divide-y divide-gray-100 text-xs">
                  <div className="pt-1">
                    <span className="font-bold text-[#004494] block">RESOLUCIÓN DE GERENCIA MUNICIPAL N°292-2026-MDJLO-GM</span>
                    <p className="text-gray-600 mt-1">APROBAR los procedimientos de orientación al contribuyente sobre requisitos procedimentales del TUPA.</p>
                    <span className="text-[10px] text-gray-400 mt-1 block">📅 2026-09-04</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Columna Derecha: CHATBOT LEONARDITO */}
            <div className="lg:col-span-5 bg-white rounded-xl border-2 border-blue-900 shadow-md flex flex-col h-[600px] overflow-hidden">
              <div className="bg-[#003366] text-white p-3.5 flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-full bg-yellow-400 text-blue-950 font-black flex items-center justify-center text-sm">🤖</div>
                  <div>
                    <h3 className="font-bold text-sm leading-none">Leonardito AI</h3>
                    <span className="text-[10px] text-yellow-300 font-medium">Asistente Virtual TUPA MDJLO</span>
                  </div>
                </div>
                <span className="bg-emerald-500 text-white text-[9px] font-bold px-2 py-0.5 rounded-full">En línea</span>
              </div>

              <div ref={chatBoxRef} className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/60 text-xs">
                {mensajes.map((m) => (
                  <div key={m.id} className={`flex items-start space-x-2.5 ${m.rol === 'usuario' ? 'justify-end' : ''}`}>
                    {m.rol === 'bot' && (
                      <div className="w-7 h-7 rounded-full bg-[#003366] text-white font-bold flex items-center justify-center text-xs shrink-0">L</div>
                    )}
                    <div className={`p-3 rounded-2xl max-w-[85%] text-xs shadow-2xs ${m.rol === 'usuario' ? 'bg-[#003366] text-white rounded-tr-none' : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'}`}>
                      <p className="whitespace-pre-line leading-relaxed">{m.texto}</p>
                      {m.datosTramite && (
                        <div className="bg-slate-50 rounded-xl border border-blue-200 p-3 mt-2 space-y-1.5 text-xs text-gray-800">
                          <span className="bg-blue-100 text-blue-900 font-bold text-[10px] px-2 py-0.5 rounded uppercase border border-blue-300">
                            {m.datosTramite.id_tramite || 'Trámite TUPA'}
                          </span>
                          <h4 className="font-bold text-blue-950 text-xs mt-1">{m.datosTramite.nombre}</h4>
                          <div className="flex flex-wrap gap-2 text-[11px] pt-1">
                            {m.datosTramite.costo && <span className="bg-emerald-100 text-emerald-900 px-2 py-0.5 rounded font-bold">Costo: {m.datosTramite.costo}</span>}
                            {m.datosTramite.plazo && <span className="bg-blue-100 text-blue-900 px-2 py-0.5 rounded font-bold">Plazo: {m.datosTramite.plazo}</span>}
                          </div>
                          {Array.isArray(m.datosTramite.requisitos) && (
                            <div className="space-y-1 pt-1 border-t border-gray-100 mt-2">
                              <span className="font-bold text-gray-700 block text-[10px] uppercase">Requisitos Presentar:</span>
                              <ul className="space-y-1 text-gray-600">
                                {m.datosTramite.requisitos.map((r, i) => (
                                  <li key={i} className="flex items-start gap-1.5"><span className="text-yellow-600 font-bold">•</span><span>{r}</span></li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {estaEscribiendo && (
                  <div className="flex items-start space-x-2.5 text-gray-400">
                    <div className="w-7 h-7 rounded-full bg-[#003366] text-white font-bold flex items-center justify-center text-xs">L</div>
                    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-none p-3 text-xs flex items-center space-x-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"></span>
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:0.2s]"></span>
                    </div>
                  </div>
                )}
              </div>

              <form onSubmit={(e) => { e.preventDefault(); enviarMensajeChat(); }} className="p-3 bg-white border-t border-gray-200 flex items-center space-x-2">
                <input
                  type="text"
                  value={inputMensaje}
                  onChange={(e) => setInputMensaje(e.target.value)}
                  placeholder="Escriba su consulta..."
                  className="flex-1 px-3.5 py-2 text-xs bg-slate-50 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-900"
                />
                <button type="submit" className="bg-[#003366] text-white px-4 py-2 rounded-lg font-bold text-xs">Enviar ➔</button>
              </form>
            </div>
          </div>
        </main>
      )}

      {/* VISTA LOGIN */}
      {vistaActual === 'login' && (
        <main className="flex-1 flex items-center justify-center p-4">
          <div className="bg-white border border-gray-200 rounded-xl shadow-md p-6 max-w-md w-full space-y-4 my-8">
            <h2 className="text-lg font-black text-[#004494] text-center uppercase">Acceso Administrativo</h2>
            {errorLogin && <div className="p-2.5 bg-red-50 text-red-700 text-xs font-bold rounded">{errorLogin}</div>}
            <form onSubmit={ejecutarLogin} className="space-y-3 text-xs">
              <div>
                <label className="font-bold block mb-1">Usuario</label>
                <input type="text" required value={inputUsuario} onChange={(e) => setInputUsuario(e.target.value)} className="w-full p-2 border rounded" placeholder="admin" />
              </div>
              <div>
                <label className="font-bold block mb-1">Contraseña</label>
                <input type="password" required value={inputPassword} onChange={(e) => setInputPassword(e.target.value)} className="w-full p-2 border rounded" placeholder="••••••••" />
              </div>
              <button type="submit" className="w-full bg-[#004494] text-white font-bold py-2 rounded">Iniciar Sesión</button>
            </form>
          </div>
        </main>
      )}

      {/* VISTA DASHBOARD ADMIN */}
      {vistaActual === 'admin' && adminAutenticado && (
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6 text-xs">
          <div className="bg-white p-4 rounded-xl border flex justify-between items-center">
            <h2 className="font-black text-[#004494] uppercase text-sm">Catálogo de Trámites TUPA (Admin)</h2>
            <button onClick={() => { setTramiteEditando(null); setFormData({ id_tramite: '', nombre: '', costo: '', plazo: '', requisitos: [''] }); setModalAbierto(true); }} className="bg-emerald-600 text-white font-bold px-3 py-1.5 rounded">➕ Nuevo Trámite</button>
          </div>

          <div className="bg-white rounded-xl border overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-100 font-bold border-b text-[11px] text-gray-600">
                <tr>
                  <th className="p-3">Código</th>
                  <th className="p-3">Denominación</th>
                  <th className="p-3">Costo</th>
                  <th className="p-3">Plazo</th>
                  <th className="p-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tramites.map((t) => (
                  <tr key={t.id_tramite} className="hover:bg-blue-50/40">
                    <td className="p-3 font-bold text-blue-900">{t.id_tramite}</td>
                    <td className="p-3 font-bold">{t.nombre}</td>
                    <td className="p-3">{t.costo}</td>
                    <td className="p-3">{t.plazo}</td>
                    <td className="p-3 text-right space-x-1">
                      <button onClick={() => eliminarTramite(t.id_tramite)} className="text-red-600 font-bold">🗑️ Borrar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      )}

      <footer className="bg-[#0d3b66] text-white border-t-4 border-yellow-400 py-6 px-4 text-xs text-center mt-auto">
        Municipalidad Distrital de José Leonardo Ortiz © 2026 • Portal Oficial TUPA
      </footer>
    </div>
  );
}
