import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDate, FuzzyDecimal, FuzzyInteger
from datetime import date

from pedidos.models import PedidoProveedor, DetallePedidoProveedor, OrdenVenta, DetalleOrdenVenta
from tests.factories import UserFactory
from tests.proveedores.factories import ProveedorFactory
from tests.clientes.factories import ClienteFactory
from tests.inventario.factories import ProductoFactory


class PedidoProveedorFactory(DjangoModelFactory):
    """
    Factory para crear pedidos a proveedores de prueba.
    """
    class Meta:
        model = PedidoProveedor

    proveedor = factory.SubFactory(ProveedorFactory)
    empleado_creador = factory.SubFactory(UserFactory)
    fecha_pedido = FuzzyDate(date(2024, 1, 1), date(2026, 12, 31))
    fecha_entrega_estimada = FuzzyDate(date(2024, 1, 1), date(2026, 12, 31))
    estado = FuzzyChoice(['pendiente', 'recibido_parcial',
                         'recibido_completo', 'cancelado'])
    subtotal = FuzzyDecimal(100.0, 10000.0, precision=2)
    impuestos = FuzzyDecimal(0.0, 1000.0, precision=2)
    total = FuzzyDecimal(100.0, 11000.0, precision=2)
    notas = factory.Faker('sentence', locale='es_ES')


class DetallePedidoProveedorFactory(DjangoModelFactory):
    """
    Factory para crear detalles de pedidos a proveedores de prueba.
    """
    class Meta:
        model = DetallePedidoProveedor

    pedido = factory.SubFactory(PedidoProveedorFactory)
    producto = factory.SubFactory(ProductoFactory)
    empleado_creador = factory.SubFactory(UserFactory)
    cantidad_pedida = FuzzyInteger(1, 100)
    cantidad_recibida = FuzzyInteger(0, 100)
    precio_unitario = FuzzyDecimal(10.0, 1000.0, precision=2)
    igic_porcentaje = FuzzyDecimal(0.0, 21.0, precision=2)
    igic_importe = FuzzyDecimal(0.0, 1000.0, precision=2)
    subtotal = FuzzyDecimal(10.0, 10000.0, precision=2)


class OrdenVentaFactory(DjangoModelFactory):
    """
    Factory para crear órdenes de venta de prueba.
    """
    class Meta:
        model = OrdenVenta

    cliente = factory.SubFactory(ClienteFactory)
    empleado_creador = factory.SubFactory(UserFactory)
    fecha_orden = FuzzyDate(date(2024, 1, 1), date(2026, 12, 31))
    fecha_entrega = FuzzyDate(date(2024, 1, 1), date(2026, 12, 31))
    estado = FuzzyChoice(['pendiente', 'procesando', 'entregado', 'cancelado'])
    subtotal = FuzzyDecimal(100.0, 10000.0, precision=2)
    descuento = FuzzyDecimal(0.0, 1000.0, precision=2)
    impuestos = FuzzyDecimal(0.0, 1000.0, precision=2)
    total = FuzzyDecimal(100.0, 11000.0, precision=2)
    metodo_pago = FuzzyChoice(
        ['efectivo', 'tarjeta', 'transferencia', 'cheque'])
    notas = factory.Faker('sentence', locale='es_ES')


class DetalleOrdenVentaFactory(DjangoModelFactory):
    """
    Factory para crear detalles de órdenes de venta de prueba.
    """
    class Meta:
        model = DetalleOrdenVenta

    orden = factory.SubFactory(OrdenVentaFactory)
    producto = factory.SubFactory(ProductoFactory)
    empleado_creador = factory.SubFactory(UserFactory)
    cantidad = FuzzyInteger(1, 100)
    precio_unitario = FuzzyDecimal(10.0, 1000.0, precision=2)
    descuento_linea = FuzzyDecimal(0.0, 100.0, precision=2)
    igic_porcentaje = FuzzyDecimal(0.0, 21.0, precision=2)
    igic_importe = FuzzyDecimal(0.0, 1000.0, precision=2)
    subtotal = FuzzyDecimal(10.0, 10000.0, precision=2)
