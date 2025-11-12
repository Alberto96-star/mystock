document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form').forEach(function (form) {
        // EXCLUIR el formulario del modal de crear cliente
        if (form.id === 'formCrearCliente' || form.id === 'formCrearProveedor') {
            return; // Saltar este formulario
        }

        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.addEventListener('click', function (e) {
                if (submitButton.disabled) {
                    e.preventDefault();
                    return;
                }
                submitButton.disabled = true;
                submitButton.innerText = 'Enviando...';
                form.submit();
            });
        }
    });
});