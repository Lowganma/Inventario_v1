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
document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("ot-menu");
    const sidebar = document.getElementById("menuPrincipal");
    if (!button || !sidebar) return;
    const wide = window.matchMedia("(min-width: 992px)");
    function show(open) {
        document.body.classList.toggle("ot-menu-open", open);
        sidebar.hidden = !open;
        button.setAttribute("aria-expanded", String(open));
    }
    function reset() {
        show(wide.matches && localStorage.getItem("ot-menu") !== "closed");
    }
    button.addEventListener("click", () => {
        const open = sidebar.hidden;
        show(open);
        if (wide.matches) localStorage.setItem("ot-menu", open ? "open" : "closed");
        if (open && !wide.matches) sidebar.querySelector("a").focus();
    });
    function dismiss() { show(false); button.focus(); }
    document.querySelector(".ot-backdrop").addEventListener("click", dismiss);
    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !wide.matches && !sidebar.hidden) dismiss();
    });
    sidebar.addEventListener("focusout", event => {
        if (!wide.matches && event.relatedTarget && !sidebar.contains(event.relatedTarget) && event.relatedTarget !== button) show(false);
    });
    wide.addEventListener("change", reset);
    reset();
});

document.addEventListener("DOMContentLoaded", () => {
    const photo = document.getElementById("vistaFotoProducto");
    const input = document.getElementById("id_imagen");
    if (photo && input) {
        const original = photo.getAttribute("src");
        let preview;
        input.addEventListener("change", () => {
            if (preview) URL.revokeObjectURL(preview);
            preview = input.files[0] && URL.createObjectURL(input.files[0]);
            const url = preview || original;
            if (url) photo.src = url;
            else photo.removeAttribute("src");
            photo.hidden = !url;
        });
    }
    const balance = document.getElementById("saldoAbono");
    const amount = document.getElementById("id_monto_pagado");
    if (balance && amount) {
        const display = document.getElementById("saldoProyectado");
        const format = new Intl.NumberFormat("es-VE", {minimumFractionDigits:2,maximumFractionDigits:2});
        const remaining = Math.round(Number(balance.dataset.saldo) * 100);
        function update() {
            const payment = Math.round(Number(amount.value) * 100);
            display.textContent = payment > remaining ? "El abono supera el saldo" : "USD " + format.format((remaining - Math.max(0, payment)) / 100);
        }
        amount.addEventListener("input", update);
        update();
    }
});
