'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';

export default function AdminTramitesPage() {
  // ---------------------------------------------------------------------------
  // ---------------------------------------------------------------------------
  // Estados de Autenticación (Requeridos: isAuthenticated y currentUser)
  // ---------------------------------------------------------------------------
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState('');
  const [loginUsuario, setLoginUsuario] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Estados de datos y carga
  // ---------------------------------------------------------------------------
  const [tramites, setTramites] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [busqueda, setBusqueda] = useState('');
  const [alerta, setAlerta] = useState(null); // { tipo: 'exito' | 'error', mensaje: string }

  // Estados del Modal de Creación / Edición
  const [modalAbierto, setModalAbierto] = useState(false);
  const [modoEdicion, setModoEdicion] = useState(false);
  const [guardando, setGuardando] = useState(false);

  // Formulario del trámite
  const [formData, setFormData] = useState({
    id: null,
    id_tramite: '',
    nombre: '',
    costo: '',
    plazo: '',
    requisitosTexto: '',
  });

  // Estado del Modal de Confirmación para Eliminar
  const [tramiteAEliminar, setTramiteAEliminar] = useState(null);
  const [eliminando, setEliminando] = useState(false);

  // Estado para expandir requisitos en la tabla
  const [requisitosExpandidos, setRequisitosExpandidos] = useState({});

  const API_URL = 'http://localhost:5000/api/admin/tramites';
  const API_LOGIN_URL = 'http://localhost:5000/api/admin/login';

  // ---------------------------------------------------------------------------
  // Utilidad para mostrar alertas automáticas
  // ---------------------------------------------------------------------------
  const mostrarAlerta = (tipo, mensaje) => {
    setAlerta({ tipo, mensaje });
    setTimeout(() => {
      setAlerta((prev) => (prev?.mensaje === mensaje ? null : prev));
    }, 4500);
  };

  // ---------------------------------------------------------------------------
  // 1. GET: Cargar todos los trámites desde el backend
  // ---------------------------------------------------------------------------
  const cargarTramites = async () => {
    setCargando(true);
    try {
      const res = await fetch(API_URL, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();

      if (res.ok && data.status === 'success') {
        setTramites(data.tramites || []);
      } else {
        const errorMsg = data.mensaje || 'Error al obtener la lista de trámites.';
        mostrarAlerta('error', errorMsg);
      }
    } catch (err) {
      console.error('Error al consultar /api/admin/tramites:', err);
      mostrarAlerta(
        'error',
        'No se pudo conectar con el servidor Flask (http://localhost:5000). Verifica que app.py esté en ejecución.'
      );
    } finally {
      setCargando(false);
    }
  };

  // Autenticación en sessionStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedUser = sessionStorage.getItem('admin_user');
      if (savedUser) {
        setIsAuthenticated(true);
        setCurrentUser(savedUser);
        cargarTramites();
      }
    }
  }, []);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);

    try {
      const res = await fetch(API_LOGIN_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usuario: loginUsuario.trim(), password: loginPassword.trim() }),
      });

      const data = await res.json();

      if (res.status === 200 && (data.username || data.status === 'success')) {
        const username = data.username || loginUsuario.trim();
        setCurrentUser(username);
        setIsAuthenticated(true);
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('admin_user', username);
        }
        cargarTramites();
      } else if (res.status === 401) {
        setLoginError(data.mensaje || 'Usuario o contraseña incorrectos');
      } else {
        setLoginError(data.mensaje || 'Error al autenticar credenciales');
      }
    } catch (err) {
      console.error('Error al conectar con login:', err);
      setLoginError('Error de conexión con el backend (http://localhost:5000).');
    } finally {
      setLoginLoading(false);
    }
  };

  const cerrarSesion = () => {
    setIsAuthenticated(false);
    setCurrentUser('');
    setLoginPassword('');
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('admin_user');
    }
  };

  // ---------------------------------------------------------------------------
  // Manejadores para abrir y cerrar el Modal (Crear / Editar)
  // ---------------------------------------------------------------------------
  const abrirModalCrear = () => {
    setModoEdicion(false);
    setFormData({
      id: null,
      id_tramite: '',
      nombre: '',
      costo: 'Gratuito',
      plazo: 'Inmediato',
      requisitosTexto: '',
    });
    setModalAbierto(true);
  };

  const abrirModalEditar = (tramite) => {
    setModoEdicion(true);
    setFormData({
      id: tramite.id,
      id_tramite: tramite.id_tramite || '',
      nombre: tramite.nombre || '',
      costo: tramite.costo || '',
      plazo: tramite.plazo || '',
      requisitosTexto: Array.isArray(tramite.requisitos) ? tramite.requisitos.join('\n') : '',
    });
    setModalAbierto(true);
  };

  const cerrarModal = () => {
    if (!guardando) {
      setModalAbierto(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 2. POST / PUT: Guardar Trámite
  // ---------------------------------------------------------------------------
  const guardarTramite = async (e) => {
    e.preventDefault();

    const idTramiteLimpio = formData.id_tramite.trim();
    const nombreLimpio = formData.nombre.trim();

    if (!idTramiteLimpio) {
      mostrarAlerta('error', 'El código de trámite (ej. T_015) es obligatorio.');
      return;
    }
    if (!nombreLimpio) {
      mostrarAlerta('error', 'El nombre del trámite es obligatorio.');
      return;
    }

    // Procesar los requisitos divididos por salto de línea
    const requisitosArray = formData.requisitosTexto
      .split('\n')
      .map((linea) => linea.trim())
      .filter((linea) => linea.length > 0);

    const payload = {
      id_tramite: idTramiteLimpio,
      nombre: nombreLimpio,
      costo: formData.costo.trim() || 'Gratuito',
      plazo: formData.plazo.trim() || 'Inmediato',
      requisitos: requisitosArray,
    };

    setGuardando(true);

    try {
      const url = modoEdicion
        ? `${API_URL}/${formData.id || formData.id_tramite}`
        : API_URL;

      const metodo = modoEdicion ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method: metodo,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.ok && data.status === 'success') {
        mostrarAlerta(
          'exito',
          data.mensaje ||
            (modoEdicion
              ? 'Trámite actualizado correctamente.'
              : 'Nuevo trámite registrado con éxito.')
        );
        setModalAbierto(false);
        await cargarTramites();
      } else {
        mostrarAlerta('error', data.mensaje || 'Error al procesar la solicitud.');
      }
    } catch (err) {
      console.error('Error al guardar trámite:', err);
      mostrarAlerta('error', 'Ocurrió un fallo de conexión al intentar guardar.');
    } finally {
      setGuardando(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 3. DELETE: Eliminar Trámite
  // ---------------------------------------------------------------------------
  const confirmarEliminar = async () => {
    if (!tramiteAEliminar) return;

    setEliminando(true);
    try {
      const idParaEliminar = tramiteAEliminar.id || tramiteAEliminar.id_tramite;
      const res = await fetch(`${API_URL}/${idParaEliminar}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await res.json();

      if (res.ok && data.status === 'success') {
        mostrarAlerta(
          'exito',
          data.mensaje || `Trámite ${tramiteAEliminar.id_tramite} eliminado exitosamente.`
        );
        setTramiteAEliminar(null);
        await cargarTramites();
      } else {
        mostrarAlerta('error', data.mensaje || 'No se pudo eliminar el trámite.');
      }
    } catch (err) {
      console.error('Error al eliminar trámite:', err);
      mostrarAlerta('error', 'Fallo de red al intentar eliminar el trámite.');
    } finally {
      setEliminando(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Alternar vista previa de requisitos en fila de tabla
  // ---------------------------------------------------------------------------
  const toggleRequisitosFila = (id) => {
    setRequisitosExpandidos((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  // ---------------------------------------------------------------------------
  // Filtro y Estadísticas
  // ---------------------------------------------------------------------------
  const tramitesFiltrados = useMemo(() => {
    if (!busqueda.trim()) return tramites;
    const q = busqueda.toLowerCase();
    return tramites.filter(
      (t) =>
        t.id_tramite?.toLowerCase().includes(q) ||
        t.nombre?.toLowerCase().includes(q) ||
        t.costo?.toLowerCase().includes(q)
    );
  }, [tramites, busqueda]);

  const estadisticas = useMemo(() => {
    const total = tramites.length;
    const conCosto = tramites.filter(
      (t) => t.costo && !t.costo.toLowerCase().includes('grat') && t.costo.trim() !== 'S/ 0.00'
    ).length;
    const gratuitos = total - conCosto;
    const totalRequisitos = tramites.reduce(
      (acc, t) => acc + (Array.isArray(t.requisitos) ? t.requisitos.length : 0),
      0
    );
    return { total, conCosto, gratuitos, totalRequisitos };
  }, [tramites]);

  return (
    <div className="min-h-screen flex flex-col bg-[#f4f6f9] text-gray-800 font-sans">
      
      {/* --------------------------------------------------------------------- */}
      {/* 1. BARRA SUPERIOR INSTITUCIONAL AMARILLA (SISGEDO)                    */}
      {/* --------------------------------------------------------------------- */}
      <header className="bg-[#fbc02d] text-[#0d3b66] text-xs font-semibold py-1.5 px-4 sm:px-8 border-b border-yellow-500 shadow-sm">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-[#0d3b66]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <span className="font-black text-sm tracking-tight text-[#0a2540]">SISGEDO</span>
              <span className="ml-2 hidden sm:inline font-normal text-[#1e3a5f]">Sistema de Gestión Documentario y TUPA</span>
            </div>
          </div>

          <div className="flex items-center space-x-3 sm:space-x-5 text-xs text-[#0a2540]">
            <Link href="/" className="hover:underline flex items-center gap-1 font-bold">
              <span>🤖 Ir al Chatbot Ciudadano</span>
            </Link>
            <span className="text-yellow-600">|</span>
            <span className="font-extrabold bg-[#0d3b66] text-white px-2 py-0.5 rounded shadow-sm">
              Panel Admin (RF06)
            </span>
            {isAuthenticated && (
              <div className="flex items-center space-x-2 bg-white/90 border border-yellow-600 px-2 py-0.5 rounded text-xs shadow-xs">
                <span>👤 <strong className="text-[#0d3b66]">{currentUser}</strong></span>
                <button
                  onClick={cerrarSesion}
                  className="bg-red-600 hover:bg-red-700 text-white text-[10px] font-bold px-1.5 py-0.5 rounded transition cursor-pointer"
                >
                  Salir
                </button>
              </div>
            )}
          </div>

        </div>
      </header>

      {/* --------------------------------------------------------------------- */}
      {/* 2. ENCABEZADO INSTITUCIONAL BLANCO CON ESCUDO Y SELLO PTE             */}
      {/* --------------------------------------------------------------------- */}
      <div className="bg-white border-b border-gray-200 py-3 px-4 sm:px-8 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between flex-wrap gap-4">
          
          <div className="flex items-center space-x-4">
            {/* Escudo Distrital MDJLO */}
            <div className="w-14 h-16 sm:w-16 sm:h-20 bg-gradient-to-b from-amber-400 to-red-600 rounded-b-full p-0.5 shadow-md flex items-center justify-center flex-shrink-0">
              <div className="w-full h-full bg-white rounded-b-full flex flex-col items-center justify-center p-1 text-center">
                <span className="text-[7px] font-black text-red-700 leading-tight">MDJLO</span>
                <div className="w-6 h-6 rounded-full bg-blue-900 border border-amber-400 flex items-center justify-center my-0.5">
                  <span className="text-[9px] text-white font-bold">🏛️</span>
                </div>
                <span className="text-[6px] font-semibold text-gray-700 uppercase">Chiclayo</span>
              </div>
            </div>

            <div>
              <h1 className="text-xl sm:text-3xl font-extrabold text-[#113f8a] tracking-tight leading-tight drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">
                Municipalidad Distrital
              </h1>
              <h2 className="text-xl sm:text-3xl font-extrabold text-[#113f8a] tracking-tight leading-tight">
                de José Leonardo Ortiz
              </h2>
            </div>
          </div>

          <div className="flex items-center space-x-3">
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
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 3. BARRA DE NAVEGACIÓN AMARILLA INSTITUCIONAL                         */}
      {/* --------------------------------------------------------------------- */}
      <nav className="bg-[#fbc02d] border-b-2 border-yellow-600 px-4 sm:px-8 py-2 text-white font-bold text-xs uppercase tracking-wide shadow">
        <div className="max-w-7xl mx-auto flex items-center space-x-2 sm:space-x-4 overflow-x-auto whitespace-nowrap">
          <Link href="/" className="hover:text-[#0d3b66] transition-colors">
            INICIO
          </Link>
          <span className="text-yellow-200 font-normal">|</span>
          <Link href="/" className="hover:text-[#0d3b66] transition-colors">
            CHATBOT LEONARDITO
          </Link>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="text-[#0d3b66] bg-yellow-400/90 px-2 py-0.5 rounded shadow-sm border border-yellow-600">
            GESTIÓN DE TRÁMITES TUPA (ADMIN)
          </span>
          <span className="text-yellow-200 font-normal">|</span>
          <span className="hover:text-[#0d3b66] transition-colors cursor-pointer">
            DOCUMENTOS DE GESTIÓN
          </span>
        </div>
      </nav>

      {/* --------------------------------------------------------------------- */}
      {/* 4. CINTA NEGRA INSTITUCIONAL                                          */}
      {/* --------------------------------------------------------------------- */}
      <div className="bg-black text-white px-4 sm:px-8 py-1.5 flex items-center justify-between text-xs font-semibold">
        <div className="max-w-7xl mx-auto w-full flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="bg-[#113f8a] text-[10px] px-2 py-0.5 rounded text-yellow-300 font-extrabold uppercase">
              Módulo RF06
            </span>
            <span className="tracking-wide">PANEL DE CONTROL ADMINISTRATIVO — BASE DE DATOS TUPA</span>
          </div>
          <div className="text-[11px] text-gray-300 hidden sm:block">
            MySQL / SQLAlchemy REST API
          </div>
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 5. CONTENIDO PRINCIPAL                                                */}
      {/* --------------------------------------------------------------------- */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        
        {/* Notificación Flotante / Banner de Alerta */}
        {alerta && (
          <div
            className={`p-4 rounded-lg shadow-md border flex items-center justify-between transition-all ${
              alerta.tipo === 'exito'
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-red-50 border-red-300 text-red-900'
            }`}
          >
            <div className="flex items-center space-x-3">
              <span className="text-xl">
                {alerta.tipo === 'exito' ? '✅' : '⚠️'}
              </span>
              <span className="text-sm font-semibold">{alerta.mensaje}</span>
            </div>
            <button
              onClick={() => setAlerta(null)}
              className="text-gray-500 hover:text-gray-800 text-sm font-bold ml-4 p-1"
            >
              ✕
            </button>
          </div>
        )}

        {/* ------------------------------------------------------------------- */}
        {/* ESTADO 1: PANTALLA DE LOGIN (Si isAuthenticated es falso)           */}
        {/* ------------------------------------------------------------------- */}
        {!isAuthenticated ? (
          <div className="bg-slate-100 rounded-2xl p-6 sm:p-12 flex items-center justify-center my-6 min-h-[50vh]">
            <div className="bg-white border border-slate-200/90 rounded-2xl shadow-xl p-6 sm:p-8 max-w-md w-full animate-fadeIn">
              
              <div className="text-center mb-6">
                <div className="w-14 h-14 bg-blue-50 border border-blue-200 text-[#004494] rounded-2xl flex items-center justify-center mx-auto mb-3 text-2xl shadow-inner">
                  🔐
                </div>
                <h3 className="text-xl font-black text-slate-900 tracking-tight font-serif">
                  Acceso al Panel Administrativo
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Ingrese sus credenciales oficiales para gestionar el catálogo TUPA de la MDJLO.
                </p>
              </div>

              {loginError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs font-semibold flex items-center space-x-2">
                  <span className="text-base">⚠️</span>
                  <span>{loginError}</span>
                </div>
              )}

              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                    Usuario
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="admin"
                    value={loginUsuario}
                    onChange={(e) => setLoginUsuario(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3.5 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#004494] focus:bg-white transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                    Contraseña
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3.5 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#004494] focus:bg-white transition"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loginLoading}
                  className="w-full bg-[#004494] hover:bg-blue-800 text-white font-bold py-2.5 px-4 rounded-lg text-sm shadow-md hover:shadow-lg transition flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
                >
                  {loginLoading ? (
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  ) : (
                    <>
                      <span>Ingresar al Panel</span>
                      <span>→</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        ) : (
          <>
            {/* ----------------------------------------------------------------- */}
            {/* ESTADO 2: PANEL CRUD (Si isAuthenticated es verdadero)           */}
            {/* ----------------------------------------------------------------- */}
            {/* Título de Sección y Botón Primario */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-gray-300">
              <div>
                <h2 className="text-xl sm:text-2xl font-black text-gray-800 uppercase tracking-tight flex items-center gap-2">
              <span>Catálogo Maestro de Trámites y Procedimientos</span>
            </h2>
            <div className="w-56 h-1 bg-[#fbc02d] mt-1 rounded-full"></div>
            <p className="text-xs text-gray-600 mt-1">
              Administración de costos, plazos de atención y requisitos de cada procedimiento administrativo municipal.
            </p>
          </div>

          <button
            onClick={abrirModalCrear}
            className="bg-[#fbc02d] hover:bg-yellow-400 text-[#0d3b66] font-extrabold px-5 py-2.5 rounded-lg shadow-md hover:shadow-lg border-2 border-yellow-500 flex items-center justify-center gap-2 text-sm transition-all transform hover:-translate-y-0.5"
          >
            <svg className="w-5 h-5 text-[#0d3b66]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4" />
            </svg>
            <span>Añadir Nuevo Trámite</span>
          </button>
        </div>

        {/* Tarjetas de Métricas Institucionales */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 text-[#113f8a] flex items-center justify-center text-xl font-bold">
              📑
            </div>
            <div>
              <span className="text-[11px] text-gray-500 uppercase font-semibold block">Total Trámites</span>
              <span className="text-xl font-black text-[#113f8a]">{estadisticas.total}</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center text-xl font-bold">
              💰
            </div>
            <div>
              <span className="text-[11px] text-gray-500 uppercase font-semibold block">Con Pago / Tasa</span>
              <span className="text-xl font-black text-amber-700">{estadisticas.conCosto}</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center text-xl font-bold">
              🆓
            </div>
            <div>
              <span className="text-[11px] text-gray-500 uppercase font-semibold block">Gratuitos</span>
              <span className="text-xl font-black text-emerald-700">{estadisticas.gratuitos}</span>
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-800 flex items-center justify-center text-xl font-bold">
              📋
            </div>
            <div>
              <span className="text-[11px] text-gray-500 uppercase font-semibold block">Total Requisitos</span>
              <span className="text-xl font-black text-indigo-700">{estadisticas.totalRequisitos}</span>
            </div>
          </div>
        </div>

        {/* Barra de Búsqueda y Filtro */}
        <div className="bg-white p-4 rounded-lg border border-gray-300 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-96">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por código (T_001), nombre o costo..."
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-[#113f8a] focus:outline-none transition"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              onClick={cargarTramites}
              disabled={cargando}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3.5 py-2 rounded-lg text-xs font-bold border border-gray-300 flex items-center gap-1.5 transition disabled:opacity-50"
              title="Recargar trámites"
            >
              <svg className={`w-3.5 h-3.5 ${cargando ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>{cargando ? 'Actualizando...' : 'Refrescar'}</span>
            </button>
          </div>
        </div>

        {/* ------------------------------------------------------------------- */}
        {/* TABLA PRINCIPAL DE TRÁMITES (Consumiendo GET /api/admin/tramites)     */}
        {/* ------------------------------------------------------------------- */}
        <div className="bg-white rounded-lg border border-gray-300 shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gradient-to-r from-[#113f8a] to-[#1a5bb8] text-white text-xs uppercase font-extrabold tracking-wider border-b border-blue-900">
                  <th className="py-3.5 px-4 w-28">Código</th>
                  <th className="py-3.5 px-4">Denominación del Trámite</th>
                  <th className="py-3.5 px-4 w-36">Costo TUPA</th>
                  <th className="py-3.5 px-4 w-36">Plazo</th>
                  <th className="py-3.5 px-4 w-36 text-center">Requisitos</th>
                  <th className="py-3.5 px-4 w-44 text-center">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 text-sm">
                {cargando ? (
                  <tr>
                    <td colSpan="6" className="py-12 text-center text-gray-500">
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <div className="w-8 h-8 border-4 border-[#113f8a] border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-xs font-semibold text-gray-600">
                          Consultando trámites en MySQL...
                        </span>
                      </div>
                    </td>
                  </tr>
                ) : tramitesFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="py-12 text-center text-gray-500">
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <span className="text-3xl">📭</span>
                        <span className="text-sm font-bold text-gray-700">
                          No se encontraron trámites registrados.
                        </span>
                        <p className="text-xs text-gray-500">
                          {busqueda ? 'No hay coincidencias con tu búsqueda.' : 'Presiona "Añadir Nuevo Trámite" para registrar uno.'}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  tramitesFiltrados.map((t) => {
                    const estaExpandido = !!requisitosExpandidos[t.id || t.id_tramite];
                    const numRequisitos = Array.isArray(t.requisitos) ? t.requisitos.length : 0;

                    return (
                      <tr
                        key={t.id || t.id_tramite}
                        className="hover:bg-blue-50/40 transition-colors group"
                      >
                        {/* Código ID */}
                        <td className="py-3.5 px-4 font-mono font-black text-xs text-[#113f8a]">
                          <span className="bg-blue-100 text-[#0c3677] px-2 py-1 rounded border border-blue-200 shadow-xs">
                            {t.id_tramite}
                          </span>
                        </td>

                        {/* Nombre del Trámite */}
                        <td className="py-3.5 px-4 font-medium text-gray-900 leading-snug">
                          <div className="font-semibold text-sm text-[#0d3b66]">
                            {t.nombre}
                          </div>

                          {/* Vista expandida de los requisitos si está abierto */}
                          {estaExpandido && numRequisitos > 0 && (
                            <div className="mt-2.5 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5">
                              <span className="font-bold text-[#113f8a] uppercase tracking-wide block text-[10px]">
                                Requisitos registrados ({numRequisitos}):
                              </span>
                              <ul className="space-y-1">
                                {t.requisitos.map((req, idx) => (
                                  <li key={idx} className="flex items-start text-gray-700">
                                    <span className="w-1.5 h-1.5 rounded-full bg-[#fbc02d] border border-amber-600 mt-1.5 mr-2 flex-shrink-0"></span>
                                    <span>{req}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </td>

                        {/* Costo */}
                        <td className="py-3.5 px-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            t.costo && !t.costo.toLowerCase().includes('grat')
                              ? 'bg-amber-100 text-amber-900 border border-amber-200'
                              : 'bg-emerald-100 text-emerald-900 border border-emerald-200'
                          }`}>
                            {t.costo || 'Gratuito'}
                          </span>
                        </td>

                        {/* Plazo */}
                        <td className="py-3.5 px-4 text-xs font-semibold text-gray-700">
                          <span className="inline-flex items-center gap-1 bg-gray-100 px-2 py-1 rounded border border-gray-200">
                            ⏱️ {t.plazo || 'Inmediato'}
                          </span>
                        </td>

                        {/* Conteo de Requisitos con botón toggle */}
                        <td className="py-3.5 px-4 text-center">
                          <button
                            onClick={() => toggleRequisitosFila(t.id || t.id_tramite)}
                            className="inline-flex items-center gap-1 text-xs font-bold text-[#113f8a] hover:text-blue-900 bg-blue-50 hover:bg-blue-100 border border-blue-200 px-2.5 py-1 rounded-full transition"
                            title="Ver requisitos"
                          >
                            <span>📋 {numRequisitos}</span>
                            <span className="text-[10px]">
                              {estaExpandido ? '▲' : '▼'}
                            </span>
                          </button>
                        </td>

                        {/* Botones de Acción (Editar / Eliminar) */}
                        <td className="py-3.5 px-4 text-center">
                          <div className="flex items-center justify-center space-x-2">
                            {/* Botón Editar */}
                            <button
                              onClick={() => abrirModalEditar(t)}
                              className="bg-blue-50 hover:bg-[#113f8a] text-[#113f8a] hover:text-white border border-[#113f8a]/40 px-2.5 py-1 rounded-md text-xs font-bold transition-all shadow-xs flex items-center gap-1"
                              title="Editar datos del trámite"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                              <span>Editar</span>
                            </button>

                            {/* Botón Eliminar */}
                            <button
                              onClick={() => setTramiteAEliminar(t)}
                              className="bg-red-50 hover:bg-red-700 text-red-700 hover:text-white border border-red-300 px-2.5 py-1 rounded-md text-xs font-bold transition-all shadow-xs flex items-center gap-1"
                              title="Eliminar trámite"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                              <span>Eliminar</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pie de tabla con totalizadores */}
          <div className="bg-gray-50 border-t border-gray-200 px-4 py-2.5 text-xs text-gray-600 flex items-center justify-between">
            <span>
              Mostrando <strong className="text-gray-800">{tramitesFiltrados.length}</strong> de{' '}
              <strong className="text-gray-800">{tramites.length}</strong> trámites registrados.
            </span>
            <span className="text-[11px] text-gray-500 italic">
              Conexión directa: MySQL <code>municipal_db</code>
            </span>
          </div>
        </div>
        </>
        )}

      </main>

      {/* --------------------------------------------------------------------- */}
      {/* MODAL DE FORMULARIO (Crear / Editar Trámite con Textarea)              */}
      {/* --------------------------------------------------------------------- */}
      {modalAbierto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-2xl border border-gray-300 w-full max-w-2xl max-h-[92vh] flex flex-col overflow-hidden">
            
            {/* Cabecera del Modal con diseño azul y amarillo */}
            <div className="bg-gradient-to-r from-[#113f8a] to-[#1b509d] text-white p-4 border-b-4 border-[#fbc02d] flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-xl">
                  {modoEdicion ? '✏️' : '📄'}
                </span>
                <div>
                  <h3 className="font-extrabold text-base leading-tight">
                    {modoEdicion ? 'Editar Trámite Administrativo' : 'Registrar Nuevo Trámite TUPA'}
                  </h3>
                  <p className="text-[11px] text-blue-200">
                    {modoEdicion
                      ? `Modificando registro: ${formData.id_tramite}`
                      : 'Completa los campos requeridos para la base de datos municipal'}
                  </p>
                </div>
              </div>
              <button
                onClick={cerrarModal}
                disabled={guardando}
                className="text-blue-200 hover:text-white text-xl font-bold p-1 rounded transition disabled:opacity-50"
              >
                ✕
              </button>
            </div>

            {/* Formulario */}
            <form onSubmit={guardarTramite} className="flex-1 overflow-y-auto p-5 space-y-4">
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Código de Trámite */}
                <div className="sm:col-span-1">
                  <label className="block text-xs font-bold text-gray-700 uppercase mb-1">
                    Código Trámite *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.id_tramite}
                    onChange={(e) =>
                      setFormData({ ...formData, id_tramite: e.target.value.toUpperCase() })
                    }
                    placeholder="Ej. T_015"
                    className="w-full font-mono text-sm px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#113f8a] focus:outline-none bg-gray-50 uppercase"
                  />
                  <span className="text-[10px] text-gray-500">Debe ser único en el sistema.</span>
                </div>

                {/* Denominación / Nombre del Trámite */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-gray-700 uppercase mb-1">
                    Nombre Oficial del Trámite *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.nombre}
                    onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                    placeholder="Ej. Licencia de Funcionamiento para Bodega"
                    className="w-full text-sm px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#113f8a] focus:outline-none"
                  />
                </div>
              </div>

              {/* Costo y Plazo */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase mb-1">
                    Costo TUPA (o Gratuito)
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500 text-xs">
                      💰
                    </span>
                    <input
                      type="text"
                      value={formData.costo}
                      onChange={(e) => setFormData({ ...formData, costo: e.target.value })}
                      placeholder="Ej. S/ 150.00 o Gratuito"
                      className="w-full text-sm pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#113f8a] focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase mb-1">
                    Plazo de Atención
                  </label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500 text-xs">
                      ⏱️
                    </span>
                    <input
                      type="text"
                      value={formData.plazo}
                      onChange={(e) => setFormData({ ...formData, plazo: e.target.value })}
                      placeholder="Ej. 7 días hábiles o Inmediato"
                      className="w-full text-sm pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#113f8a] focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Área de Texto para Requisitos (Separados por Salto de Línea) */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-bold text-gray-700 uppercase">
                    Lista de Requisitos (Un requisito por línea)
                  </label>
                  <span className="text-[11px] font-semibold text-[#113f8a] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                    {formData.requisitosTexto.split('\n').filter((l) => l.trim()).length} requisitos detectados
                  </span>
                </div>

                <textarea
                  rows="6"
                  value={formData.requisitosTexto}
                  onChange={(e) =>
                    setFormData({ ...formData, requisitosTexto: e.target.value })
                  }
                  placeholder="Escribe cada requisito en una nueva línea:&#10;1. Solicitud con carácter de declaración jurada&#10;2. Copia simple del DNI del titular o representante&#10;3. Croquis o plano de ubicación del local comercial"
                  className="w-full text-sm px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#113f8a] focus:outline-none font-sans leading-relaxed"
                />

                <p className="text-[11px] text-gray-500 mt-1">
                  ℹ️ <strong>Instrucción:</strong> Presiona <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-700 text-[10px]">Enter</kbd> para separar cada requisito. En el backend se guardarán como filas individuales vinculadas al trámite.
                </p>
              </div>

              {/* Pie del Modal con Botones */}
              <div className="pt-3 border-t border-gray-200 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={cerrarModal}
                  disabled={guardando}
                  className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 text-xs font-bold transition disabled:opacity-50"
                >
                  Cancelar
                </button>

                <button
                  type="submit"
                  disabled={guardando}
                  className="bg-[#113f8a] hover:bg-[#0c2f68] text-white px-5 py-2 rounded-lg text-xs font-bold shadow-md hover:shadow-lg transition flex items-center gap-2 disabled:opacity-50"
                >
                  {guardando ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Guardando en BD...</span>
                    </>
                  ) : (
                    <>
                      <span>{modoEdicion ? 'Guardar Cambios' : 'Registrar Trámite'}</span>
                      <span>💾</span>
                    </>
                  )}
                </button>
              </div>

            </form>

          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* MODAL DE CONFIRMACIÓN DE ELIMINACIÓN (Con borrado en cascada)         */}
      {/* --------------------------------------------------------------------- */}
      {tramiteAEliminar && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-2xl border border-red-300 w-full max-w-md p-5 space-y-4">
            
            <div className="flex items-center space-x-3 text-red-600">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center text-2xl flex-shrink-0">
                ⚠️
              </div>
              <div>
                <h3 className="font-extrabold text-base text-gray-900 leading-tight">
                  ¿Confirmar eliminación del trámite?
                </h3>
                <span className="text-xs text-red-700 font-semibold font-mono">
                  {tramiteAEliminar.id_tramite}
                </span>
              </div>
            </div>

            <div className="bg-red-50/70 p-3 rounded-lg border border-red-200 text-xs text-red-900 space-y-1">
              <p className="font-bold text-gray-800">
                &ldquo;{tramiteAEliminar.nombre}&rdquo;
              </p>
              <p className="text-[11px] text-gray-600 leading-relaxed">
                Esta acción ejecutará una eliminación en cascada (<code>ON DELETE CASCADE</code>). Se eliminarán de forma permanente el trámite y sus {Array.isArray(tramiteAEliminar.requisitos) ? tramiteAEliminar.requisitos.length : 0} requisitos vinculados.
              </p>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-gray-200">
              <button
                type="button"
                onClick={() => setTramiteAEliminar(null)}
                disabled={eliminando}
                className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 text-xs font-bold transition disabled:opacity-50"
              >
                Cancelar
              </button>

              <button
                type="button"
                onClick={confirmarEliminar}
                disabled={eliminando}
                className="bg-red-700 hover:bg-red-800 text-white px-4 py-2 rounded-lg text-xs font-bold shadow-md transition flex items-center gap-1.5 disabled:opacity-50"
              >
                {eliminando ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Eliminando...</span>
                  </>
                ) : (
                  <>
                    <span>Sí, Eliminar Trámite</span>
                    <span>🗑️</span>
                  </>
                )}
              </button>
            </div>

          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* 6. PIE DE PÁGINA INSTITUCIONAL NEGRO                                  */}
      {/* --------------------------------------------------------------------- */}
      <footer className="bg-[#1a1a1a] text-gray-300 text-xs py-3.5 px-4 sm:px-8 border-t border-gray-800 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span className="font-semibold text-white">2026 OFICINA DE TECNOLOGÍAS DE LA INFORMACIÓN Y COMUNICACIÓN</span>
            <span className="text-gray-400 ml-2">| Sistema de Gestión TUPA</span>
          </div>
          <div className="flex items-center space-x-4 text-gray-400">
            <Link href="/" className="hover:text-white transition">
              Chatbot Leonardito
            </Link>
            <span>•</span>
            <span className="hover:text-white cursor-pointer transition">Portal del Estado Peruano (Gob.pe)</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
