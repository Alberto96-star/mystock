// detail_product.js - Funcionalidades para el detalle de productos

document.addEventListener('DOMContentLoaded', function () {
    // Elementos del DOM
    const cantidadActualInput = document.getElementById('cantidad_actual');
    const cantidadReservadaInput = document.getElementById('cantidad_reservada');
    const stockMinimoInput = document.getElementById('stock_minimo');

    // Elementos de las tarjetas informativas
    const stockActualCard = document.querySelector('.card:nth-child(1) h3');
    const stockReservadoCard = document.querySelector('.card:nth-child(2) h3');
    const stockDisponibleCard = document.querySelector('.card:nth-child(3) h3');

    // Función para actualizar las tarjetas en tiempo real
    function actualizarTarjetasInfo() {
        const cantidadActual = parseInt(cantidadActualInput.value) || 0;
        const cantidadReservada = parseInt(cantidadReservadaInput.value) || 0;
        const stockMinimo = parseInt(stockMinimoInput.value) || 0;
        const disponible = cantidadActual - cantidadReservada;

        // Actualizar valores en las tarjetas
        if (stockActualCard) stockActualCard.textContent = cantidadActual;
        if (stockReservadoCard) stockReservadoCard.textContent = cantidadReservada;
        if (stockDisponibleCard) stockDisponibleCard.textContent = disponible;

        // Cambiar colores según el estado del stock
        actualizarColoresStock(cantidadActual, stockMinimo, disponible);
    }

    // Función para actualizar colores según el estado del stock
    function actualizarColoresStock(cantidadActual, stockMinimo, disponible) {
        const stockActualElement = stockActualCard?.closest('.card');
        const stockDisponibleElement = stockDisponibleCard?.closest('.card');

        if (stockActualElement) {
            // Remover clases existentes
            stockActualElement.classList.remove('border-danger', 'border-success');
            stockActualCard.classList.remove('text-danger', 'text-success');

            // Agregar clases según el estado
            if (cantidadActual <= stockMinimo) {
                stockActualElement.classList.add('border-danger');
                stockActualCard.classList.add('text-danger');
            } else {
                stockActualElement.classList.add('border-success');
                stockActualCard.classList.add('text-success');
            }
        }

        if (stockDisponibleElement) {
            // Remover clases existentes
            stockDisponibleElement.classList.remove('border-danger', 'border-primary');
            stockDisponibleCard.classList.remove('text-danger', 'text-primary');

            // Agregar clases según disponibilidad
            if (disponible <= 0) {
                stockDisponibleElement.classList.add('border-danger');
                stockDisponibleCard.classList.add('text-danger');
            } else {
                stockDisponibleElement.classList.add('border-primary');
                stockDisponibleCard.classList.add('text-primary');
            }
        }
    }

    // Validación para cantidad reservada
    function validarCantidadReservada() {
        const cantidadActual = parseInt(cantidadActualInput.value) || 0;
        const cantidadReservada = parseInt(cantidadReservadaInput.value) || 0;

        if (cantidadReservada > cantidadActual) {
            cantidadReservadaInput.setCustomValidity('La cantidad reservada no puede ser mayor que la cantidad actual');
            cantidadReservadaInput.classList.add('is-invalid');
            mostrarTooltipError(cantidadReservadaInput, 'La cantidad reservada no puede ser mayor que la cantidad actual');
        } else {
            cantidadReservadaInput.setCustomValidity('');
            cantidadReservadaInput.classList.remove('is-invalid');
            ocultarTooltipError(cantidadReservadaInput);
        }
    }

    // Validación para valores negativos
    function validarValoresNegativos(input, nombreCampo) {
        const valor = parseFloat(input.value) || 0;

        if (valor < 0) {
            input.setCustomValidity(`${nombreCampo} no puede ser negativo`);
            input.classList.add('is-invalid');
            mostrarTooltipError(input, `${nombreCampo} no puede ser negativo`);
        } else {
            input.setCustomValidity('');
            input.classList.remove('is-invalid');
            ocultarTooltipError(input);
        }
    }

    // Función para mostrar tooltip de error
    function mostrarTooltipError(elemento, mensaje) {
        // Remover tooltip existente
        ocultarTooltipError(elemento);

        // Crear nuevo tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'invalid-tooltip position-absolute';
        tooltip.style.display = 'block';
        tooltip.style.top = '100%';
        tooltip.style.left = '0';
        tooltip.style.zIndex = '1000';
        tooltip.textContent = mensaje;

        elemento.parentNode.style.position = 'relative';
        elemento.parentNode.appendChild(tooltip);
        elemento.dataset.hasTooltip = 'true';
    }

    // Función para ocultar tooltip de error
    function ocultarTooltipError(elemento) {
        if (elemento.dataset.hasTooltip) {
            const tooltip = elemento.parentNode.querySelector('.invalid-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
            delete elemento.dataset.hasTooltip;
        }
    }

    // Obtén las referencias a los elementos input por su ID
    // Es crucial que estos selectores ('precio_compra', 'precio_venta') coincidan con los 'id' de tus inputs en el HTML.
    const precioCompraInput = document.getElementById('precio_compra');
    const precioVentaInput = document.getElementById('precio_venta');

    // Función para calcular margen de ganancia
    function calcularMargenGanancia() {
        // Usamos ?.value para acceder al valor de forma segura, y parseFloat para convertir a número.
        // Si el valor no existe o no es un número, se usa 0 como fallback.
        const precioCompra = parseFloat(precioCompraInput?.value) || 0;
        const precioVenta = parseFloat(precioVentaInput?.value) || 0;

        // Obtenemos las referencias a los elementos donde se mostrarán los resultados
        const margenEurosElement = document.getElementById('margen-euros');
        const margenPorcentajeElement = document.getElementById('margen-porcentaje');

        // Solo calculamos si ambos precios son mayores que 0
        if (precioCompra > 0 && precioVenta > 0) {
            // Calcular margen en euros
            const margenEuros = precioVenta - precioCompra;

            // Calcular margen en porcentaje
            // Nos aseguramos de no dividir por cero si precioCompra es 0
            const margenPorcentaje = precioCompra !== 0 ? (margenEuros / precioCompra) * 100 : 0;

            // Actualizar el texto y la clase (color) del margen en euros
            if (margenEurosElement) {
                margenEurosElement.textContent = `€${margenEuros.toFixed(2)}`;
                margenEurosElement.className = `h5 mb-0 ${margenEuros >= 0 ? 'text-success' : 'text-danger'}`;
            }

            // Actualizar el texto y la clase (color) del margen en porcentaje
            if (margenPorcentajeElement) {
                margenPorcentajeElement.textContent = `${margenPorcentaje.toFixed(2)}%`;
                margenPorcentajeElement.className = `h5 mb-0 ${margenPorcentaje >= 0 ? 'text-success' : 'text-danger'}`;
            }

            // Actualizar el color del borde de la tarjeta del margen
            const margenCard = margenEurosElement?.closest('.card');
            if (margenCard) {
                margenCard.classList.remove('border-success', 'border-danger', 'border-info');
                if (margenEuros > 0) {
                    margenCard.classList.add('border-success');
                } else if (margenEuros < 0) {
                    margenCard.classList.add('border-danger');
                } else {
                    margenCard.classList.add('border-info'); // Margen neutro o cero
                }
            }
        } else {
            // Si los precios no son válidos, resetear los valores y colores
            if (margenEurosElement) {
                margenEurosElement.textContent = '€0.00';
                margenEurosElement.className = 'h5 mb-0 text-muted';
            }

            if (margenPorcentajeElement) {
                margenPorcentajeElement.textContent = '0%';
                margenPorcentajeElement.className = 'h5 mb-0 text-muted';
            }

            // Resetear el borde de la tarjeta a un estado neutral
            const margenCard = margenEurosElement?.closest('.card');
            if (margenCard) {
                margenCard.classList.remove('border-success', 'border-danger');
                margenCard.classList.add('border-info');
            }
        }
    }

    // Prevenir envío del formulario con Enter - NUEVO
    function prevenirEnterEnInputs() {
        const inputs = document.querySelectorAll('input:not([type="submit"]):not([readonly]), select');
        inputs.forEach(input => {
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    // Opcional: mover al siguiente campo
                    const nextInput = findNextInput(this);
                    if (nextInput) {
                        nextInput.focus();
                    }
                }
            });
        });
    }

    // Función auxiliar para encontrar el siguiente input
    function findNextInput(currentInput) {
        const inputs = Array.from(document.querySelectorAll('input:not([readonly]), select, textarea'));
        const currentIndex = inputs.indexOf(currentInput);
        return inputs[currentIndex + 1] || null;
    }

    // Event listeners
    if (cantidadActualInput) {
        cantidadActualInput.addEventListener('input', function () {
            validarValoresNegativos(this, 'La cantidad actual');
            validarCantidadReservada();
            actualizarTarjetasInfo();
        });
    }

    if (cantidadReservadaInput) {
        cantidadReservadaInput.addEventListener('input', function () {
            validarValoresNegativos(this, 'La cantidad reservada');
            validarCantidadReservada();
            actualizarTarjetasInfo();
        });
    }

    if (stockMinimoInput) {
        stockMinimoInput.addEventListener('input', function () {
            validarValoresNegativos(this, 'El stock mínimo');
            actualizarTarjetasInfo();
        });
    }

    if (precioCompraInput) {
        precioCompraInput.addEventListener('input', function () {
            validarValoresNegativos(this, 'El precio de compra');
            calcularMargenGanancia();
        });
    }

    if (precioVentaInput) {
        precioVentaInput.addEventListener('input', function () {
            validarValoresNegativos(this, 'El precio de venta');
            calcularMargenGanancia();
        });
    }

    // Validación del formulario antes del envío
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function (e) {
            // Validar todos los campos antes del envío
            let hasErrors = false;

            // Validar campos numéricos
            const numericalInputs = [cantidadActualInput, cantidadReservadaInput, stockMinimoInput, precioCompraInput, precioVentaInput];
            numericalInputs.forEach(input => {
                if (input && input.value !== '') {
                    const valor = parseFloat(input.value);
                    if (valor < 0) {
                        hasErrors = true;
                        input.classList.add('is-invalid');
                    }
                }
            });

            // Validar cantidad reservada vs actual
            if (cantidadReservadaInput && cantidadActualInput) {
                const cantidadReservada = parseInt(cantidadReservadaInput.value) || 0;
                const cantidadActual = parseInt(cantidadActualInput.value) || 0;

                if (cantidadReservada > cantidadActual) {
                    hasErrors = true;
                    cantidadReservadaInput.classList.add('is-invalid');
                }
            }

            // Validar campos requeridos
            const requiredInputs = document.querySelectorAll('input[required], select[required]');
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    hasErrors = true;
                    input.classList.add('is-invalid');
                }
            });

            if (hasErrors) {
                e.preventDefault();
                // Scroll al primer error
                const firstError = document.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }

                // Mostrar alerta
                mostrarAlerta('Por favor corrige los errores antes de continuar', 'danger');
            }
        });
    }

    // Función para mostrar alertas
    function mostrarAlerta(mensaje, tipo = 'info') {
        const alertContainer = document.querySelector('.alert') || document.querySelector('h2');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${tipo} alert-dismissible fade show`;
            alert.innerHTML = `
                ${mensaje}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            alertContainer.parentNode.insertBefore(alert, alertContainer.nextSibling);

            // Auto-hide después de 5 segundos
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 5000);
        }
    }

    // Inicializar todas las funciones
    prevenirEnterEnInputs();
    actualizarTarjetasInfo();
    calcularMargenGanancia();
});