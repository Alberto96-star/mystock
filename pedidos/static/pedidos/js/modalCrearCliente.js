document.addEventListener('DOMContentLoaded', function () {
    // Manejar el envío del formulario de crear cliente
    const formCrearCliente = document.getElementById('formCrearCliente');

    if (formCrearCliente) {
        formCrearCliente.addEventListener('submit', function (e) {
            e.preventDefault();

            // Validar formulario antes del envío
            if (!validarFormularioCliente()) {
                return;
            }

            // Deshabilitar botón de envío para evitar doble click
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creando...';

            const formData = new FormData(this);

            // Obtener el token CSRF
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',  // Este es el header clave
                    'X-CSRFToken': csrfToken,              // Token CSRF
                    // NO incluir 'Content-Type' cuando usas FormData
                }
            })
                .then(response => {

                    // Verificar si la respuesta es JSON
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return response.json();
                    } else {
                        // Si no es JSON, probablemente es una respuesta HTML (error)
                        return response.text().then(text => {
                            throw new Error(`Respuesta no JSON recibida: ${text.substring(0, 200)}...`);
                        });
                    }
                })
                .then(data => {

                    if (data.success) {
                        // Cerrar modal
                        const modal = bootstrap.Modal.getInstance(document.getElementById('modalCrearCliente'));
                        if (modal) {
                            modal.hide();
                        }

                        // Limpiar formulario
                        this.reset();

                        // Actualizar select de clientes si existe
                        actualizarSelectCliente(data);

                        // Mostrar mensaje de éxito
                        mostrarAlerta('success', data.message);
                    } else {
                        // Mostrar mensaje de error
                        mostrarAlerta('danger', data.message || 'Error desconocido al crear el cliente');
                    }
                })
                .catch(error => {
                    console.error('Error completo:', error);
                    mostrarAlerta('danger', 'Error de conexión o respuesta inválida. Inténtalo de nuevo.');
                })
                .finally(() => {
                    // Rehabilitar botón
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                });
        });
    }

    // Limpiar formulario cuando se cierre el modal
    const modalCrearCliente = document.getElementById('modalCrearCliente');
    if (modalCrearCliente) {
        modalCrearCliente.addEventListener('hidden.bs.modal', function () {
            const form = document.getElementById('formCrearCliente');
            if (form) {
                form.reset();
                // Limpiar mensajes de error si existen
                const alertContainer = document.querySelector('.alert-container');
                if (alertContainer) {
                    alertContainer.innerHTML = '';
                }
            }
        });
    }
});

/**
 * Actualiza el select de clientes con el nuevo cliente creado
 * @param {Object} data - Datos del cliente creado
 */
function actualizarSelectCliente(data) {
    // Buscar select de cliente (pueden tener diferentes IDs)
    const posiblesSelects = ['cliente', 'clienteId', 'cliente_id', 'id_cliente'];
    let selectCliente = null;

    for (const id of posiblesSelects) {
        selectCliente = document.getElementById(id);
        if (selectCliente) break;
    }

    if (selectCliente) {
        // Crear nueva opción
        const newOption = document.createElement('option');
        newOption.value = data.cliente_id;
        newOption.textContent = data.cliente_nombre;

        // Agregar al select
        selectCliente.appendChild(newOption);

        // Seleccionar la nueva opción
        selectCliente.value = data.cliente_id;

        // Disparar evento change si hay listeners
        selectCliente.dispatchEvent(new Event('change'));

    } else {
        console.warn('No se encontró el select de clientes para actualizar');
    }
}

/**
 * Muestra alertas dinámicas en la página
 * @param {string} type - Tipo de alerta (success, danger, warning, info)
 * @param {string} message - Mensaje a mostrar
 */
function mostrarAlerta(type, message) {
    // Crear HTML de la alerta
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${getIconForAlertType(type)}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    // Buscar contenedor para alertas
    let container = document.querySelector('.alert-container');

    // Si no existe, crear uno al principio del contenido principal
    if (!container) {
        const mainContent = document.querySelector('.container, .container-fluid, main, .content');
        if (mainContent) {
            container = document.createElement('div');
            container.className = 'alert-container mb-3';
            mainContent.insertBefore(container, mainContent.firstChild);
        }
    }

    if (container) {
        container.innerHTML = alertHtml;

        // Hacer scroll al top para mostrar la alerta
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Auto-ocultar después de 5 segundos para alertas de éxito
        if (type === 'success') {
            setTimeout(() => {
                const alert = container.querySelector('.alert');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }
}

/**
 * Obtiene el icono apropiado para cada tipo de alerta
 * @param {string} type - Tipo de alerta
 * @returns {string} - Clase del icono
 */
function getIconForAlertType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Valida el formulario antes del envío
 * @returns {boolean} - True si el formulario es válido
 */
function validarFormularioCliente() {
    const form = document.getElementById('formCrearCliente');
    if (!form) return false;

    const camposRequeridos = [
        { name: 'nombreComercial', label: 'Nombre Comercial' },
        { name: 'cif', label: 'CIF' },
        { name: 'telefonoOficina', label: 'Teléfono de Oficina' },
        { name: 'direccionFiscal', label: 'Dirección Fiscal' },
        { name: 'ciudadFiscal', label: 'Ciudad Fiscal' },
        { name: 'codigoPostalFiscal', label: 'Código Postal Fiscal' }
    ];

    for (const campo of camposRequeridos) {
        const input = form.querySelector(`[name="${campo.name}"]`);
        if (!input || !input.value.trim()) {
            mostrarAlerta('warning', `El campo "${campo.label}" es obligatorio.`);
            input.focus();
            return false;
        }
    }

    // Validar formato de email si se proporciona
    const emailInput = form.querySelector('[name="email"]');
    if (emailInput && emailInput.value.trim()) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailInput.value.trim())) {
            mostrarAlerta('warning', 'El formato del email no es válido.');
            emailInput.focus();
            return false;
        }
    }

    return true;
}