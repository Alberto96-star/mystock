document.addEventListener('DOMContentLoaded', function () {
    const cookieModal = document.getElementById('cookieModal');
    const acceptButton = document.getElementById('acceptCookiesBtn');
    const cookieAccepted = localStorage.getItem('MyStock_cookies_accepted');

    // Inicialmente, oculta la modal. Luego la mostramos solo si no ha sido aceptada.
    // Esto previene un "flash" de la modal antes de que el JS actúe.
    cookieModal.style.display = 'none';
    document.body.style.overflow = ''; // Asegura que el scroll del body esté normal por defecto

    // Si el usuario NO ha aceptado las cookies antes, muestra la modal
    if (!cookieAccepted) {
        cookieModal.style.display = 'block'; // Muestra la ventana modal
        document.body.style.overflow = 'hidden'; // Bloquea el scroll de la página de fondo
    }

    // Cuando el usuario hace clic en "Entendido"
    if (acceptButton) {
        acceptButton.addEventListener('click', function () {
            localStorage.setItem('MyStock_cookies_accepted', 'true'); // Guarda la preferencia en localStorage
            cookieModal.style.display = 'none'; // Oculta la ventana modal
            document.body.style.overflow = ''; // Restaura el scroll de la página de fondo
        });
    }
});