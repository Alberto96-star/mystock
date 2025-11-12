"""
Para que no se me olvide, aqui esta toda la logica para manejar los
signals o trigger para la base de datos y asi gestionar el inventario

Nota: estado enviado no se refleja en los flujos visuales se mantiene en los
signasl para un futuro uso
"""

from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import OrdenVenta, DetalleOrdenVenta, PedidoProveedor, DetallePedidoProveedor
from inventario.models import Inventario, Producto
import logging

logger = logging.getLogger(__name__)

# ===========================================
# SIGNALS PARA ÓRDENES DE VENTA
# ===========================================


@receiver(post_save, sender=DetalleOrdenVenta)
def detalle_orden_venta_post_save(sender, instance, created, **kwargs):
    """Maneja la creación y modificación de detalles de orden de venta"""
    try:
        # Solo procesar si la orden está en estado que requiere reserva
        if instance.orden.estado not in ['pendiente', 'procesando']:
            logger.info(
                f"Orden en estado '{instance.orden.estado}' - No se procesa reserva para detalle")
            return

        if created:
            # NUEVO DETALLE: Reservar stock (ahora siempre se puede)
            logger.info(
                f"Creando nuevo detalle - Producto: {instance.producto.nombre}, Cantidad: {instance.cantidad}")
            reservar_stock_detalle_orden(instance)
        else:
            # DETALLE MODIFICADO: Ajustar reservas
            cantidad_anterior = getattr(instance, '_cantidad_anterior', 0)
            producto_anterior = getattr(instance, '_producto_anterior', None)

            # Caso 1: Cambió el producto
            if producto_anterior and producto_anterior != instance.producto:
                logger.info(
                    f"Cambio de producto: {producto_anterior.nombre} -> {instance.producto.nombre}")
                # Liberar reserva del producto anterior
                liberar_reserva_producto(producto_anterior, cantidad_anterior)
                # Reservar para el nuevo producto
                reservar_stock_detalle_orden(instance)

            # Caso 2: Cambió la cantidad del mismo producto
            elif cantidad_anterior != instance.cantidad:
                diferencia = instance.cantidad - cantidad_anterior
                logger.info(
                    f"Cambio de cantidad para {instance.producto.nombre}: {cantidad_anterior} -> {instance.cantidad} (diferencia: {diferencia})")

                if diferencia > 0:
                    # Aumentó la cantidad - Reservar más stock
                    reservar_stock_adicional(instance, diferencia)
                else:
                    # Disminuyó la cantidad - Liberar stock
                    liberar_stock_detalle(instance, abs(diferencia))

    except Exception as e:
        logger.error(f"Error en post_save de DetalleOrdenVenta: {str(e)}")
        raise


@receiver(pre_save, sender=DetalleOrdenVenta)
def detalle_orden_venta_pre_save(sender, instance, **kwargs):
    """Captura la cantidad anterior del detalle antes de guardar"""
    if instance.pk:
        try:
            detalle_anterior = DetalleOrdenVenta.objects.get(pk=instance.pk)
            instance._cantidad_anterior = detalle_anterior.cantidad
            instance._producto_anterior = detalle_anterior.producto
        except DetalleOrdenVenta.DoesNotExist:
            instance._cantidad_anterior = 0
            instance._producto_anterior = None
    else:
        instance._cantidad_anterior = 0
        instance._producto_anterior = None


@receiver(pre_delete, sender=DetalleOrdenVenta)
def detalle_orden_venta_pre_delete(sender, instance, **kwargs):
    """Libera el stock reservado cuando se elimina un detalle"""
    try:
        # Solo procesar si la orden está en estado que requiere reserva
        if instance.orden.estado in ['pendiente', 'procesando']:
            logger.info(
                f"Eliminando detalle - Producto: {instance.producto.nombre}, Cantidad: {instance.cantidad}")
            liberar_reserva_producto(instance.producto, instance.cantidad)
        else:
            logger.info(
                f"Eliminando detalle de orden en estado '{instance.orden.estado}' - No se libera reserva")

    except Exception as e:
        logger.error(f"Error en pre_delete de DetalleOrdenVenta: {str(e)}")
        # No hacer raise aquí para no bloquear la eliminación


