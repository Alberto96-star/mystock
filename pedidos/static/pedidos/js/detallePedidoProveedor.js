document.addEventListener('DOMContentLoaded', function () {
    const productSelect = document.getElementById('id_producto');
    const precioUnitarioInput = document.getElementById('id_precio_unitario');
    const categoriaFilter = document.getElementById('categoria-filter');
    const stockSpan = document.getElementById('stock-orden-0');

    // Guardar copia de todas las opciones del select
    const allOptions = Array.from(productSelect.options);

    // Filtrado de productos por categoría (iOS compatible)
    if (categoriaFilter && productSelect) {
        categoriaFilter.addEventListener('change', function () {
            const categoriaSeleccionada = this.value;

            // Limpiar y reconstruir opciones según categoría
            productSelect.innerHTML = '';

            allOptions.forEach(option => {
                const categoriaProducto = option.getAttribute('data-categoria');
                const mostrar = !categoriaSeleccionada || categoriaProducto === categoriaSeleccionada;

                if (mostrar) {
                    productSelect.appendChild(option.cloneNode(true));
                }
            });

            // Reiniciar valores visuales
            productSelect.value = "";
            if (precioUnitarioInput) precioUnitarioInput.value = "0.00";
            if (stockSpan) stockSpan.textContent = "Stock disponible: 0";
        });
    }

    // Mostrar el stock y precio del producto seleccionado
    if (productSelect && precioUnitarioInput) {
        productSelect.addEventListener('change', function () {
            const selectedOption = this.options[this.selectedIndex];

            const precio = selectedOption.getAttribute('data-precio');
            const cantActual = parseInt(selectedOption.getAttribute('cantActual') || 0);
            const cantReservada = parseInt(selectedOption.getAttribute('cantReservada') || 0);
            const disponible = cantActual - cantReservada;

            precioUnitarioInput.value = precio ? parseFloat(precio).toFixed(2) : "0.00";
            if (stockSpan) {
                stockSpan.textContent = `Stock disponible: ${disponible}`;
            }
        });
    }

    // Validación para cambio de estado del pedido
    const totalProductosElement = document.querySelector('[data-total-productos]');
    const totalProductos = totalProductosElement ?
        parseInt(totalProductosElement.getAttribute('data-total-productos')) : 0;

    const formEstado = document.querySelector('form[action*="detalle_pedido_proveedor"]');
    const selectEstado = document.getElementById('id_estado');

    if (formEstado && selectEstado) {
        formEstado.addEventListener('submit', function (e) {
            const nuevoEstado = selectEstado.value;
            const estadosQueRequierenProductos = ['enviado', 'recibido', 'completado'];
            const tieneProductos = totalProductos > 0;

            if (estadosQueRequierenProductos.includes(nuevoEstado) && !tieneProductos) {
                e.preventDefault();
                alert('No puedes cambiar a este estado porque el pedido no tiene productos asociados.');
                return false;
            }
        });
    }

    // Validación para evitar eliminar el último producto del pedido
    const botonesEliminarProducto = document.querySelectorAll('form[action*="eliminar_producto_pedido_proveedor"] button[type="submit"]');

    botonesEliminarProducto.forEach(function (boton) {
        boton.addEventListener('click', function (e) {
            if (totalProductos <= 1) {
                e.preventDefault();
                alert('No puedes eliminar el último producto del pedido.');
                return false;
            }
        });
    });
});
