// La moneda de consulta nunca modifica los valores de los formularios.
const monedaVista = (() => {
    const tasa = Number(document.getElementById("bcv-rate-container")?.dataset.tasa);
    const hayTasa = Number.isFinite(tasa) && tasa > 0;
    const clave = "venta_catalogo_moneda"; // Conserva la preferencia del catálogo anterior.
    const formato = new Intl.NumberFormat("es-VE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
    const centavosUSD = new Intl.NumberFormat("en-US", {
        useGrouping: false, minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
    const tasaEnMillonesimas = hayTasa ? BigInt(Math.round(tasa * 1_000_000)) : null;
    let seleccion = "usd";
    try {
        if (hayTasa && localStorage.getItem(clave) === "bs") seleccion = "bs";
    } catch { /* El selector también funciona sin almacenamiento. */ }

    function importe(usd, moneda = seleccion) {
        if (!Number.isFinite(Number(usd))) return "—";
        if (moneda === "usd") return "USD " + formato.format(usd);
        if (!hayTasa) return "—";
        // Dos decimales del importe más seis de la tasa. Intl redondea al mostrar.
        const centavos = BigInt(centavosUSD.format(usd).replace(".", ""));
        const bolivares = (centavos * tasaEnMillonesimas).toString() + "e-8";
        return "Bs. " + formato.format(bolivares);
    }

    function actualizar(contenedor) {
        contenedor.querySelectorAll("data.ot-importe").forEach(elemento => {
            elemento.textContent = importe(elemento.value);
        });
    }

    function aplicar() {
        document.documentElement.dataset.moneda = seleccion;
        actualizar(document);
        document.querySelectorAll("[data-moneda-vista]").forEach(boton => {
            const activo = boton.dataset.monedaVista === seleccion;
            boton.setAttribute("aria-pressed", String(activo));
            boton.classList.toggle("active", activo);
            if (boton.dataset.monedaVista === "bs" && !hayTasa) {
                boton.disabled = true;
                boton.title = "Actualiza la tasa BCV para consultar en bolívares";
            }
        });
        document.dispatchEvent(new Event("monedacambiada"));
    }

    document.querySelectorAll("[data-moneda-vista]").forEach(boton => {
        boton.addEventListener("click", () => {
            seleccion = boton.dataset.monedaVista;
            try { localStorage.setItem(clave, seleccion); } catch { /* Solo esta página. */ }
            aplicar();
        });
    });
    aplicar();
    return { importe, actualizar, tasa, get seleccion() { return seleccion; } };
})();
