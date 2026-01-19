import pytest
from django.test import Client
from django.contrib.auth import get_user_model

from tests.factories import UserFactory

User = get_user_model()


@pytest.fixture
def client():
    """
    Cliente HTTP básico de Django para hacer requests.
    Renombro a 'client' en lugar de 'api_client' porque es más
    estándar en proyectos Django.
    """
    return Client()


@pytest.fixture
def authenticated_client(db):
    """
    Cliente autenticado con un usuario de prueba.

    Este fixture es crítico para tus vistas porque todas
    tienen el decorator @login_required.
    """

    django_client = Client()

    user = UserFactory(
        username='testuser',
        password='testpass123'
    )

    # force_login es más rápido que login() porque no hashea el password
    # client.force_login(user)

    # logged_in = client.login(username='testuser', password='testpass123')

    # if not logged_in:
    #     raise RuntimeError("Failed to log in user in test fixture")

    # # Guardamos referencia al user para que los tests puedan accederlo
    # client.user = user

    # return client

    django_client.force_login(user)

    django_client.user = user

    return django_client


@pytest.fixture
def empleado(db):
    """
    Fixture que crea un empleado (User) que puede ser asignado a clientes.

    Útil cuando múltiples tests necesitan el mismo empleado.
    """
    return UserFactory(username='EMP0001', password='testpass123')
