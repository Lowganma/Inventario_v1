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