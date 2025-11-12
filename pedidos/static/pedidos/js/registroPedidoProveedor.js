/**
 * Gestión de pedidos a proveedor - Funcionalidad para añadir/eliminar productos dinámicamente
 */

class PedidoProveedorManager {
    constructor() {
        this.productDetailsContainer = document.getElementById('product-details-container');
        this.addProductBtn = document.getElementById('add-product-btn');
        this.productCount = 1; // Contador para IDs únicos
        this.productosData = window.productosData || [];

        this.init();
    }

    /**
     * Inicializar la funcionalidad
     */
    init() {
        if (!this.productDetailsContainer || !this.addProductBtn) {
            console.error('Elementos requeridos no encontrados en el DOM');
            return;
        }

        // Configurar eventos para la fila inicial
        const initialRow = document.querySelector('.product-row');
        if (initialRow) {
            this.setupProductRowEvents(initialRow);
        }

        // Event listener para añadir producto
        this.addProductBtn.addEventListener('click', (e) => this.handleAddProduct(e));

        // Actualización inicial de botones
        this.updateRemoveButtons();
    }

    /**
     * Actualizar la visibilidad de los botones de Eliminar
     */

    updateRemoveButtons() {
        const productRows = this.productDetailsContainer.querySelectorAll('.product-row');
        const removeButtons = this.productDetailsContainer.querySelectorAll('.remove-product-btn');

        const mostrar = productRows.length > 1;

        removeButtons.forEach(btn => {
            btn.style.display = mostrar ? 'block' : 'none';
        });
    }


    /**
     * Crear las opciones del select de productos
     * @returns {string} HTML de las opciones
     */

    createCategoriaOptions() {
        let options = '<option value="">Filtrar categorías</option>';
        (window.categoriasData || []).forEach(cat => {
            options += `<option value="${cat.id}">${cat.nombre}</option>`;
        });
        return options;
    }


    createProductOptions() {
        let options = '<option value="">Selecciona un producto</option>';
        this.productosData.forEach(function (prod) {
            options += `<option value="${prod.id}" 
                data-precio="${prod.precio}" data-categoria="${prod.categoria}" cantActual="${prod.cantActual}" cantReservada="${prod.cantReservada}" >${prod.nombre}</option>`;
        });
        return options;
    }

    /**
     * Crear una nueva fila de producto
     * @param {number} index - Índice para IDs únicos
     * @returns {HTMLElement} Elemento DOM de la nueva fila
     */
    createProductRow(index) {
        const newRowHTML = `
            <div class="row g-3 align-items-end mb-3 product-row border rounded p-3 bg-light">
                <div class="col-md-2">
                    <label class="form-label">Categorias</label>
                    <select class="form-select me-2 categoria-filter" id="categoria-filter-${index}">
                        ${this.createCategoriaOptions()}
                    </select>
                </div>
                <div class="col-md-4">
                    <label for="product-select-${index}" class="form-label">Producto - <small id="stock-orden-0" class="text-muted">Stock disponible: 0</small><span class="text-danger"> *</span></label>
                    <select class="form-select product-select" id="product-select-${index}" name="producto_id" required>
                        ${this.createProductOptions()}
                    </select>
                </div>
                <div class="col-md-2">
                    <label for="cantidad-${index}" class="form-label">Cantidad <span class="text-danger">*</span></label>
                    <input type="number" class="form-control cantidad-input" id="cantidad-${index}" name="cantidad" value="1" min="1" required>
                </div>
                <div class="col-md-2">
                    <label for="precio-unitario-${index}" class="form-label">Precio Unitario (€) <span class="text-danger">*</span></label>
                    <input type="number" step="0.01" class="form-control precio-unitario-input" id="precio-unitario-${index}" name="precio_unitario" value="0.00" min="0" required>
                </div>
                <div class="col-md-2">
                    <label for="igic-porcentaje-${index}" class="form-label">Porcentaje de IGIC (%) <span class="text-danger">*</span></label>
                    <select class="form-select" id="igic-porcentaje-${index}" name="igic_porcentaje" required>
                        <option value="">Seleccionar porcentaje de IGIC...</option>
                        <option value="0.00">0% - Exento</option>
                        <option value="3.00">3% - Tipo reducido</option>
                        <option value="7.00" selected>7% - Tipo general</option>
                    </select>
                </div>
                <div class="col-md-1 d-flex justify-content-center">
                    <button type="button" class="btn btn-danger btn-sm remove-product-btn">
                        Eliminar
                    </button>
                </div>
            </div>
        `;

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = newRowHTML;
        return tempDiv.firstElementChild;
    }

