"use strict";

(() => {
  const $ = id => document.getElementById(id);
  const loginPage = document.body.dataset.pagina === "login";
  const loginUrl = "/admin/login";
  let tramites = [];
  let selectedDelete = null;
  let toastTimer;
  let loading = false;

  function showError(element, message) {
    element.textContent = message;
    element.hidden = false;
  }

  async function api(url, options = {}) {
    const response = await fetch(url, {
      credentials: "same-origin",
      cache: "no-store",
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
    if (!loginPage && (response.status === 401 || response.status === 403)) {
      window.location.replace(`${loginUrl}?sesion=expirada`);
      throw new Error("Tu sesión ha expirado. Inicia sesión nuevamente.");
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.status !== "success") {
      throw new Error(data.mensaje || "No se pudo completar la operación. Intenta nuevamente.");
    }
    return data;
  }

  if (loginPage) {
    $("ver-password").addEventListener("click", event => {
      const show = $("login-password").type === "password";
      $("login-password").type = show ? "text" : "password";
      event.currentTarget.setAttribute("aria-label", show ? "Ocultar contraseña" : "Mostrar contraseña");
      event.currentTarget.setAttribute("aria-pressed", String(show));
    });
    $("form-login").addEventListener("submit", async event => {
      event.preventDefault();
      const button = $("login-submit");
      if (button.disabled) return;
      button.disabled = true;
      button.querySelector("span").textContent = "Verificando acceso…";
      $("login-error").hidden = true;
      try {
        await api("/api/admin/login", {
          method: "POST",
          body: JSON.stringify({ usuario: $("login-usuario").value.trim(), password: $("login-password").value }),
        });
        // El servidor vuelve a validar la sesión antes de entregar el panel.
        window.location.replace("/admin");
      } catch (error) {
        showError($("login-error"), error.message || "No hay conexión con el servidor.");
        $("login-password").focus();
        button.disabled = false;
        button.querySelector("span").textContent = "Ingresar al panel";
      }
    });
    return;
  }

  function notify(message, error = false) {
    clearTimeout(toastTimer);
    $("alerta-mensaje").textContent = message;
    $("alerta-box").classList.toggle("error", error);
    $("alerta-box").setAttribute("role", error ? "alert" : "status");
    $("alerta-box").hidden = false;
    toastTimer = setTimeout(() => { $("alerta-box").hidden = true; }, 5500);
  }

  const normalize = value => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

  function stateRow(message) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.className = "table-state";
    cell.textContent = message;
    row.append(cell);
    $("tbody-tramites").replaceChildren(row);
  }

  function applyFilters() {
    const query = normalize($("filtro-busqueda").value.trim());
    const [field, direction] = $("orden-tabla").value.split("-");
    const key = field === "nombre" ? "nombre" : "id_tramite";
    const list = tramites.filter(item => normalize(`${item.id_tramite} ${item.nombre}`).includes(query));
    list.sort((a, b) => String(a[key]).localeCompare(String(b[key]), "es", { numeric: true }) * (direction === "desc" ? -1 : 1));
    $("total-resultados").textContent = list.length.toLocaleString("es-PE");
    $("resultados-texto").textContent = `Mostrando ${list.length} de ${tramites.length} trámites`;
    if (!list.length) {
      stateRow(query ? "No encontramos trámites con esa búsqueda. Prueba con otro nombre o código." : "El catálogo todavía no tiene trámites. Registra el primero para comenzar.");
      return;
    }
    const fragment = document.createDocumentFragment();
    for (const item of list) {
      const row = document.createElement("tr");
      const code = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = "code-badge";
      badge.textContent = item.id_tramite;
      code.append(badge);
      const name = document.createElement("td");
      name.className = "name-cell";
      const nameText = document.createElement("span");
      nameText.textContent = item.nombre;
      nameText.title = item.nombre;
      name.append(nameText);
      const values = [[item.costo || "No especificado", "value-pill"], [item.plazo || "No especificado", "value-pill deadline-pill"]].map(([value, className]) => {
        const cell = document.createElement("td");
        const pill = document.createElement("span");
        pill.className = className;
        pill.textContent = value;
        cell.append(pill);
        return cell;
      });
      const requirements = document.createElement("td");
      requirements.className = "requirements-count";
      const count = (item.requisitos || []).length;
      requirements.textContent = `${count} ${count === 1 ? "requisito" : "requisitos"}`;
      const actions = document.createElement("td");
      actions.className = "row-actions";
      for (const [label, className, action] of [["Editar", "row-action", () => editRecord(item)], ["Eliminar", "row-action delete", () => confirmDelete(item)]]) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = className;
        button.textContent = label;
        button.setAttribute("aria-label", `${label} trámite ${item.id_tramite}`);
        button.addEventListener("click", action);
        actions.append(button);
      }
      row.append(code, name, ...values, requirements, actions);
      fragment.append(row);
    }
    // Los nombres y requisitos del catálogo nunca se insertan como HTML.
    $("tbody-tramites").replaceChildren(fragment);
  }

  async function loadCatalog() {
    if (loading) return;
    loading = true;
    $("actualizar-catalogo").disabled = true;
    $("tabla-scroll").setAttribute("aria-busy", "true");
    try {
      const data = await api("/api/admin/tramites");
      tramites = data.tramites;
      $("total-tramites").textContent = tramites.length.toLocaleString("es-PE");
      $("catalog-count").textContent = tramites.length;
      $("total-requisitos").textContent = tramites.reduce((total, item) => total + (item.requisitos || []).length, 0).toLocaleString("es-PE");
      applyFilters();
    } catch (error) {
      notify(error.message || "No se pudo conectar con el servidor.", true);
      if (!tramites.length) {
        stateRow("No se pudo cargar el catálogo. Utiliza Actualizar para volver a intentarlo.");
        $("resultados-texto").textContent = "Catálogo no disponible";
      }
    } finally {
      loading = false;
      $("actualizar-catalogo").disabled = false;
      $("tabla-scroll").removeAttribute("aria-busy");
    }
  }

  function editRecord(item = null) {
    $("form-tramite").reset();
    $("tramite-error").hidden = true;
    $("modal-titulo").textContent = item ? "Editar trámite" : "Nuevo trámite";
    $("tramite-id-bd").value = item ? (item.id || item.id_tramite) : "";
    for (const [field, value] of [["codigo", item?.id_tramite], ["nombre", item?.nombre], ["costo", item?.costo], ["plazo", item?.plazo], ["requisitos", item?.requisitos?.join("\n")]]) {
      $(`tramite-${field}`).value = value || "";
    }
    $("modal-tramite").showModal();
  }

  function confirmDelete(item) {
    selectedDelete = item;
    $("eliminar-codigo").textContent = item.id_tramite;
    $("eliminar-nombre").textContent = item.nombre;
    $("eliminar-error").hidden = true;
    $("modal-eliminar").showModal();
  }

  $("form-tramite").addEventListener("submit", async event => {
    event.preventDefault();
    const button = $("guardar-tramite");
    if (button.disabled) return;
    const requirements = $("tramite-requisitos").value.split("\n").map(text => text.trim()).filter(Boolean);
    if (!requirements.length) {
      showError($("tramite-error"), "Añade al menos un requisito para el ciudadano.");
      $("tramite-requisitos").focus();
      return;
    }
    const id = $("tramite-id-bd").value;
    const body = {
      id_tramite: $("tramite-codigo").value.trim(),
      nombre: $("tramite-nombre").value.trim(),
      costo: $("tramite-costo").value.trim(),
      plazo: $("tramite-plazo").value.trim(),
      requisitos: requirements,
    };
    button.disabled = true;
    button.textContent = "Guardando…";
    $("tramite-error").hidden = true;
    try {
      await api(id ? `/api/admin/tramites/${encodeURIComponent(id)}` : "/api/admin/tramites", { method: id ? "PUT" : "POST", body: JSON.stringify(body) });
      $("modal-tramite").close();
      notify(id ? "La información del trámite se actualizó correctamente." : "El nuevo trámite se registró correctamente.");
      await loadCatalog();
    } catch (error) {
      showError($("tramite-error"), error.message || "No se pudo guardar el trámite.");
    } finally {
      button.disabled = false;
      button.textContent = "Guardar trámite";
    }
  });

  $("confirmar-eliminar").addEventListener("click", async () => {
    const button = $("confirmar-eliminar");
    if (button.disabled || !selectedDelete) return;
    const id = selectedDelete.id || selectedDelete.id_tramite;
    button.disabled = true;
    button.textContent = "Eliminando…";
    try {
      await api(`/api/admin/tramites/${encodeURIComponent(id)}`, { method: "DELETE" });
      $("modal-eliminar").close();
      notify("El trámite y sus requisitos se eliminaron correctamente.");
      await loadCatalog();
    } catch (error) {
      showError($("eliminar-error"), error.message || "No se pudo eliminar el trámite.");
    } finally {
      button.disabled = false;
      button.textContent = "Sí, eliminar trámite";
    }
  });

  document.querySelectorAll("[data-logout]").forEach(button => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await api("/api/admin/logout", { method: "POST" });
        window.location.replace(loginUrl);
      } catch (error) {
        notify(error.message || "No se pudo cerrar la sesión. Intenta nuevamente.", true);
        button.disabled = false;
      }
    });
  });
  document.querySelectorAll("[data-close]").forEach(button => {
    button.addEventListener("click", () => $(button.dataset.close).close());
  });
  $("nuevo-tramite").addEventListener("click", () => editRecord());
  $("actualizar-catalogo").addEventListener("click", loadCatalog);
  $("filtro-busqueda").addEventListener("input", () => { applyFilters(); $("tabla-scroll").scrollTop = 0; });
  $("orden-tabla").addEventListener("change", () => { applyFilters(); $("tabla-scroll").scrollTop = 0; });
  $("cerrar-alerta").addEventListener("click", () => { $("alerta-box").hidden = true; });
  window.addEventListener("pageshow", event => { if (event.persisted) window.location.reload(); });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) api("/api/admin/sesion").catch(() => {});
  });
  loadCatalog();
})();
