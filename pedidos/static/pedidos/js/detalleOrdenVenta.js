document.addEventListener('DOMContentLoaded', function () {
    const categoriaFilter = document.getElementById('categoria-filter');
    const productoSelect = document.getElementById('id_producto_orden');
    const stockSpan = document.getElementById('stock-orden-0');
    const precioUnitarioInputOrden = document.getElementById('id_precio_unitario_orden');

    // Guardar copia de todas las opciones al inicio
    const allOptions = Array.from(productoSelect.options);

    // Filtrar productos al cambiar categoría
    if (categoriaFilter && productoSelect) {
        categoriaFilter.addEventListener('change', function () {
            const categoriaSeleccionada = this.value;

            // Limpiar el select
            productoSelect.innerHTML = '';

            // Agregar solo las opciones que coincidan con la categoría seleccionada
            allOptions.forEach(option => {
                const categoriaProducto = option.getAttribute('data-categoria');
                const esOpcionValida = !categoriaSeleccionada || !categoriaProducto || categoriaProducto === categoriaSeleccionada;

                if (esOpcionValida) {
                    productoSelect.appendChild(option.cloneNode(true));
                }
            });

            // Reiniciar valores
            productoSelect.value = "";
            if (precioUnitarioInputOrden) precioUnitarioInputOrden.value = "0.00";
            if (stockSpan) stockSpan.textContent = "Stock disponible: 0";
        });
    }

    // Mostrar stock disponible y actualizar precio al seleccionar producto
    if (productoSelect && stockSpan) {
        productoSelect.addEventListener('change', function () {
            const selectedOption = this.options[this.selectedIndex];
            const cantActual = parseInt(selectedOption.getAttribute('cantActual') || 0);
            const cantReservada = parseInt(selectedOption.getAttribute('cantReservada') || 0);
            const precio = selectedOption.getAttribute('data-precio') || "0.00";
            const disponible = cantActual - cantReservada;

            if (stockSpan) {
                stockSpan.textContent = `Stock disponible: ${disponible}`;
            }

            if (precioUnitarioInputOrden) {
                precioUnitarioInputOrden.value = parseFloat(precio).toFixed(2);
            }
        });
    }
});
