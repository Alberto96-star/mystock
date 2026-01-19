import pytest
from django.urls import reverse
from datetime import date

from pedidos.models import PedidoProveedor, DetallePedidoProveedor, OrdenVenta, DetalleOrdenVenta
from inventario.models import Inventario
from tests.pedidos.factories import (
    PedidoProveedorFactory, DetallePedidoProveedorFactory,
    OrdenVentaFactory, DetalleOrdenVentaFactory
)
from tests.factories import UserFactory
from tests.proveedores.factories import ProveedorFactory
from tests.clientes.factories import ClienteFactory
from tests.inventario.factories import ProductoFactory


@pytest.mark.django_db
class TestDashboardPedidosView:
    """
    Tests para la vista dashboard_pedidos.
    """

    def test_get_dashboard_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el dashboard se muestra correctamente.
        """
        url = reverse('dashboard_pedidos')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'pedidos/dashboard.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestRegistroPedidoProveedorView:
    """
    Tests para la vista registro_pedido_proveedor.
    """

    def test_get_registro_form_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el formulario de registro se muestra correctamente.
        """
        url = reverse('registro_pedido_proveedor')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'pedidos/registro_pedido_proveedor.html' in [
            t.name for t in response.templates]

    def test_post_registro_pedido_successfully(self, authenticated_client):
        """
        Test del caso feliz: registrar un pedido a proveedor.
        """
        url = reverse('registro_pedido_proveedor')
        proveedor = ProveedorFactory()
        producto = ProductoFactory()

        pedido_data = {
            'proveedor': proveedor.id,
            'fecha_pedido': date.today(),
            'fecha_entrega_estimada': date.today(),
            'notas': 'Notas del pedido',
            'producto_id': [producto.id],
            'cantidad': [5],
            'precio_unitario': [100.50],
            'igic_porcentaje': [7.00]
        }

        response = authenticated_client.post(url, data=pedido_data)

        assert response.status_code == 302
        assert response.url == reverse('listado_pedidos_proveedor')

        assert PedidoProveedor.objects.count() == 1
        pedido = PedidoProveedor.objects.first()
        assert pedido.proveedor == proveedor
        assert pedido.estado == 'pendiente'
        assert pedido.detalles.count() == 1

    def test_post_registro_pedido_without_products(self, authenticated_client):
        """
        Test que verifica que se puede crear pedido sin productos inicialmente.
        """
        url = reverse('registro_pedido_proveedor')
        proveedor = ProveedorFactory()

        pedido_data = {
            'proveedor': proveedor.id,
            'fecha_pedido': date.today(),
            'fecha_entrega_estimada': date.today(),
            'notas': 'Notas del pedido'
        }

        response = authenticated_client.post(url, data=pedido_data)

        assert response.status_code == 302  # Redirige porque crea el pedido
        assert PedidoProveedor.objects.count() == 1


@pytest.mark.django_db
class TestListadoPedidosProveedorView:
    """
    Tests para la vista listado_pedidos_proveedor.
    """

    def test_get_listado_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el listado se muestra correctamente.
        """
        url = reverse('listado_pedidos_proveedor')
        pedido = PedidoProveedorFactory()

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'pedidos/listado_pedidos_proveedor.html' in [
            t.name for t in response.templates]
        assert pedido in response.context['pedidos']

    def test_filter_by_estado(self, authenticated_client):
        """
        Test que verifica el filtro por estado.
        """
        url = reverse('listado_pedidos_proveedor')
        pedido_pendiente = PedidoProveedorFactory(estado='pendiente')
        pedido_completo = PedidoProveedorFactory(estado='recibido_completo')

        response = authenticated_client.get(url, {'estado': 'pendiente'})

        assert response.status_code == 200
        assert pedido_pendiente in response.context['pedidos']
        assert pedido_completo not in response.context['pedidos']


@pytest.mark.django_db
class TestDetallePedidoProveedorView:
    """
    Tests para la vista detalle_pedido_proveedor.
    """

    def test_get_detalle_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el detalle se muestra correctamente.
        """
        pedido = PedidoProveedorFactory()
        detalle = DetallePedidoProveedorFactory(pedido=pedido)
        url = reverse('detalle_pedido_proveedor',
                      kwargs={'pedido_id': pedido.id})

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'pedidos/detalle_pedido_proveedor.html' in [
            t.name for t in response.templates]
        assert response.context['pedido'] == pedido
        assert detalle in response.context['detalles']

    def test_post_update_estado_to_recibido_completo(self, authenticated_client):
        """
        Test que verifica la actualización de estado y el impacto en inventario.
        """
        pedido = PedidoProveedorFactory(estado='pendiente')
        detalle = DetallePedidoProveedorFactory(
            pedido=pedido, cantidad_pedida=10)
        # Crear inventario si no existe
        inventario, created = Inventario.objects.get_or_create(
            producto=detalle.producto,
            defaults={'cantidad_actual': 0, 'cantidad_reservada': 0}
        )
        inventario.cantidad_actual = 0
        inventario.save()

        url = reverse('detalle_pedido_proveedor',
                      kwargs={'pedido_id': pedido.id})

        response = authenticated_client.post(
            url, {'estado': 'recibido_completo'})

        assert response.status_code == 302
        pedido.refresh_from_db()
        assert pedido.estado == 'recibido_completo'

        # Verificar que el inventario se actualizó
        inventario.refresh_from_db()
        assert inventario.cantidad_actual == 10


