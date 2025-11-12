from django.db import models
from django.contrib.auth.models import User
from proveedores.models import Proveedor
from clientes.models import Cliente
from inventario.models import Producto
from django.core.exceptions import ValidationError
import uuid


def generar_codigo_pedido():
    """ Esta funcion generara un codigo unico """

    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


def generar_codigo_orden():
    """ Esta funcion generara un codigo unico """

    return f"PED-{uuid.uuid4().hex[:8].upper()}"


class PedidoProveedor(models.Model):

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("recibido_parcial", "Recibido Parcial"),
        ("recibido_completo", "Recibido Completo"),
        ("cancelado", "Cancelado"),
    ]

    numero_pedido = models.CharField(
        max_length=40,
        default=generar_codigo_pedido,
        unique=True,
        editable=False,
        verbose_name="Número de Pedido"
    )
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, verbose_name="Proveedor")
    empleado_creador = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, verbose_name="Empleado Creador")
    fecha_pedido = models.DateField(verbose_name="Fecha de Pedido")
    fecha_entrega_estimada = models.DateField(
        verbose_name="Fecha Estimada de Entrega")
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default="pendiente", verbose_name="Estado")
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Subtotal")

    impuestos = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Impuestos")

    total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Total")

    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    creado_el = models.DateTimeField(
        auto_now_add=True, verbose_name="Creado el")
    actualizado_el = models.DateTimeField(
        auto_now=True, verbose_name="Actualizado el")

    def puede_cambiar_a_estado(self, nuevo_estado):
        """Valida si el pedido puede cambiar a un estado específico"""
        estados_que_requieren_productos = ['enviado', 'recibido', 'completado']

        if nuevo_estado in estados_que_requieren_productos:
            return self.detalles.exists()
        return True

    def puede_eliminar_producto(self):
        """Valida si se puede eliminar un producto (debe quedar al menos 1)"""
        return self.detalles.count() > 1

    def clean(self):
        """Validaciones del modelo"""

        # Validar que pedidos en ciertos estados tengan productos
        estados_que_requieren_productos = ['enviado', 'recibido', 'completado']

        if (self.estado in estados_que_requieren_productos and
                not self.detalles.exists()):
            raise ValidationError(
                f'Un pedido en estado "{self.get_estado_display()}" debe tener al menos un producto.'
            )

    class Meta:
        verbose_name = 'Pedido a Proveedor'
        verbose_name_plural = 'Pedidos a Proveedores'

    def __str__(self):
        return f"Número pedido: {self.numero_pedido} al proveedor: {self.proveedor}"


class DetallePedidoProveedor(models.Model):
    pedido = models.ForeignKey(
        PedidoProveedor, on_delete=models.CASCADE, related_name="detalles", verbose_name="Pedido")
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, verbose_name="Producto")
    empleado_creador = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, verbose_name="Empleado Creador")
    cantidad_pedida = models.PositiveIntegerField(
        verbose_name="Cantidad Pedida")
    cantidad_recibida = models.PositiveIntegerField(
        default=0, verbose_name="Cantidad Recibida")
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio Unitario")

    igic_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)

    igic_importe = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)

    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Subtotal")
    creado_el = models.DateTimeField(
        auto_now_add=True, verbose_name="Creado el")
    actualizado_el = models.DateTimeField(
        auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = 'Detalle de Pedido a Proveedor'
        verbose_name_plural = 'Detalles de Pedidos a Proveedores'

    def __str__(self):
        return f"Número de pedido: {self.pedido} creado por: {self.empleado_creador}"


class OrdenVenta(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("procesando", "Procesando"),
        ("entregado", "Entregado"),
        ("cancelado", "Cancelado"),
    ]

    numero_orden = models.CharField(
        max_length=40,
        default=generar_codigo_orden,
        unique=True,
        editable=False,
        verbose_name="Número de Orden"
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, verbose_name="Cliente")
    empleado_creador = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, verbose_name="Empleado Creador")
    fecha_orden = models.DateField(verbose_name="Fecha de Orden")
    fecha_entrega = models.DateField(verbose_name="Fecha de Entrega")
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default="pendiente", verbose_name="Estado")
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Subtotal")
    descuento = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Descuento")
    impuestos = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Impuestos")
    total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Total")
    metodo_pago = models.CharField(
        max_length=100, verbose_name="Método de Pago")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    creado_el = models.DateTimeField(
        auto_now_add=True, verbose_name="Creado el")
    actualizado_el = models.DateTimeField(
        auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = 'Orden de Venta'
        verbose_name_plural = 'Órdenes de Venta'

    def __str__(self):
        return f"Número de orden: {self.numero_orden} para el cliente: {self.cliente}"


class DetalleOrdenVenta(models.Model):

    empleado_creador = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, verbose_name="Empleado Creador")
    orden = models.ForeignKey(
        OrdenVenta, on_delete=models.CASCADE, related_name="detalles", verbose_name="Orden")
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, verbose_name="Producto")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    descuento_linea = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Descuento por Línea")

    igic_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)

    igic_importe = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Subtotal")
    creado_el = models.DateTimeField(
        auto_now_add=True, verbose_name="Creado el")
    actualizado_el = models.DateTimeField(
        auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = 'Detalle de Orden de Venta'
        verbose_name_plural = 'Detalles de Órdenes de Venta'

    def __str__(self):
        return f"Orden: {self.orden} creada por: {self.empleado_creador}"