    /**
     * Configurar eventos de una fila de producto
     * @param {HTMLElement} row - Elemento de la fila
     */
    setupProductRowEvents(row) {
        const productSelect = row.querySelector('.product-select');
        const priceInput = row.querySelector('.precio-unitario-input');
        const removeBtn = row.querySelector('.remove-product-btn');
        const categoriaFilter = row.querySelector('.categoria-filter');

        // Capturar copia de opciones originales para reconstrucción posterior
        const originalOptions = Array.from(productSelect.querySelectorAll('option')).map(option => option.cloneNode(true));

        // Filtrar productos por categoría (compatible con Safari)
        if (categoriaFilter && productSelect) {
            categoriaFilter.addEventListener('change', () => {
                const categoriaSeleccionada = categoriaFilter.value;

                // Limpiar opciones actuales
                productSelect.innerHTML = '';

                // Agregar solo las opciones que coinciden con la categoría o son la opción vacía
                originalOptions.forEach(option => {
                    const categoriaProducto = option.getAttribute('data-categoria');
                    if (!categoriaSeleccionada || categoriaProducto === categoriaSeleccionada || option.value === "") {
                        productSelect.appendChild(option.cloneNode(true));
                    }
                });

                productSelect.value = "";
                priceInput.value = "0.00";

                const stockSpan = row.querySelector('small[id^="stock-orden-"]');
                if (stockSpan) {
                    stockSpan.textContent = `Stock disponible: 0`;
                }
            });
        }

        // Actualizar precio y stock al seleccionar producto
        if (productSelect && priceInput) {
            productSelect.addEventListener('change', () => {
                const selectedOption = productSelect.options[productSelect.selectedIndex];
                const precio = selectedOption.getAttribute('data-precio');
                const cantActual = parseInt(selectedOption.getAttribute('cantActual') || 0);
                const cantReservada = parseInt(selectedOption.getAttribute('cantReservada') || 0);
                const cantidadDisponible = cantActual - cantReservada;

                priceInput.value = isNaN(parseFloat(precio)) ? "0.00" : parseFloat(precio).toFixed(2);

                const stockSpan = row.querySelector('small[id^="stock-orden-"]');
                if (stockSpan) {
                    stockSpan.textContent = `Stock disponible: ${cantidadDisponible}`;
                }
            });
        }

        // Botón eliminar (mantiene lógica actual)
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                const totalRows = this.productDetailsContainer.querySelectorAll('.product-row').length;
                if (totalRows > 1) {
                    row.remove();
                    this.updateRemoveButtons();
                }
            });
        }
    }

    /**
     * Manejar la adición de un nuevo producto
     * @param {Event} e - Evento del click
     */
    handleAddProduct(e) {
        e.preventDefault(); // Prevenir comportamiento por defecto

        try {
            const newProductRow = this.createProductRow(this.productCount);

            this.productDetailsContainer.appendChild(newProductRow);

            // Configurar eventos para la nueva fila
            this.setupProductRowEvents(newProductRow);

            this.productCount++;
            this.updateRemoveButtons();

        } catch (error) {
            console.error('Error al añadir producto:', error);
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
    new PedidoProveedorManager();
});