@pytest.mark.django_db
class TestAgregarProductoPedidoProveedorView:
    """
    Tests para la vista agregar_producto_pedido_proveedor.
    """

    def test_post_agregar_producto_successfully(self, authenticated_client):
        """
        Test que verifica agregar producto a pedido existente.
        """
        pedido = PedidoProveedorFactory()
        producto = ProductoFactory()

        url = reverse('agregar_producto_pedido_proveedor',
                      kwargs={'pedido_id': pedido.id})

        data = {
            'producto': producto.id,
            'cantidad': 5,
            'precio_unitario': 50.00,
            'igic_porcentaje': 7.00
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert pedido.detalles.count() == 1
        detalle = pedido.detalles.first()
        assert detalle.producto == producto
        assert detalle.cantidad_pedida == 5


@pytest.mark.django_db
class TestEliminarProductoPedidoProveedorView:
    """
    Tests para la vista eliminar_producto_pedido_proveedor.
    """

    def test_post_eliminar_ultimo_producto_fails(self, authenticated_client):
        """
        Test que verifica que no se puede eliminar el último producto.
        """
        pedido = PedidoProveedorFactory()
        detalle = DetallePedidoProveedorFactory(pedido=pedido)

        url = reverse('eliminar_producto_pedido_proveedor',
                      kwargs={'detalle_id': detalle.id})

        response = authenticated_client.post(url)

        assert response.status_code == 302
        assert pedido.detalles.count() == 1  # No se eliminó

    def test_post_eliminar_producto_successfully(self, authenticated_client):
        """
        Test que verifica eliminar producto cuando hay más de uno.
        """
        pedido = PedidoProveedorFactory()
        detalle1 = DetallePedidoProveedorFactory(pedido=pedido)
        detalle2 = DetallePedidoProveedorFactory(pedido=pedido)

        url = reverse('eliminar_producto_pedido_proveedor',
                      kwargs={'detalle_id': detalle1.id})

        response = authenticated_client.post(url)

        assert response.status_code == 302
        assert pedido.detalles.count() == 1


@pytest.mark.django_db
class TestRegistroOrdenVentaView:
    """
    Tests para la vista registro_orden_venta.
    """

    def test_get_registro_form_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el formulario de registro se muestra correctamente.
        """
        url = reverse('registro_orden_venta')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'pedidos/registro_orden_venta.html' in [
            t.name for t in response.templates]

    def test_post_registro_orden_successfully(self, authenticated_client):
        """
        Test del caso feliz: registrar una orden de venta.
        """
        url = reverse('registro_orden_venta')
        cliente = ClienteFactory()
        producto = ProductoFactory()

        orden_data = {
            'cliente': cliente.id,
            'fecha_orden': date.today(),
            'fecha_entrega': date.today(),
            'metodo_pago': 'efectivo',
            'notas': 'Notas de la orden',
            'descuento_general': 0,
            'producto_id': [producto.id],
            'cantidad': [2],
            'precio_unitario': [200.00],
            'descuento_linea': [0],
            'igic_porcentaje': [7.00]
        }

        response = authenticated_client.post(url, data=orden_data)

        assert response.status_code == 302
        assert OrdenVenta.objects.count() == 1
        orden = OrdenVenta.objects.first()
        assert orden.cliente == cliente
        assert orden.estado == 'pendiente'
        assert orden.detalles.count() == 1

    def test_post_registro_orden_reserva_inventario(self, authenticated_client):
        """
        Test que verifica que al crear orden se reserva inventario.
        """
        cliente = ClienteFactory()
        producto = ProductoFactory()
        # Crear inventario si no existe
        inventario, created = Inventario.objects.get_or_create(
            producto=producto,
            defaults={'cantidad_actual': 10, 'cantidad_reservada': 0}
        )
        inventario.cantidad_actual = 10
        inventario.cantidad_reservada = 0
        inventario.save()

        url = reverse('registro_orden_venta')

        orden_data = {
            'cliente': cliente.id,
            'fecha_orden': date.today(),
            'fecha_entrega': date.today(),
            'metodo_pago': 'efectivo',
            'producto_id': [producto.id],
            'cantidad': [3],
            'precio_unitario': [100.00],
            'descuento_linea': [0],
            'igic_porcentaje': [0]
        }

        authenticated_client.post(url, data=orden_data)

        # Verificar reserva
        inventario.refresh_from_db()
        assert inventario.cantidad_reservada == 3


@pytest.mark.django_db
class TestListadoOrdenesVentaView:
    """
    Tests para la vista listado_ordenes_venta.
    """

    def test_get_listado_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el listado se muestra correctamente.
        """
        url = reverse('listado_ordenes_venta')
        orden = OrdenVentaFactory()

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'pedidos/listado_ordenes_venta.html' in [
            t.name for t in response.templates]
        assert orden in response.context['ordenes']


@pytest.mark.django_db
class TestDetalleOrdenVentaView:
    """
    Tests para la vista detalle_orden_venta.
    """

    def test_get_detalle_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el detalle se muestra correctamente.
        """
        orden = OrdenVentaFactory()
        detalle = DetalleOrdenVentaFactory(orden=orden)
        url = reverse('detalle_orden_venta', kwargs={'orden_id': orden.id})

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'pedidos/detalle_orden_venta.html' in [
            t.name for t in response.templates]
        assert response.context['orden'] == orden
        assert detalle in response.context['detalles']

    def test_post_update_estado_to_entregado(self, authenticated_client):
        """
        Test que verifica la actualización de estado y consumo de inventario.
        """
        orden = OrdenVentaFactory(estado='procesando')
        detalle = DetalleOrdenVentaFactory(orden=orden, cantidad=5)
        # Crear inventario si no existe
        inventario, created = Inventario.objects.get_or_create(
            producto=detalle.producto,
            defaults={'cantidad_actual': 10, 'cantidad_reservada': 5}
        )
        inventario.cantidad_actual = 10
        inventario.cantidad_reservada = 5
        inventario.save()

        url = reverse('detalle_orden_venta', kwargs={'orden_id': orden.id})

        response = authenticated_client.post(url, {'estado': 'entregado'})

        assert response.status_code == 302
        orden.refresh_from_db()
        assert orden.estado == 'entregado'

        # Verificar que el inventario se consumió
        inventario.refresh_from_db()
        assert inventario.cantidad_actual == 5  # 10 - 5
        assert inventario.cantidad_reservada == 0  # Reserva liberada


@pytest.mark.django_db
class TestAgregarProductoOrdenVentaView:
    """
    Tests para la vista agregar_producto_orden_venta.
    """

    def test_post_agregar_producto_reserva_inventario(self, authenticated_client):
        """
        Test que verifica agregar producto y reserva de inventario.
        """
        orden = OrdenVentaFactory(estado='pendiente')
        producto = ProductoFactory()
        # Crear inventario si no existe
        inventario, created = Inventario.objects.get_or_create(
            producto=producto,
            defaults={'cantidad_actual': 10, 'cantidad_reservada': 0}
        )
        inventario.cantidad_actual = 10
        inventario.cantidad_reservada = 0
        inventario.save()

        url = reverse('agregar_producto_orden_venta',
                      kwargs={'orden_id': orden.id})

        data = {
            'producto': producto.id,
            'cantidad': 2,
            'precio_unitario': 100.00,
            'descuento_linea': 0,
            'igic_porcentaje': 7.00
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert orden.detalles.count() == 1

        # Verificar reserva
        inventario.refresh_from_db()
        assert inventario.cantidad_reservada == 2
