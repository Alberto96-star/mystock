import pytest
from django.urls import reverse

from proveedores.models import Proveedor
from tests.proveedores.factories import ProveedorFactory


@pytest.mark.django_db
class TestSupplierRegisterView:
    """
    Tests para la vista supplier_register.
    """

    def test_get_register_form_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el formulario de registro se muestra correctamente.
        """
        url = reverse('registro_proveedores')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'proveedores/supplier_form.html' in [
            t.name for t in response.templates]

    def test_register_supplier_successfully(self, authenticated_client):
        """
        Test del caso feliz: registrar un proveedor con todos los campos.
        """
        url = reverse('registro_proveedores')
        supplier_data = {
            'nombreEmpresa': 'Empresa Proveedora S.A.',
            'cif': 'B12345678',
            'nombreContacto': 'Juan Pérez',
            'telefonoOficina': '912345678',
            'telefonoSegundario': '654321987',
            'email': 'contacto@empresa.com',
            'direccionFiscal': 'Calle Mayor 123',
            'ciudadFiscal': 'Madrid',
            'codigoPostalFiscal': '28001',
            'condicionesPago': 'Pago a 30 días'
        }

        response = authenticated_client.post(url, data=supplier_data)

        assert response.status_code == 302
        assert response.url == reverse('listado_proveedor')

        assert Proveedor.objects.count() == 1
        proveedor = Proveedor.objects.first()
        assert proveedor.nombre_empresa == 'Empresa Proveedora S.A.'
        assert proveedor.cif == 'B12345678'
        assert proveedor.contacto_nombre == 'Juan Pérez'
        assert proveedor.telefono_oficina == '912345678'
        assert proveedor.telefono_segundario == '654321987'
        assert proveedor.email == 'contacto@empresa.com'
        assert proveedor.direccion == 'Calle Mayor 123'
        assert proveedor.ciudad == 'Madrid'
        assert proveedor.codigo_postal == 28001
        assert proveedor.condiciones_pago == 'Pago a 30 días'

    def test_register_supplier_with_minimal_fields(self, authenticated_client):
        """
        Test registrar proveedor con campos mínimos.
        """
        url = reverse('registro_proveedores')
        supplier_data = {
            'nombreEmpresa': 'Empresa Mínima',
            'cif': 'A98765432',
            'nombreContacto': 'Ana López',
            'telefonoOficina': '911111111'
        }

        response = authenticated_client.post(url, data=supplier_data)

        assert response.status_code == 302
        assert Proveedor.objects.count() == 1
        proveedor = Proveedor.objects.first()
        assert proveedor.nombre_empresa == 'Empresa Mínima'
        assert proveedor.email is None
        assert proveedor.direccion is None

    def test_register_supplier_duplicate_cif(self, authenticated_client):
        """
        Test que verifica que no se permiten CIF duplicados.
        """
        # Crear proveedor existente
        ProveedorFactory(cif='B12345678')

        url = reverse('registro_proveedores')
        supplier_data = {
            'nombreEmpresa': 'Empresa Duplicada',
            'cif': 'B12345678',  # CIF duplicado
            'nombreContacto': 'Pedro García',
            'telefonoOficina': '912345678'
        }

        response = authenticated_client.post(url, data=supplier_data)

        assert response.status_code == 200  # No redirige
        assert Proveedor.objects.count() == 1  # No se creó nuevo

    def test_register_supplier_invalid_postal_code(self, authenticated_client):
        """
        Test que verifica validación de código postal inválido.
        """
        url = reverse('registro_proveedores')
        supplier_data = {
            'nombreEmpresa': 'Empresa Test',
            'cif': 'B12345678',
            'nombreContacto': 'Juan Pérez',
            'telefonoOficina': '912345678',
            'codigoPostalFiscal': 'abc'  # Código postal inválido
        }

        response = authenticated_client.post(url, data=supplier_data)

        assert response.status_code == 200  # No redirige
        assert Proveedor.objects.count() == 0

    def test_register_supplier_missing_required_fields(self, authenticated_client):
        """
        Test que verifica validación de campos obligatorios.
        """
        url = reverse('registro_proveedores')
        supplier_data = {
            'nombreEmpresa': '',
            'cif': 'B12345678',
            'telefonoOficina': '912345678'
        }

        response = authenticated_client.post(url, data=supplier_data)

        assert response.status_code == 200
        assert Proveedor.objects.count() == 0


@pytest.mark.django_db
class TestListSupplierView:
    """
    Tests para la vista list_supplier.
    """

    def test_get_list_suppliers_renders_correctly(self, authenticated_client):
        """
        Test que verifica que la lista de proveedores se muestra correctamente.
        """
        url = reverse('listado_proveedor')
        proveedor = ProveedorFactory()

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'proveedores/list_supplier.html' in [
            t.name for t in response.templates]
        assert proveedor in response.context['proveedores']

    def test_filter_suppliers_by_name(self, authenticated_client):
        """
        Test que verifica el filtro por nombre de empresa.
        """
        url = reverse('listado_proveedor')
        proveedor1 = ProveedorFactory(nombre_empresa='Empresa ABC')
        proveedor2 = ProveedorFactory(nombre_empresa='Otra Empresa')

        response = authenticated_client.get(url, {'buscarProveedor': 'ABC'})

        assert response.status_code == 200
        assert proveedor1 in response.context['proveedores']
        assert proveedor2 not in response.context['proveedores']


@pytest.mark.django_db
class TestDetailsSupplierView:
    """
    Tests para la vista details_supplier.
    """

    def test_get_detail_supplier_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el detalle del proveedor se muestra correctamente.
        """
        proveedor = ProveedorFactory()
        url = reverse('editar_proveedor', kwargs={'supplier_id': proveedor.id})

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'proveedores/supplier_edit.html' in [
            t.name for t in response.templates]
        assert response.context['proveedor'] == proveedor

    def test_update_supplier_successfully(self, authenticated_client):
        """
        Test que verifica la actualización exitosa de un proveedor.
        """
        proveedor = ProveedorFactory()
        url = reverse('editar_proveedor', kwargs={'supplier_id': proveedor.id})

        update_data = {
            'nombreEmpresa': 'Empresa Actualizada S.A.',
            'cif': 'C98765432',
            'nombreContacto': 'María González',
            'telefonoOficina': '987654321',
            'telefonoSegundario': '654321098',
            'email': 'nuevo@empresa.com',
            'direccionFiscal': 'Nueva Dirección 456',
            'ciudadFiscal': 'Barcelona',
            'codigoPostalFiscal': '08001',
            'condicionesPago': 'Pago a 60 días'
        }

        response = authenticated_client.post(url, data=update_data)

        assert response.status_code == 302
        assert response.url == reverse('listado_proveedor')

        proveedor.refresh_from_db()
        assert proveedor.nombre_empresa == 'Empresa Actualizada S.A.'
        assert proveedor.cif == 'C98765432'
        assert proveedor.contacto_nombre == 'María González'
        assert proveedor.telefono_oficina == '987654321'
        assert proveedor.email == 'nuevo@empresa.com'
        assert proveedor.ciudad == 'Barcelona'
        assert proveedor.codigo_postal == 8001

    def test_update_supplier_duplicate_cif(self, authenticated_client):
        """
        Test que verifica que no se permite actualizar a un CIF duplicado.
        """
        proveedor1 = ProveedorFactory(cif='B12345678')
        proveedor2 = ProveedorFactory(cif='A98765432')

        url = reverse('editar_proveedor', kwargs={
                      'supplier_id': proveedor2.id})

        update_data = {
            'nombreEmpresa': proveedor2.nombre_empresa,
            'cif': 'B12345678',  # CIF de proveedor1
            'nombreContacto': proveedor2.contacto_nombre,
            'telefonoOficina': proveedor2.telefono_oficina
        }

        response = authenticated_client.post(url, data=update_data)

        assert response.status_code == 200  # No redirige
        # En producción se captura el error y render, en tests puede ser 400

    def test_update_supplier_invalid_postal_code(self, authenticated_client):
        """
        Test que verifica validación de código postal inválido en actualización.
        """
        proveedor = ProveedorFactory()
        url = reverse('editar_proveedor', kwargs={'supplier_id': proveedor.id})

        update_data = {
            'nombreEmpresa': proveedor.nombre_empresa,
            'cif': proveedor.cif,
            'nombreContacto': proveedor.contacto_nombre,
            'telefonoOficina': proveedor.telefono_oficina,
            'codigoPostalFiscal': 'invalid'
        }

        response = authenticated_client.post(url, data=update_data)

        assert response.status_code == 200  # No redirige

    def test_update_supplier_missing_required_fields(self, authenticated_client):
        """
        Test que verifica validación de campos obligatorios en actualización.
        """
        proveedor = ProveedorFactory()
        url = reverse('editar_proveedor', kwargs={'supplier_id': proveedor.id})

        update_data = {
            'nombreEmpresa': '',
            'cif': proveedor.cif,
            'telefonoOficina': proveedor.telefono_oficina
        }

        response = authenticated_client.post(url, data=update_data)

        assert response.status_code == 200  # No redirige