@receiver(pre_save, sender=OrdenVenta)
def orden_venta_pre_save(sender, instance, **kwargs):
    """Captura el estado anterior de la orden antes de guardar"""
    if instance.pk:
        try:
            orden_anterior = OrdenVenta.objects.get(pk=instance.pk)
            instance._estado_anterior = orden_anterior.estado
            logger.info(
                f"Estado anterior capturado: {orden_anterior.estado} -> {instance.estado}")
        except OrdenVenta.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=OrdenVenta)
def orden_venta_post_save(sender, instance, created, **kwargs):
    """Maneja los cambios de estado en órdenes de venta"""
    if created:
        # Para órdenes recién creadas, no hacer nada aquí
        # La reserva se maneja cuando se agregan los detalles
        logger.info(f"Orden de venta creada: {instance.id}")
        return

    estado_anterior = getattr(instance, '_estado_anterior', None)
    estado_actual = instance.estado

    logger.info(
        f"Procesando cambio de estado: {estado_anterior} -> {estado_actual}")

    if estado_anterior == estado_actual:
        logger.info("No hubo cambio de estado, saltando procesamiento")
        return  # No hubo cambio de estado

    # Procesar cada detalle de la orden

    for detalle in instance.detalles.all():
        procesar_cambio_estado_orden_venta(
            detalle, estado_anterior, estado_actual)


def procesar_cambio_estado_orden_venta(detalle, estado_anterior, estado_actual):
    """Procesa el cambio de estado para un detalle específico de orden de venta - SIMPLIFICADO"""
    try:
        with transaction.atomic():
            inventario, created = Inventario.objects.select_for_update().get_or_create(
                producto=detalle.producto,
                defaults={'cantidad_actual': 0, 'cantidad_reservada': 0}
            )

            if created:
                logger.info(
                    f"Inventario creado automáticamente para {detalle.producto.nombre}")

            cantidad = detalle.cantidad

            logger.info(f"Procesando detalle - Producto: {detalle.producto.nombre}, "
                        f"Cantidad: {cantidad}, Estado: {estado_anterior} -> {estado_actual}")

            # 1. LIBERAR RESERVAS DEL ESTADO ANTERIOR
            if estado_anterior in ['pendiente', 'procesando']:
                # Estaba reservado, liberar reserva
                inventario.cantidad_reservada -= cantidad
                logger.info(f"Liberando reserva de {cantidad} unidades")

            # 2. DEVOLVER STOCK SI VENÍA DE ENVIADO/ENTREGADO
            if estado_anterior in ['enviado', 'entregado']:
                # Estaba consumido, devolver al stock
                inventario.cantidad_actual += cantidad
                logger.info(f"Devolviendo {cantidad} unidades al stock actual")

            # 3. APLICAR NUEVO ESTADO
            if estado_actual in ['pendiente', 'procesando']:
                # Debe estar reservado
                inventario.cantidad_reservada += cantidad
                logger.info(f"Reservando {cantidad} unidades")

            elif estado_actual in ['enviado', 'entregado']:
                # Debe consumir stock actual
                inventario.cantidad_actual -= cantidad
                logger.info(
                    f"Consumiendo {cantidad} unidades del stock actual")

            # Para 'cancelado' no hace nada adicional, solo libera lo que tenía antes

            inventario.save()

            logger.info(
                f"✅ Inventario actualizado para {detalle.producto.nombre}: "
                f"Actual: {inventario.cantidad_actual}, Reservada: {inventario.cantidad_reservada}")

    except Exception as e:
        logger.error(
            f"❌ Error procesando cambio de estado orden venta: {str(e)}")
        logger.error(
            f"Detalle: Producto={detalle.producto.nombre}, Cantidad={detalle.cantidad}")
        logger.error(f"Estados: {estado_anterior} -> {estado_actual}")
        raise


# ===========================================
# FUNCIONES AUXILIARES PARA MANEJO DE RESERVAS
# ===========================================


