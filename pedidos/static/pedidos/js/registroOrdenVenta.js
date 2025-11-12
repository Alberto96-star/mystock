document.addEventListener('DOMContentLoaded', function () {
    const productDetailsContainerOrden = document.getElementById('product-details-container-orden');
    const addProductBtnOrden = document.getElementById('add-product-btn-orden');
    let productCountOrden = 1;

    const originalProductSelect = document.querySelector('.product-select-orden');
    const originalProductOptionsHTML = originalProductSelect ? originalProductSelect.innerHTML : '';
    const allProductOptions = Array.from(originalProductSelect.options);

    function filtrarProductosPorCategoria(selectElement, categoriaSeleccionada) {
        selectElement.innerHTML = '';
        allProductOptions.forEach(opt => {
            const categoria = opt.getAttribute('data-categoria');
            if (!categoriaSeleccionada || categoria === categoriaSeleccionada || opt.value === "") {
                selectElement.appendChild(opt.cloneNode(true));
            }
        });
    }

    function updateProductPrice(selectElement, priceInputElement) {
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        const precio = selectedOption.getAttribute('data-precio');
        const cantActual = parseInt(selectedOption.getAttribute('cantActual') || 0);
        const cantReservada = parseInt(selectedOption.getAttribute('cantReservada') || 0);
        const cantidadDisponible = cantActual - cantReservada;

        priceInputElement.value = precio ? parseFloat(precio).toFixed(2) : "0.00";

        const stockSpanId = selectElement.id.replace('product-select-orden', 'stock-orden');
        const stockSpan = document.getElementById(stockSpanId);
        if (stockSpan) {
            stockSpan.textContent = `Stock disponible: ${cantidadDisponible}`;
        }
    }

    function updateRemoveButtonsOrden() {
        const removeButtons = productDetailsContainerOrden.querySelectorAll('.remove-product-btn-orden');
        removeButtons.forEach(btn => {
            btn.style.display = (removeButtons.length > 1) ? 'block' : 'none';
        });
    }

    function cloneProductRowOrden(index) {
        const originalRow = productDetailsContainerOrden.querySelector('.product-row-orden');
        const newRow = originalRow.cloneNode(true);

        newRow.classList.add('mt-3');
        newRow.querySelectorAll('[id]').forEach(el => {
            el.id = el.id.replace(/-\d+$/, `-${index}`);
        });
        newRow.querySelectorAll('[name]').forEach(el => el.value = el.defaultValue);

        const newSelect = newRow.querySelector('.product-select-orden');
        const newCategoryFilter = newRow.querySelector('#categoria-filter');
        const newPriceInput = newRow.querySelector('.precio-unitario-input-orden');
        const stockSpan = newRow.querySelector('small[id^="stock-orden-"]');

        newSelect.innerHTML = originalProductOptionsHTML;

        if (stockSpan) {
            stockSpan.id = `stock-orden-${index}`;
            stockSpan.textContent = 'Stock disponible: 0';
        }

        newSelect.value = "";
        newPriceInput.value = "0.00";
        newRow.querySelector('.cantidad-input-orden').value = "1";
        newRow.querySelector('.descuento-linea-input-orden').value = "0.00";

        if (newCategoryFilter && newSelect) {
            newCategoryFilter.addEventListener('change', function () {
                const categoriaSeleccionada = this.value;
                filtrarProductosPorCategoria(newSelect, categoriaSeleccionada);
                newSelect.value = "";
                newPriceInput.value = "0.00";
                if (stockSpan) stockSpan.textContent = 'Stock disponible: 0';
            });
        }

        newSelect.addEventListener('change', function () {
            updateProductPrice(this, newPriceInput);
        });

        return newRow;
    }

    // Delegación global para eliminar cualquier fila si hay más de una
    productDetailsContainerOrden.addEventListener('click', function (event) {
        const button = event.target.closest('.remove-product-btn-orden');
        if (button) {
            const allRows = productDetailsContainerOrden.querySelectorAll('.product-row-orden');
            if (allRows.length > 1) {
                button.closest('.product-row-orden').remove();
                updateRemoveButtonsOrden();
            }
        }
    });

    addProductBtnOrden.addEventListener('click', function () {
        const newProductRow = cloneProductRowOrden(productCountOrden);
        productDetailsContainerOrden.appendChild(newProductRow);
        productCountOrden++;
        updateRemoveButtonsOrden();
    });

    const initialProductSelect = document.getElementById('product-select-orden-0');
    const initialPriceInput = document.getElementById('precio-unitario-orden-0');
    const initialCategoryFilter = document.getElementById('categoria-filter');
    const initialStockSpan = document.getElementById('stock-orden-0');

    if (initialProductSelect) {
        initialProductSelect.addEventListener('change', function () {
            updateProductPrice(this, initialPriceInput);
        });
    }

    if (initialCategoryFilter) {
        initialCategoryFilter.addEventListener('change', function () {
            const categoriaSeleccionada = this.value;
            filtrarProductosPorCategoria(initialProductSelect, categoriaSeleccionada);
            initialProductSelect.value = "";
            initialPriceInput.value = "0.00";
            if (initialStockSpan) initialStockSpan.textContent = 'Stock disponible: 0';
        });
    }

    updateRemoveButtonsOrden();
});
