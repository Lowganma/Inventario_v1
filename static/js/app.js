/* ============================================================
   ARCHIVO GLOBAL DE JAVASCRIPT
   Proyecto: Control de cuentas
   Descripción:
   Contiene las interacciones compartidas por toda la aplicación.
   ============================================================ */


document.addEventListener("DOMContentLoaded", () => {
    configurarTema();
});


/* ============================================================
   FUNCIONALIDAD: MODO CLARO Y OSCURO

   - Recupera la preferencia guardada en localStorage.
   - Cambia el atributo data-bs-theme del documento.
   - Actualiza el icono del botón.
   - Conserva la selección después de cerrar el navegador.
   ============================================================ */

function configurarTema() {
    const htmlElement = document.documentElement;
    const themeButton = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");

    // Evita errores si alguna página no contiene el botón.
    if (!themeButton || !themeIcon) {
        return;
    }

    const savedTheme =
        localStorage.getItem("app-theme") || "light";

    aplicarTema(savedTheme);

    themeButton.addEventListener("click", () => {
        const currentTheme =
            htmlElement.getAttribute("data-bs-theme");

        const newTheme =
            currentTheme === "dark" ? "light" : "dark";

        aplicarTema(newTheme);
        localStorage.setItem("app-theme", newTheme);
    });


    function aplicarTema(theme) {
        htmlElement.setAttribute("data-bs-theme", theme);

        if (theme === "dark") {
            themeIcon.className = "bi bi-sun";
            themeButton.title = "Activar modo claro";
            themeButton.setAttribute(
                "aria-label",
                "Activar modo claro"
            );
        } else {
            themeIcon.className = "bi bi-moon-stars";
            themeButton.title = "Activar modo oscuro";
            themeButton.setAttribute(
                "aria-label",
                "Activar modo oscuro"
            );
        }
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const botones = document.querySelectorAll(".toggle-password");

    botones.forEach(function (boton) {
        boton.addEventListener("click", function () {
            const targetId = boton.dataset.target;
            const input = document.getElementById(targetId);
            const icono = boton.querySelector("i");

            if (!input) {
                return;
            }

            const mostrar = input.type === "password";

            input.type = mostrar ? "text" : "password";

            if (icono) {
                icono.className = mostrar
                    ? "bi bi-eye-slash"
                    : "bi bi-eye";
            }

            const texto = mostrar
                ? "Ocultar contraseña"
                : "Mostrar contraseña";

            boton.title = texto;
            boton.setAttribute("aria-label", texto);
        });
    });
});
// Una preferencia de moneda para todas las pantallas. Los valores contables
// originales permanecen en USD; los controles visibles convierten al editar.
window.Precios = (() => {
    const formatoBs = new Intl.NumberFormat("es-VE", {minimumFractionDigits: 2, maximumFractionDigits: 2});
    const clave = "inventario-moneda";
    let moneda = "usd";
    let preferida = "usd";
    const campos = new Map();
    const nombres = new Set(["costo", "precio_venta", "monto_total", "monto_pagado", "monto", "saldo_inicial", "saldo_final_declarado", "valor_descuento"]);
    function numero(valor) {
        const n = Number(String(valor ?? "").replace(",", "."));
        return Number.isFinite(n) ? n : 0;
    }
    function tasa() {
        const n = numero(document.getElementById("bcv-rate-container")?.dataset.tasa);
        return n > 0 ? n : 0;
    }
    function redondear(valor) {
        const n = numero(valor);
        return Math.sign(n) * Math.round((Math.abs(n) + Number.EPSILON) * 100) / 100;
    }
    function dolares(valor) { return "$" + redondear(valor).toFixed(2); }
    function bolivares(valor) {
        return tasa() ? "Bs. " + formatoBs.format(redondear(redondear(valor) * tasa())) : "Tasa BCV no disponible";
    }
    function mostrar(elemento, valor) {
        elemento.dataset.importeUsd = String(redondear(valor));
        elemento.textContent = moneda === "bs" ? bolivares(valor) : dolares(valor);
        elemento.classList.add("importe-moneda");
    }
    function porcentaje(input) {
        return input.name === "valor_descuento" && document.getElementById("id_tipo_descuento")?.value === "porcentaje";
    }
    function actualizarInputs() {
        campos.forEach((visible, original) => {
            if (!original.isConnected) { campos.delete(original); return; }
            const esBs = moneda === "bs" && !porcentaje(original);
            visible.readOnly = original.readOnly;
            visible.disabled = original.disabled;
            if (document.activeElement !== visible) {
                visible.value = original.value === "" ? "" : redondear(numero(original.value) * (esBs ? tasa() : 1)).toFixed(2);
            }
            for (const limite of ["min", "max"]) {
                if (original.hasAttribute(limite)) visible.setAttribute(limite, String(numero(original.getAttribute(limite)) * (esBs ? tasa() : 1)));
            }
            const unidad = porcentaje(original) ? "%" : esBs ? "Bs." : "USD";
            visible.setAttribute("aria-label", `${original.dataset.etiquetaMoneda || original.name}: ${unidad}`);
            const prefijo = visible.parentElement.querySelector(".input-group-text");
            if (prefijo && /^(\$|USD|Bs\.|%)$/.test(prefijo.textContent.trim())) prefijo.textContent = unidad;
            const etiqueta = document.querySelector(`label[for="${visible.id}"]`);
            const badge = etiqueta?.querySelector("[data-unidad-moneda]");
            if (badge) badge.textContent = ` (${unidad})`;
        });
    }
    function prepararInputs() {
        document.querySelectorAll('input[type="number"]:not([data-moneda-visible])').forEach(original => {
            if (campos.has(original) || !(nombres.has(original.name))) return;
            const visible = original.cloneNode();
            visible.removeAttribute("name");
            visible.removeAttribute("class");
            visible.className = "form-control";
            visible.id = `${original.id}-moneda`;
            visible.dataset.monedaVisible = "true";
            visible.step = "0.01";
            const etiqueta = document.querySelector(`label[for="${original.id}"]`);
            if (etiqueta) {
                original.dataset.etiquetaMoneda = etiqueta.textContent.trim();
                etiqueta.htmlFor = visible.id;
                const unidad = document.createElement("span");
                unidad.dataset.unidadMoneda = "";
                etiqueta.append(unidad);
            }
            original.type = "hidden";
            original.after(visible);
            campos.set(original, visible);
            visible.addEventListener("input", () => {
                original.value = visible.value === "" ? "" : redondear(numero(visible.value) / (moneda === "bs" && !porcentaje(original) ? tasa() : 1)).toFixed(2);
                original.dispatchEvent(new Event("input", {bubbles: true}));
            });
            visible.addEventListener("change", () => original.dispatchEvent(new Event("change", {bubbles: true})));
            visible.addEventListener("blur", () => actualizarInputs());
        });
        actualizarInputs();
    }
    function refrescar(root = document) {
        if (root.matches?.("[data-importe-usd]")) mostrar(root, root.dataset.importeUsd);
        root.querySelectorAll("[data-importe-usd]").forEach(el => mostrar(el, el.dataset.importeUsd));
        prepararInputs();
    }
    function cambiar(elegida, guardar = true) {
        preferida = elegida === "bs" ? "bs" : "usd";
        moneda = preferida === "bs" && tasa() ? "bs" : "usd";
        document.documentElement.dataset.moneda = moneda;
        document.querySelectorAll("button[data-moneda]").forEach(b => {
            b.setAttribute("aria-pressed", String(b.dataset.moneda === moneda));
            if (b.dataset.moneda === "bs") {
                b.disabled = !tasa();
                if (b.disabled) b.title = "Actualiza la tasa BCV para usar bolívares";
                else b.removeAttribute("title");
            }
        });
        const estado = document.getElementById("moneda-estado");
        if (estado) estado.textContent = !tasa() ? "Actualiza la tasa BCV para ver bolívares" : moneda === "bs" ? "Bolívares · tasa BCV de referencia" : "Importes en dólares";
        if (guardar) { try { localStorage.setItem(clave, preferida); } catch (_) {} }
        refrescar();
    }
    document.addEventListener("DOMContentLoaded", () => {
        let guardada;
        try { guardada = localStorage.getItem(clave); } catch (_) {}
        cambiar(guardada, false);
        document.addEventListener("click", evento => {
            const boton = evento.target.closest("button[data-moneda]");
            if (boton && !boton.disabled) cambiar(boton.dataset.moneda);
        });
        // Recalcular siempre desde USD si la tasa activa cambia sin recargar.
        const contenedorTasa = document.getElementById("bcv-rate-container");
        if (contenedorTasa) {
            new MutationObserver(() => cambiar(preferida, false)).observe(contenedorTasa, {
                attributes: true, attributeFilter: ["data-tasa"]
            });
        }
        new MutationObserver(registros => {
            registros.forEach(r => r.addedNodes.forEach(n => {
                if (n.nodeType === 1 && (n.matches("[data-importe-usd], input[type=number]") || n.querySelector("[data-importe-usd], input[type=number]"))) refrescar(n.parentElement || document);
            }));
        }).observe(document.querySelector("main") || document.body, {childList: true, subtree: true});
    });
    window.addEventListener("storage", evento => {
        if (evento.key === clave || evento.key === null) cambiar(evento.newValue, false);
    });
    document.addEventListener("change", actualizarInputs);
    return { tasa, bolivares, mostrar, actualizarInputs, redondear, dolares, cambiar, refrescar };
})();