def reservar_stock_detalle_orden(detalle):
    """Reserva stock cuando se agrega un detalle a una orden (ahora siempre posible)"""
    try:
        with transaction.atomic():
            inventario, created = Inventario.objects.select_for_update().get_or_create(
                producto=detalle.producto,
                defaults={'cantidad_actual': 0, 'cantidad_reservada': 0}
            )

            if created:
                logger.info(
                    f"Inventario creado automáticamente para {detalle.producto.nombre}")

            cantidad = detalle.cantidad

            # Ahora siempre reservamos, sin importar el stock disponible
            inventario.cantidad_reservada += cantidad
            inventario.save()

            logger.info(
                f"✅ Stock reservado - Producto: {detalle.producto.nombre}, "
                f"Cantidad: {cantidad}, "
                f"Actual: {inventario.cantidad_actual}, Reservada: {inventario.cantidad_reservada}")

    except Exception as e:
        logger.error(f"❌ Error reservando stock: {str(e)}")
        raise


def reservar_stock_adicional(detalle, cantidad_adicional):
    """Reserva stock adicional cuando se aumenta la cantidad de un detalle"""
    try:
        with transaction.atomic():
            inventario = Inventario.objects.select_for_update().get(producto=detalle.producto)

            # Ahora siempre reservamos la cantidad adicional
            inventario.cantidad_reservada += cantidad_adicional
            inventario.save()

            logger.info(
                f"✅ Stock adicional reservado - Producto: {detalle.producto.nombre}, "
                f"Cantidad adicional: {cantidad_adicional}, "
                f"Reservada total: {inventario.cantidad_reservada}")

    except Exception as e:
        logger.error(f"❌ Error reservando stock adicional: {str(e)}")
        raise


def ajustar_reserva_detalle_orden(detalle, diferencia_cantidad):
    """Ajusta la reserva cuando se modifica la cantidad de un detalle"""
    try:
        with transaction.atomic():
            inventario = Inventario.objects.select_for_update().get(producto=detalle.producto)

            if diferencia_cantidad > 0:
                # Se aumentó la cantidad, verificar stock disponible
                stock_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
                if stock_disponible >= diferencia_cantidad:
                    inventario.cantidad_reservada += diferencia_cantidad
                else:
                    raise ValueError(
                        f"Stock insuficiente para aumentar cantidad de {detalle.producto.nombre}")
            else:
                # Se redujo la cantidad, liberar reserva
                inventario.cantidad_reservada += diferencia_cantidad  # diferencia es negativa

            inventario.save()

            logger.info(
                f"Reserva ajustada para {detalle.producto.nombre}: "
                f"Cambio: {diferencia_cantidad}, "
                f"Reservada total: {inventario.cantidad_reservada}")

    except Exception as e:
        logger.error(f"Error ajustando reserva detalle orden: {str(e)}")
        raise


def liberar_stock_detalle(detalle, cantidad_a_liberar):
    """Libera stock cuando se reduce la cantidad de un detalle"""
    try:
        with transaction.atomic():
            inventario = Inventario.objects.select_for_update().get(producto=detalle.producto)

            # Simplemente liberamos la cantidad solicitada (puede generar reservas negativas)
            inventario.cantidad_reservada -= cantidad_a_liberar
            inventario.save()

            logger.info(
                f"✅ Stock liberado - Producto: {detalle.producto.nombre}, "
                f"Cantidad liberada: {cantidad_a_liberar}, "
                f"Reservada restante: {inventario.cantidad_reservada}")

    except Exception as e:
        logger.error(f"❌ Error liberando stock: {str(e)}")
        raise


def liberar_reserva_producto(producto, cantidad):
    """Libera la reserva completa de un producto (para eliminación o cambio de producto)"""
    try:
        with transaction.atomic():
            inventario = Inventario.objects.select_for_update().get(producto=producto)

            # Simplemente liberamos la cantidad solicitada
            inventario.cantidad_reservada -= cantidad
            inventario.save()

            logger.info(
                f"✅ Reserva liberada - Producto: {producto.nombre}, "
                f"Cantidad liberada: {cantidad}, "
                f"Reservada restante: {inventario.cantidad_reservada}")

    except Inventario.DoesNotExist:
        logger.warning(
            f"⚠️ No se encontró inventario para liberar del producto {producto.nombre}")
    except Exception as e:
        logger.error(f"❌ Error liberando reserva: {str(e)}")
        raise


# ===========================================
# FUNCIÓN PARA OBTENER ESTADO DEL INVENTARIO
# ===========================================

