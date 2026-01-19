import pytest
from django.urls import reverse
from django.contrib import messages

from clientes.models import Cliente
from tests.factories import UserFactory
from tests.clientes.factories import ClienteFactory


@pytest.mark.django_db
class TestClientRegisterView:
    """
    Tests para la vista client_register.
    """

    def test_get_register_form_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el formulario de registro se muestra correctamente.
        """
        url = reverse('registro_cliente')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'clientes/clients_form.html' in [
            t.name for t in response.templates]

    def test_register_client_successfully_with_all_fields(self, authenticated_client, empleado):
        """
        Test del caso feliz: registrar un cliente con todos los campos completos.
        """
        url = reverse('registro_cliente')
        client_data = {
            'nombreComercial': 'Empresa Test S.L.',
            'cif': 'B12345678',
            'telefonoOficina': '912345678',
            'telefonoSegundario': '656789012',
            'email': 'test@empresa.com',
            'direccionFiscal': 'Calle Mayor 123',
            'ciudadFiscal': 'Madrid',
            'codigoPostalFiscal': 28001,
            'direccionEntrega': 'Calle Menor 456',
            'ciudadEntrega': 'Barcelona',
            'codigoPostalEntrega': 18001,
            'estadoCliente': 'on',
            'username': empleado.username
        }

        response = authenticated_client.post(url, data=client_data)

        assert response.status_code == 302
        assert response.url == reverse('listado_clientes')

        assert Cliente.objects.count() == 1
        cliente = Cliente.objects.first()
        assert cliente.nombre_comercial == 'Empresa Test S.L.'
        assert cliente.cif == 'B12345678'
        assert cliente.telefono_oficina == '912345678'
        assert cliente.telefono_adicional == '656789012'
        assert cliente.email == 'test@empresa.com'
        assert cliente.direccion_fiscal == 'Calle Mayor 123'
        assert cliente.ciudad_fiscal == 'Madrid'
        assert cliente.codigo_postal_fiscal == 28001
        assert cliente.direccion_entrega == 'Calle Menor 456'
        assert cliente.ciudad_entrega == 'Barcelona'
        assert cliente.codigo_postal_entrega == 18001
        assert cliente.activo is True
        assert cliente.empleado_asignado == empleado

    def test_register_client_with_minimal_fields(self, authenticated_client):
        """
        Test registrar cliente con campos mínimos.
        """
        url = reverse('registro_cliente')
        client_data = {
            'nombreComercial': 'Empresa Mínima',
            'cif': 'A98765432',
            'telefonoOficina': '911111111',
            'direccionFiscal': 'Dirección Básica',
            'ciudadFiscal': 'Ciudad Básica',
            'codigoPostalFiscal': 12345,
            'estadoCliente': 'on'
        }

        response = authenticated_client.post(url, data=client_data)

        assert response.status_code == 302
        assert Cliente.objects.count() == 1
        cliente = Cliente.objects.first()
        assert cliente.nombre_comercial == 'Empresa Mínima'
        assert cliente.email is None
        assert cliente.empleado_asignado is None

    def test_register_client_duplicate_cif(self, authenticated_client):
        """
        Test que verifica que no se permiten CIF duplicados.
        """
        # Crear cliente existente
        ClienteFactory(cif='B12345678')

        url = reverse('registro_cliente')
        client_data = {
            'nombreComercial': 'Empresa Duplicada',
            'cif': 'B12345678',  # CIF duplicado
            'telefonoOficina': '912345678',
            'direccionFiscal': 'Calle Test',
            'ciudadFiscal': 'Madrid',
            'estadoCliente': 'on'
        }

        response = authenticated_client.post(url, data=client_data)

        assert response.status_code == 302
        assert response.url == reverse('registro_cliente')
        assert Cliente.objects.count() == 1  # No se creó nuevo

    def test_register_client_invalid_employee(self, authenticated_client):
        """
        Test que verifica manejo de empleado inexistente.
        """
        url = reverse('registro_cliente')
        client_data = {
            'nombreComercial': 'Empresa Test',
            'cif': 'B12345678',
            'telefonoOficina': '912345678',
            'direccionFiscal': 'Calle Test',
            'ciudadFiscal': 'Madrid',
            'codigoPostalFiscal': 28001,
            'estadoCliente': 'on',
            'username': 'INVALID_USER'
        }

        response = authenticated_client.post(url, data=client_data)

        assert response.status_code == 200  # No redirige
        assert Cliente.objects.count() == 0


@pytest.mark.django_db
class TestListClientView:
    """
    Tests para la vista list_client.
    """

    def test_get_list_clients_renders_correctly(self, authenticated_client):
        """
        Test que verifica que la lista de clientes se muestra correctamente.
        """
        url = reverse('listado_clientes')
        cliente = ClienteFactory()

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'clientes/list_client.html' in [
            t.name for t in response.templates]
        assert cliente in response.context['clientes']

    def test_filter_clients_by_name(self, authenticated_client):
        """
        Test que verifica el filtro por nombre comercial.
        """
        url = reverse('listado_clientes')
        cliente1 = ClienteFactory(nombre_comercial='Empresa ABC')
        cliente2 = ClienteFactory(nombre_comercial='Otra Empresa')

        response = authenticated_client.get(url, {'buscarCliente': 'ABC'})

        assert response.status_code == 200
        assert cliente1 in response.context['clientes']
        assert cliente2 not in response.context['clientes']


@pytest.mark.django_db
class TestDetailClientView:
    """
    Tests para la vista detail_client.
    """

    def test_get_detail_client_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el detalle del cliente se muestra correctamente.
        """
        cliente = ClienteFactory()
        url = reverse('detalle_cliente', kwargs={'cliente_id': cliente.id})

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'clientes/detail_client.html' in [
            t.name for t in response.templates]
        assert response.context['cliente'] == cliente

    def test_update_client_successfully(self, authenticated_client, empleado):
        """
        Test que verifica la actualización exitosa de un cliente.
        """
        cliente = ClienteFactory()
        url = reverse('detalle_cliente', kwargs={'cliente_id': cliente.id})

        update_data = {
            'nombreComercial': 'Empresa Actualizada',
            'email': 'nuevo@email.com',
            'telefonoOficina': '987654321',
            'telefonoAdicional': '654321987',
            'direccionFiscal': 'Nueva Dirección Fiscal',
            'ciudadFiscal': 'Nueva Ciudad',
            'codigoPostalFiscal': 54321,
            'direccionEntrega': 'Nueva Dirección Entrega',
            'ciudadEntrega': 'Ciudad Entrega',
            'codigoPostalEntrega': 12345,
            'cif': 'C98765432',
            'estadoCliente': 'on',
            'username': empleado.username
        }

        response = authenticated_client.post(url, data=update_data)

        assert response.status_code == 302
        assert response.url == reverse('listado_clientes')

        cliente.refresh_from_db()
        assert cliente.nombre_comercial == 'Empresa Actualizada'
        assert cliente.email == 'nuevo@email.com'
        assert cliente.cif == 'C98765432'
        assert cliente.empleado_asignado == empleado

    def test_update_client_duplicate_cif(self, authenticated_client):
        """
        Test que verifica que no se permite actualizar a un CIF duplicado.
        """
        cliente1 = ClienteFactory(cif='B12345678')
        cliente2 = ClienteFactory(cif='A98765432')

        url = reverse('detalle_cliente', kwargs={'cliente_id': cliente2.id})

        update_data = {
            'cif': 'B12345678',  # CIF de cliente1
            'estadoCliente': 'on'
        }

        response = authenticated_client.post(url, data=update_data)

        # En tests, IntegrityError causa 400; en producción se captura y render 200
        assert response.status_code == 400

    def test_update_client_invalid_employee(self, authenticated_client):
        """
        Test que verifica manejo de empleado inexistente en actualización.
        """
        cliente = ClienteFactory()
        url = reverse('detalle_cliente', kwargs={'cliente_id': cliente.id})

        update_data = {
            'nombreComercial': cliente.nombre_comercial,
            'cif': cliente.cif,
            'telefonoOficina': cliente.telefono_oficina,
            'direccionFiscal': cliente.direccion_fiscal,
            'ciudadFiscal': cliente.ciudad_fiscal,
            'codigoPostalFiscal': cliente.codigo_postal_fiscal,
            'estadoCliente': 'on',
            'username': 'INVALID_USER'
        }

        response = authenticated_client.post(url, data=update_data)

        assert response.status_code == 302  # Redirige, pero con warning
        cliente.refresh_from_db()
        assert cliente.empleado_asignado is None
