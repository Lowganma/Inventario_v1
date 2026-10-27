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
// Importes contables e inputs permanecen en USD. Bs. es una referencia BCV.
window.Precios = (() => {
    const formatoBs = new Intl.NumberFormat("es-VE", {
        minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
    function numero(valor) {
        const n = Number(String(valor ?? "").replace(",", "."));
        return Number.isFinite(n) ? n : 0;
    }
    function tasa() {
        const valor = numero(document.getElementById("bcv-rate-container")?.dataset.tasa);
        return valor > 0 ? valor : 0;
    }
    function redondear(valor) {
        const n = numero(valor);
        return Math.sign(n) * Math.round((Math.abs(n) + Number.EPSILON) * 100) / 100;
    }
    function dolares(valor) {
        return "$" + redondear(valor).toFixed(2);
    }
    function bolivares(valor) {
        if (!tasa()) return "Tasa BCV no disponible";
        const usd = redondear(valor);
        return "Bs. " + formatoBs.format(redondear(usd * tasa()));
    }
    function mostrar(elemento, valor, principal = "usd") {
        const usd = dolares(valor);
        const bs = bolivares(valor);
        const contenedor = document.createElement("span");
        contenedor.className = "precio-doble";
        const primero = document.createElement("span");
        primero.className = principal === "bs" ? "precio-bs-principal" : "precio-usd";
        primero.textContent = principal === "bs" ? bs : usd;
        const segundo = document.createElement("small");
        segundo.className = "precio-bs";
        segundo.textContent = principal === "bs" ? usd : bs;
        segundo.title = "Equivalente de referencia con la última tasa BCV registrada";
        contenedor.append(primero, segundo);
        elemento.replaceChildren(contenedor);
    }
    function actualizarInputs(root = document) {
        root.querySelectorAll("[data-equivalente-input]").forEach(salida => {
            const input = document.getElementById(salida.dataset.equivalenteInput);
            salida.textContent = input && input.value !== "" ? "USD · " + bolivares(input.value) : "Importe en USD · equivalente en Bs.";
        });
    }
    document.addEventListener("DOMContentLoaded", () => actualizarInputs());
    document.addEventListener("input", () => actualizarInputs());
    return { tasa, bolivares, mostrar, actualizarInputs, redondear, dolares };
})();