def obtener_estado_inventario(producto):
    """Función auxiliar para obtener el estado actual del inventario"""
    try:
        inventario = Inventario.objects.get(producto=producto)
        stock_disponible = inventario.cantidad_actual - inventario.cantidad_reservada

        return {
            'existe': True,
            'cantidad_actual': inventario.cantidad_actual,
            'cantidad_reservada': inventario.cantidad_reservada,
            'stock_disponible': stock_disponible,
            'inventario_negativo': inventario.cantidad_actual < 0 or inventario.cantidad_reservada < 0
        }
    except Inventario.DoesNotExist:
        return {
            'existe': False,
            'cantidad_actual': 0,
            'cantidad_reservada': 0,
            'stock_disponible': 0,
            'inventario_negativo': False
        }


# ===========================================
# SIGNALS PARA PEDIDOS A PROVEEDORES
# ===========================================


@receiver(pre_save, sender=PedidoProveedor)
def pedido_proveedor_pre_save(sender, instance, **kwargs):
    """Captura el estado anterior del pedido a proveedor antes de guardar"""
    if instance.pk:
        try:
            instance._estado_anterior = PedidoProveedor.objects.get(
                pk=instance.pk).estado
        except PedidoProveedor.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=PedidoProveedor)
def pedido_proveedor_post_save(sender, instance, created, **kwargs):
    """Maneja los cambios de estado en pedidos a proveedores"""
    if created:
        return

    estado_anterior = getattr(instance, '_estado_anterior', None)
    estado_actual = instance.estado

    if estado_anterior == estado_actual:
        return

    # Procesar cada detalle del pedido
    for detalle in instance.detalles.all():
        procesar_cambio_estado_pedido_proveedor(
            detalle, estado_anterior, estado_actual)


@receiver(post_save, sender=DetallePedidoProveedor)
def detalle_pedido_proveedor_post_save(sender, instance, created, **kwargs):
    """Maneja cambios en cantidad_recibida para recepciones parciales"""
    if created:
        return

    # Solo procesar si el pedido está en estado recibido_parcial
    if instance.pedido.estado != 'recibido_parcial':
        return

    cantidad_recibida_anterior = getattr(
        instance, '_cantidad_recibida_anterior', 0)
    cantidad_recibida_actual = instance.cantidad_recibida

    if cantidad_recibida_anterior != cantidad_recibida_actual:
        diferencia = cantidad_recibida_actual - cantidad_recibida_anterior

        if diferencia != 0:
            actualizar_inventario_por_recepcion(instance.producto, diferencia)


@receiver(pre_save, sender=DetallePedidoProveedor)
def detalle_pedido_proveedor_pre_save(sender, instance, **kwargs):
    """Captura valores anteriores del detalle de pedido a proveedor"""
    if instance.pk:
        try:
            detalle_anterior = DetallePedidoProveedor.objects.get(
                pk=instance.pk)
            instance._cantidad_recibida_anterior = detalle_anterior.cantidad_recibida
            instance._cantidad_pedida_anterior = detalle_anterior.cantidad_pedida
            instance._producto_anterior = detalle_anterior.producto
        except DetallePedidoProveedor.DoesNotExist:
            instance._cantidad_recibida_anterior = 0
            instance._cantidad_pedida_anterior = 0
            instance._producto_anterior = None
    else:
        instance._cantidad_recibida_anterior = 0
        instance._cantidad_pedida_anterior = 0
        instance._producto_anterior = None


