// modalCrearProveedor.js
document.addEventListener('DOMContentLoaded', function () {
    const modalElement = document.getElementById('modalCrearProveedor');
    const formElement = document.getElementById('formCrearProveedor');
    const alertElement = document.getElementById('modalProveedorAlert');

    if (!modalElement || !formElement) {
        console.warn('Modal de proveedor no encontrado en esta página');
        return;
    }

    const modal = new bootstrap.Modal(modalElement);

    // Limpiar formulario cuando se abre el modal
    modalElement.addEventListener('show.bs.modal', function () {
        resetForm();
        hideAlert();
    });

    // Manejar envío del formulario
    formElement.addEventListener('submit', function (e) {
        e.preventDefault();

        // Deshabilitar el botón de envío para evitar múltiples envíos
        const submitBtn = formElement.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creando...';

        // Crear FormData del formulario
        const formData = new FormData(formElement);

        // Realizar petición AJAX
        fetch(formElement.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Éxito: mostrar mensaje y actualizar select
                    showAlert('success', data.message);

                    // Actualizar el select de proveedores
                    updateProveedorSelect(data.proveedor);

                    // Cerrar modal después de un breve delay
                    setTimeout(() => {
                        modal.hide();
                        resetForm();
                    }, 500);

                } else {
                    // Error: mostrar mensaje de error
                    showAlert('danger', data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'Error de conexión. Por favor, inténtelo de nuevo.');
            })
            .finally(() => {
                // Restaurar botón
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            });
    });

    /**
     * Muestra una alerta en el modal
     * @param {string} type - Tipo de alerta (success, danger, warning, info)
     * @param {string} message - Mensaje a mostrar
     */
    function showAlert(type, message) {
        alertElement.className = `alert alert-${type} alert-dismissible fade show`;
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        alertElement.classList.remove('d-none');

        // Scroll al top del modal para ver la alerta
        modalElement.querySelector('.modal-body').scrollTop = 0;
    }

    /**
     * Oculta la alerta del modal
     */
    function hideAlert() {
        alertElement.classList.add('d-none');
        alertElement.innerHTML = '';
    }

    /**
     * Resetea el formulario del modal
     */
    function resetForm() {
        formElement.reset();

        // Remover clases de validación si existen
        const formControls = formElement.querySelectorAll('.form-control');
        formControls.forEach(control => {
            control.classList.remove('is-valid', 'is-invalid');
        });
    }

    /**
     * Actualiza el select de proveedores con el nuevo proveedor creado
     * @param {Object} proveedor - Datos del proveedor creado
     */
    function updateProveedorSelect(proveedor) {
        const proveedorSelect = document.getElementById('id_proveedor');

        if (proveedorSelect) {
            // Crear nueva opción
            const newOption = document.createElement('option');
            newOption.value = proveedor.id;
            newOption.textContent = proveedor.nombre_empresa;
            newOption.selected = true; // Seleccionar automáticamente el nuevo proveedor

            // Añadir al select (después del placeholder)
            proveedorSelect.appendChild(newOption);

            // Opcional: Mostrar una notificación visual de que se ha actualizado
            proveedorSelect.classList.add('border-success');
            setTimeout(() => {
                proveedorSelect.classList.remove('border-success');
            }, 2000);

            console.log('Proveedor añadido al select:', proveedor.nombre_empresa);
        } else {
            console.warn('Select de proveedores no encontrado para actualizar');
        }
    }

    // Función global para abrir el modal (opcional, por si se necesita desde otro script)
    window.abrirModalCrearProveedor = function () {
        modal.show();
    };
});