def procesar_cambio_estado_pedido_proveedor(detalle, estado_anterior, estado_actual):
    """Procesa el cambio de estado para un detalle específico de pedido a proveedor"""
    try:
        with transaction.atomic():
            inventario, created = Inventario.objects.select_for_update().get_or_create(
                producto=detalle.producto,
                defaults={'cantidad_actual': 0, 'cantidad_reservada': 0}
            )

            if created:
                logger.info(
                    f"Inventario creado automáticamente para {detalle.producto.nombre}")

            # Lógica según el cambio de estado
            if estado_actual == 'recibido_completo':
                if estado_anterior == 'recibido_parcial':
                    # Sumar solo lo que falta por recibir
                    cantidad_pendiente = detalle.cantidad_pedida - detalle.cantidad_recibida
                    inventario.cantidad_actual += cantidad_pendiente
                    # Actualizar cantidad_recibida para que coincida con cantidad_pedida
                    detalle.cantidad_recibida = detalle.cantidad_pedida
                    detalle.save()
                elif estado_anterior in ['pendiente', 'enviado']:
                    # Sumar toda la cantidad pedida
                    inventario.cantidad_actual += detalle.cantidad_pedida
                    detalle.cantidad_recibida = detalle.cantidad_pedida
                    detalle.save()
                elif estado_anterior == 'cancelado':
                    # Restar lo que se había restado al cancelar y sumar lo nuevo
                    if estado_anterior == 'cancelado':
                        # El inventario ya estaba ajustado, solo sumar lo recibido
                        inventario.cantidad_actual += detalle.cantidad_pedida
                        detalle.cantidad_recibida = detalle.cantidad_pedida
                        detalle.save()

            elif estado_actual == 'recibido_parcial':
                if estado_anterior == 'recibido_completo':
                    # Restar la diferencia entre lo que se había sumado y lo realmente recibido
                    cantidad_a_restar = detalle.cantidad_pedida - detalle.cantidad_recibida
                    inventario.cantidad_actual -= cantidad_a_restar
                elif estado_anterior in ['pendiente', 'enviado']:
                    # Sumar solo lo recibido hasta ahora
                    inventario.cantidad_actual += detalle.cantidad_recibida
                elif estado_anterior == 'cancelado':
                    # Sumar lo recibido
                    inventario.cantidad_actual += detalle.cantidad_recibida

            elif estado_actual == 'cancelado' or estado_actual == 'pendiente':
                # Restar según lo que se había sumado en el estado anterior
                if estado_anterior == 'recibido_completo':
                    inventario.cantidad_actual -= detalle.cantidad_pedida
                elif estado_anterior == 'recibido_parcial':
                    inventario.cantidad_actual -= detalle.cantidad_recibida
                # Si venía de pendiente o enviado, no hay nada que restar

            inventario.save()

            logger.info(f"Inventario actualizado para {detalle.producto.nombre}: "
                        f"Cantidad actual: {inventario.cantidad_actual}")

    except Exception as e:
        logger.error(
            f"Error procesando cambio de estado pedido proveedor: {str(e)}")
        raise


def actualizar_inventario_pedido_proveedor(detalle, cantidad_cambio):
    """Actualiza el inventario para pedidos a proveedores (permite inventarios negativos)"""
    try:
        with transaction.atomic():
            inventario, created = Inventario.objects.select_for_update().get_or_create(
                producto=detalle.producto,
                defaults={'cantidad_actual': 0, 'cantidad_reservada': 0}
            )

            if created:
                logger.info(
                    f"Inventario creado automáticamente para {detalle.producto.nombre}")

            # Sumar o restar según el cambio (ahora permite inventarios negativos)
            inventario.cantidad_actual += cantidad_cambio
            inventario.save()

            logger.info(
                f"Inventario actualizado para {detalle.producto.nombre}: "
                f"Cantidad actual: {inventario.cantidad_actual} (cambio: {cantidad_cambio})")

    except Exception as e:
        logger.error(
            f"Error actualizando inventario pedido proveedor: {str(e)}")
        raise


def actualizar_inventario_por_recepcion(producto, diferencia_cantidad):
    """Actualiza el inventario cuando cambia la cantidad_recibida en recepciones parciales"""
    try:
        with transaction.atomic():
            inventario, created = Inventario.objects.select_for_update().get_or_create(
                producto=producto,
                defaults={'cantidad_actual': 0, 'cantidad_reservada': 0}
            )

            if created:
                logger.info(
                    f"Inventario creado automáticamente para {producto.nombre}")

            inventario.cantidad_actual += diferencia_cantidad
            inventario.save()

            logger.info(
                f"Inventario actualizado por cambio en recepción - Producto: {producto.nombre}, "
                f"Diferencia: {diferencia_cantidad}, Cantidad actual: {inventario.cantidad_actual}")

    except Exception as e:
        logger.error(f"Error actualizando inventario por recepción: {str(e)}")
        raise
