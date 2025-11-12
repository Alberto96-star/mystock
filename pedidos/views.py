"""
Esta son todas las funciones que se manejan
para la gestion de pedidos a proveedores y clientes
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from datetime import datetime, date
from proveedores.models import Proveedor
from .models import PedidoProveedor, DetallePedidoProveedor, OrdenVenta, DetalleOrdenVenta
from clientes.models import Cliente
from inventario.models import Producto, Inventario, CategoriaProducto


# ================================
# VISTAS PARA PEDIDOS A PROVEEDORES
# ================================

@login_required
def registro_pedido_proveedor(request):
    """Crear un nuevo pedido a proveedor"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos del pedido principal
                proveedor_id = request.POST.get('proveedor')
                fecha_pedido = request.POST.get('fecha_pedido')
                fecha_entrega_estimada = request.POST.get(
                    'fecha_entrega_estimada')
                notas = request.POST.get('notas', '')

                # Crear el pedido
                pedido = PedidoProveedor.objects.create(
                    proveedor_id=proveedor_id,
                    empleado_creador=request.user,
                    fecha_pedido=fecha_pedido,
                    fecha_entrega_estimada=fecha_entrega_estimada,
                    notas=notas,
                    subtotal=0,
                    impuestos=0,
                    total=0
                )

                # Procesar productos
                productos_ids = request.POST.getlist('producto_id')
                cantidades = request.POST.getlist('cantidad')
                precios = request.POST.getlist('precio_unitario')
                igic_porcentajes = request.POST.getlist('igic_porcentaje')

                subtotal_sin_igic_total = 0
                igic_total = 0

                for i, producto_id in enumerate(productos_ids):
                    if producto_id and cantidades[i] and precios[i]:
                        cantidad = int(cantidades[i])
                        precio_unitario = float(precios[i])
                        igic_porcentaje = float(
                            igic_porcentajes[i]) if igic_porcentajes[i] else 7.00
                        # Calcular subtotal sin IGIC
                        subtotal_sin_igic = cantidad * precio_unitario

                        # Calcular IGIC para esta línea
                        igic_importe = subtotal_sin_igic * \
                            (igic_porcentaje / 100)

                        # Subtotal final de la línea (con IGIC)
                        subtotal_linea = subtotal_sin_igic + igic_importe

                        DetallePedidoProveedor.objects.create(
                            pedido=pedido,
                            producto_id=producto_id,
                            empleado_creador=request.user,
                            cantidad_pedida=cantidad,
                            precio_unitario=precio_unitario,
                            igic_porcentaje=igic_porcentaje,
                            igic_importe=igic_importe,
                            subtotal=subtotal_linea
                        )

                        # Acumular totales
                        subtotal_sin_igic_total += subtotal_sin_igic
                        igic_total += igic_importe

                # Actualizar totales del pedido

                total_final = subtotal_sin_igic_total + igic_total

                pedido.subtotal = subtotal_sin_igic_total
                pedido.impuestos = igic_total
                pedido.total = total_final
                pedido.save()

                messages.success(
                    request, f'Pedido {pedido.numero_pedido} creado exitosamente')
                return redirect('listado_pedidos_proveedor')

        except ValueError as ve:
            messages.error(
                request, f'Error en los datos proporcionados: {type(ve)}, {str(ve)}')

        except Exception as e:
            messages.error(request, f'Error al crear el pedido: {str(e)}')
            print(f'el error es {type(e).__name__} - {str(e)}')

    proveedores = Proveedor.objects.all()
    productos = Producto.objects.all().prefetch_related('inventarios')
    categorias = CategoriaProducto.objects.all()

    context = {
        'proveedores': proveedores,
        'productos': productos,
        'categorias': categorias,
        'fecha_actual': date.today()
    }

    return render(request, 'pedidos/registro_pedido_proveedor.html', context)


@login_required
def listado_pedidos_proveedor(request):
    """Listar todos los pedidos a proveedores"""
    pedidos = PedidoProveedor.objects.select_related(
        'proveedor', 'empleado_creador').order_by('-fecha_pedido')

    # Filtros opcionales
    estado_filtro = request.GET.get('estado')
    proveedor_filtro = request.GET.get('proveedor')

    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    if proveedor_filtro:
        pedidos = pedidos.filter(proveedor_id=proveedor_filtro)

    context = {
        'pedidos': pedidos,
        'estados': PedidoProveedor.ESTADOS,
        'proveedores': Proveedor.objects.all(),
        'estado_actual': estado_filtro,
        'proveedor_actual': proveedor_filtro
    }

    return render(request, 'pedidos/listado_pedidos_proveedor.html', context)


@login_required
def detalle_pedido_proveedor(request, pedido_id):
    """Ver/editar detalle de un pedido a proveedor"""
    pedido = get_object_or_404(
        PedidoProveedor.objects.select_related('proveedor'), id=pedido_id)
    detalles = pedido.detalles.select_related('producto')
    productos = Producto.objects.all().prefetch_related('inventarios')
    categorias = CategoriaProducto.objects.all()

    if request.method == 'POST':
        # Actualizar estado si se envió
        try:
            nuevo_estado = request.POST.get('estado')
            if nuevo_estado and nuevo_estado in dict(PedidoProveedor.ESTADOS):

                # VALIDACIÓN: No permitir ciertos estados si no hay productos
                estados_que_requieren_productos = [
                    'recibido_parcial', 'recibido_completo']  # Ajusta según tus estados

                if (nuevo_estado in estados_que_requieren_productos and
                        not detalles.exists()):
                    messages.error(
                        request,
                        f'No puedes cambiar el estado a "{dict(PedidoProveedor.ESTADOS)[nuevo_estado]}" '
                        'porque el pedido no tiene productos asociados.'
                    )
                    return redirect('detalle_pedido_proveedor', pedido_id=pedido.id)

                pedido.estado = nuevo_estado

                # Si el estado es recibido_parcial, actualizamos cantidades recibidas
                if nuevo_estado == 'recibido_parcial':
                    for detalle in detalles:
                        key = f'cantidad_recibida_{detalle.id}'
                        nueva_cantidad = request.POST.get(key)

                        if nueva_cantidad is not None:
                            try:
                                nueva_cantidad = int(nueva_cantidad)
                                if 0 <= nueva_cantidad <= detalle.cantidad_pedida:
                                    detalle.cantidad_recibida = nueva_cantidad
                                    detalle.save()
                                else:
                                    messages.warning(
                                        request, f'Cantidad inválida para {detalle.producto.nombre}.')
                            except ValueError:
                                messages.warning(
                                    request, f'Valor inválido en la cantidad para {detalle.producto.nombre}.')

                            # Guardar notas generales
                            notas = request.POST.get('notas')
                            pedido.notas = notas
                pedido.save()
                messages.success(
                    request, f'Estado actualizado a {pedido.get_estado_display()}')
                return redirect('detalle_pedido_proveedor', pedido_id=pedido.id)
        except ValueError:
            messages.error(
                request, 'No se pueden almacenar los datos, por favor eliminar la orden por completo y reacerla')
            return redirect('detalle_pedido_proveedor', pedido_id=pedido.id)

    context = {
        'pedido': pedido,
        'productos': productos,
        'categorias': categorias,
        'detalles': detalles,
        'estados': PedidoProveedor.ESTADOS,
        'tiene_productos': detalles.exists(),
        'total_productos': detalles.count(),
        'puede_editar': pedido.estado not in ['recibido_parcial', 'recibido_completo'],
    }

    return render(request, 'pedidos/detalle_pedido_proveedor.html', context)


@login_required
def agregar_producto_pedido_proveedor(request, pedido_id):
    """Agregar producto a un pedido existente"""
    pedido = get_object_or_404(PedidoProveedor, id=pedido_id)

    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto')
            cantidad = int(request.POST.get('cantidad'))
            precio_unitario = float(request.POST.get('precio_unitario'))
            igic_porcentaje = float(request.POST.get(
                'igic_porcentaje'))  # NUEVO: Capturar IGIC

            subtotal_linea = cantidad * precio_unitario
            # Calcular impuestos de esta línea específica
            igic_importe_linea = subtotal_linea * (igic_porcentaje / 100)

            DetallePedidoProveedor.objects.create(
                pedido=pedido,
                producto_id=producto_id,
                empleado_creador=request.user,
                cantidad_pedida=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal_linea,
                igic_porcentaje=igic_porcentaje,
                igic_importe=igic_importe_linea
            )

            # Recalcular totales del pedido
            _recalcular_totales_pedido_proveedor(pedido)

            messages.success(request, 'Producto agregado exitosamente')

        except Exception as e:
            messages.error(request, f'Error al agregar producto: {str(e)}')

    return redirect('detalle_pedido_proveedor', pedido_id=pedido.id)


@login_required
def eliminar_producto_pedido_proveedor(request, detalle_id):
    """Eliminar producto de un pedido"""
    try:
        detalle = get_object_or_404(DetallePedidoProveedor, id=detalle_id)
        pedido = detalle.pedido

        # VALIDACIÓN: Verificar si es el último producto
        total_productos = pedido.detalles.count()

        if total_productos <= 1:
            messages.error(
                request,
                'No puedes eliminar este producto porque el pedido debe tener al menos un producto. '
                'Si deseas cancelar el pedido, cambia su estado a "Cancelado".'
            )
            return redirect('detalle_pedido_proveedor', pedido_id=pedido.id)

        detalle.delete()
        _recalcular_totales_pedido_proveedor(pedido)

        messages.success(request, 'Producto eliminado del pedido')
        return redirect('detalle_pedido_proveedor', pedido_id=pedido.id)

    except Exception as e:
        print(f'Error al eliminar el producto {type(e)}, {str(e)}')
        messages.error(request, 'Error al eliminar producto')
        return redirect('detalle_pedido_proveedor', pedido_id=pedido.id)


@login_required
def eliminar_pedido_proveedor(request, pedido_id):
    """Eliminar pedido completo"""
    if request.method == 'POST':
        pedido = get_object_or_404(PedidoProveedor, id=pedido_id)

        # Solo permitir eliminar pedidos en estado 'pendiente' o 'cancelado'
        if pedido.estado not in ['pendiente', 'cancelado']:
            messages.error(
                request,
                'Solo se pueden eliminar pedidos en estado "Pendiente" o "Cancelado"'
            )
            return redirect('detalle_pedido_proveedor', pedido_id=pedido.id)
        codigo_pedido = pedido.numero_pedido
        pedido.delete()
        messages.success(
            request, f'Pedido {codigo_pedido} eliminado exitosamente')
        return redirect('listado_pedidos_proveedor')

    return redirect('listado_pedidos_proveedor')


def _recalcular_totales_pedido_proveedor(pedido):
    """Función auxiliar para recalcular totales de un pedido a proveedor"""
    try:
        detalles = pedido.detalles.all()

        # Calcular subtotal (suma de todos los subtotales de línea)
        subtotal = sum(detalle.subtotal for detalle in detalles)

        # Calcular impuestos (suma de todos los igic_importe por línea)
        impuestos = sum(detalle.igic_importe for detalle in detalles)

        total = subtotal + impuestos

        # Calcular el porcentaje promedio de IGIC del pedido (para mostrar en template)
        if subtotal > 0:
            igic_porcentaje_promedio = (impuestos / subtotal) * 100
        else:
            igic_porcentaje_promedio = 0

        pedido.subtotal = subtotal
        pedido.impuestos = impuestos
        pedido.total = total
        pedido.igic_porcentaje = igic_porcentaje_promedio  # Actualizar porcentaje promedio
        pedido.save()

        print(
            f"Totales recalculados - Subtotal: {subtotal}, Impuestos: {impuestos}, Total: {total}")

    except Exception as e:
        print(
            f'Error al recalcular totales del pedido proveedor: {type(e)}, {str(e)}')

# ============================
# VISTAS PARA ÓRDENES DE VENTA
# ============================


@login_required
def registro_orden_venta(request):
    """Crear una nueva orden de venta"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Datos de la orden principal
                cliente_id = request.POST.get('cliente')
                fecha_orden = request.POST.get('fecha_orden')
                fecha_entrega = request.POST.get('fecha_entrega')
                metodo_pago = request.POST.get('metodo_pago')
                notas = request.POST.get('notas', '')

                # Crear la orden
                orden = OrdenVenta.objects.create(
                    cliente_id=cliente_id,
                    empleado_creador=request.user,
                    fecha_orden=fecha_orden,
                    fecha_entrega=fecha_entrega,
                    metodo_pago=metodo_pago,
                    notas=notas,
                    subtotal=0,
                    descuento=0,
                    impuestos=0,
                    total=0
                )

                # Procesar productos
                productos_ids = request.POST.getlist('producto_id')
                cantidades = request.POST.getlist('cantidad')
                precios = request.POST.getlist('precio_unitario')
                descuentos_linea = request.POST.getlist('descuento_linea')
                igic_porcentajes = request.POST.getlist('igic_porcentaje')

                subtotal_sin_igic_total = 0
                igic_total = 0

                for i, producto_id in enumerate(productos_ids):
                    if producto_id and cantidades[i] and precios[i]:
                        cantidad = int(cantidades[i])
                        precio_unitario = float(precios[i])
                        descuento_linea = float(
                            descuentos_linea[i]) if descuentos_linea[i] else 0
                        igic_porcentaje = float(
                            igic_porcentajes[i]) if igic_porcentajes[i] else 7.00

                        # Calcular subtotal sin IGIC
                        subtotal_sin_igic = (
                            cantidad * precio_unitario) - descuento_linea

                        # Calcular IGIC para esta línea
                        igic_importe = subtotal_sin_igic * \
                            (igic_porcentaje / 100)

                        # Subtotal final de la línea (con IGIC)
                        subtotal_linea = subtotal_sin_igic + igic_importe

                        DetalleOrdenVenta.objects.create(
                            orden=orden,
                            producto_id=producto_id,
                            empleado_creador=request.user,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            descuento_linea=descuento_linea,
                            igic_porcentaje=igic_porcentaje,
                            igic_importe=igic_importe,
                            subtotal=subtotal_linea
                        )

                        # Acumular totales
                        subtotal_sin_igic_total += subtotal_sin_igic
                        igic_total += igic_importe

                # Actualizar totales de la orden
                descuento_general = float(
                    request.POST.get('descuento_general', 0))

                # Aplicar descuento general al subtotal sin IGIC
                subtotal_con_descuento_general = subtotal_sin_igic_total - descuento_general

                # IGIC ya calculado por línea
                igic_final = igic_total

                total_final = subtotal_con_descuento_general + igic_final

                # Actualizar la orden
                orden.subtotal = subtotal_sin_igic_total  # Subtotal sin impuestos
                orden.descuento = descuento_general
                orden.impuestos = igic_final              # Total de IGIC
                orden.total = total_final                 # Total final
                orden.save()

                messages.success(
                    request, f'Orden {orden.numero_orden} creada exitosamente')
                return redirect('detalle_orden_venta', orden_id=orden.id)

        except ValueError as ve:
            messages.error(
                request, f'Error en los datos proporcionados: {type(ve)}, {str(ve)}')

        except Exception as e:
            messages.error(
                request, f'Error al crear la orden: {type(e)}, {str(e)}')

    # GET request
    clientes = Cliente.objects.all()
    productos = Producto.objects.all().prefetch_related('inventarios')

    categorias = CategoriaProducto.objects.all()

    metodos_pago_choices = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
    ]

    context = {
        'clientes': clientes,
        'categorias': categorias,
        'productos': productos,
        'metodos_pago_choices': metodos_pago_choices,
        'fecha_actual': date.today()
    }

    return render(request, 'pedidos/registro_orden_venta.html', context)


@login_required
def listado_ordenes_venta(request):
    """Listar todas las órdenes de venta"""
    ordenes = OrdenVenta.objects.select_related(
        'cliente', 'empleado_creador').order_by('-fecha_orden')

    # Filtros opcionales
    estado_filtro = request.GET.get('estado')
    cliente_filtro = request.GET.get('cliente')

    if estado_filtro:
        ordenes = ordenes.filter(estado=estado_filtro)

    if cliente_filtro:
        ordenes = ordenes.filter(cliente_id=cliente_filtro)

    context = {
        'ordenes': ordenes,
        'estados': OrdenVenta.ESTADOS,
        'clientes': Cliente.objects.all(),
        'estado_actual': estado_filtro,
        'cliente_actual': cliente_filtro
    }

    return render(request, 'pedidos/listado_ordenes_venta.html', context)


@login_required
def detalle_orden_venta(request, orden_id):
    """Ver/editar detalle de una orden de venta"""
    orden = get_object_or_404(
        OrdenVenta.objects.select_related('cliente'), id=orden_id)
    detalles = orden.detalles.select_related(
        'producto')
    productos = Producto.objects.all().prefetch_related('inventarios')

    categorias = CategoriaProducto.objects.all()

    if request.method == 'POST':
        try:
            # Determinar qué tipo de actualización se está realizando
            accion = request.POST.get('accion')
            if accion == 'actualizar_estado':
                # Actualizar solo el estado
                nuevo_estado = request.POST.get('estado')
                if nuevo_estado and nuevo_estado in dict(OrdenVenta.ESTADOS):
                    orden.estado = nuevo_estado
                    orden.save()
                    messages.success(
                        request, f'Estado actualizado a {orden.get_estado_display()}')
                else:
                    messages.error(request, 'Estado no válido')
            elif accion == 'actualizar_informacion_general':

                # Validar que la orden se pueda editar
                if orden.estado in ['entregado', 'cancelado']:
                    messages.error(
                        request, 'No se puede editar una orden entregada o cancelada')
                    return redirect('detalle_orden_venta', orden_id=orden.id)

                # Actualizar información general
                orden.notas = request.POST.get('notas', '').strip()
                orden.metodo_pago = request.POST.get(
                    'metodo_pago', orden.metodo_pago)

                # Actualizar fechas si se proporcionan
                fecha_entrega = request.POST.get('fecha_entrega')
                if fecha_entrega:
                    try:
                        fecha_entrega_obj = datetime.strptime(
                            fecha_entrega, '%Y-%m-%d').date()
                        if fecha_entrega_obj >= orden.fecha_orden:
                            orden.fecha_entrega = fecha_entrega_obj
                        else:
                            messages.warning(
                                request, 'La fecha de entrega no puede ser anterior a la fecha de orden')
                    except ValueError:
                        messages.warning(request, 'Formato de fecha no válido')

                # Actualizar descuento general
                try:
                    nuevo_descuento = float(
                        request.POST.get('descuento_general', 0))
                    if nuevo_descuento < 0:
                        messages.error(
                            request, 'El descuento no puede ser negativo')
                    elif nuevo_descuento > orden.subtotal:
                        messages.error(
                            request, 'El descuento no puede ser mayor que el subtotal')
                    else:
                        orden.descuento = nuevo_descuento

                        # Recalcular totales después del cambio de descuento
                        _recalcular_totales_orden_venta(orden)

                        messages.success(
                            request, 'Información de la orden actualizada exitosamente')

                except ValueError:
                    messages.error(
                        request, 'El descuento debe ser un número válido')

                # Guardar los cambios
                orden.save()
            else:
                # Si no hay acción específica, asumir actualización de estado (compatibilidad)
                nuevo_estado = request.POST.get('estado')
                if nuevo_estado and nuevo_estado in dict(OrdenVenta.ESTADOS):
                    orden.estado = nuevo_estado
                    orden.save()
                    messages.success(
                        request, f'Estado actualizado a {orden.get_estado_display()}')

        except Exception as e:
            messages.error(request, f'Error al actualizar la orden: {str(e)}')

        return redirect('detalle_orden_venta', orden_id=orden.id)

    # Litado metodos de pago
    metodos_pago_choices = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
    ]

    context = {
        'orden': orden,
        'detalles': detalles,
        'productos': productos,
        'categorias': categorias,
        'estados': OrdenVenta.ESTADOS,
        'metodos_pago_choices': metodos_pago_choices,
        'puede_editar': orden.estado not in ['entregado', 'cancelado']
    }

    return render(request, 'pedidos/detalle_orden_venta.html', context)


@login_required
def agregar_producto_orden_venta(request, orden_id):
    """Agregar producto a una orden existente"""
    orden = get_object_or_404(OrdenVenta, id=orden_id)

    if request.method == 'POST':
        try:
            producto_id = request.POST.get('producto')
            cantidad = int(request.POST.get('cantidad'))
            precio_unitario = float(request.POST.get('precio_unitario'))
            descuento_linea = float(request.POST.get('descuento_linea', 0))
            igic_porcentaje = float(request.POST.get('igic_porcentaje', 0))

            # Calcular subtotal antes de impuestos
            subtotal_sin_igic = (cantidad * precio_unitario) - descuento_linea

            # Calcular el IGIC
            igic_importe = subtotal_sin_igic * (igic_porcentaje / 100)

            # Calcular subtotal final (incluyendo IGIC)
            subtotal_linea = subtotal_sin_igic + igic_importe

            DetalleOrdenVenta.objects.create(
                orden=orden,
                producto_id=producto_id,
                empleado_creador=request.user,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento_linea=descuento_linea,
                igic_porcentaje=igic_porcentaje,
                igic_importe=igic_importe,
                subtotal=subtotal_linea
            )

            # Recalcular totales de la orden
            _recalcular_totales_orden_venta(orden)

            messages.success(
                request, 'Producto agregado exitosamente')

        except ValueError as e:
            messages.error(
                request, f'Error en los datos proporcionados: {str(e)}')

        except Exception as e:
            messages.error(
                request, f'Error al agregar producto: {str(e)}, {type(e)}')

    return redirect('detalle_orden_venta', orden_id=orden.id)


@login_required
def eliminar_producto_orden_venta(request, detalle_id):
    """Eliminar producto de una orden"""
    try:
        detalle = get_object_or_404(DetalleOrdenVenta, id=detalle_id)
        orden = detalle.orden

        detalle.delete()
        _recalcular_totales_orden_venta(orden)

        messages.success(request, 'Producto eliminado de la orden')
        return redirect('detalle_orden_venta', orden_id=orden.id)
    except Exception as e:
        print(f'Error al eliminar orden {type(e)}, {str(e)}')
        messages.error(request, 'error al eliminar orden')
        return redirect('detalle_orden_venta', orden_id=orden.id)


@login_required
def eliminar_orden_venta(request, detalle_id):
    """Eliminar orden completo"""
    if request.method == 'POST':
        orden = get_object_or_404(OrdenVenta, id=detalle_id)

        # Solo permitir eliminar ordens en estado 'cancelado'
        if orden.estado not in ['cancelado']:
            messages.error(
                request,
                'Solo se pueden eliminar ordens en estado "Cancelado"'
            )
            return redirect('detalle_orden_venta', detalle_id=orden.id)

        codigo_orden = orden.numero_orden
        orden.delete()
        messages.success(
            request, f'Orden {codigo_orden} eliminado exitosamente')
        return redirect('listado_ordenes_venta')

    messages.info(request, 'Acción no valida')
    return redirect('listado_ordenes_venta')


def _recalcular_totales_orden_venta(orden):
    """Función auxiliar para recalcular totales de una orden de venta"""
    try:
        detalles = orden.detalles.all()

        # Calcular subtotal sin IGIC e IGIC total
        subtotal_sin_igic = 0
        igic_total = 0

        for detalle in detalles:
            subtotal_linea_sin_igic = (
                detalle.cantidad * detalle.precio_unitario) - detalle.descuento_linea
            subtotal_sin_igic += subtotal_linea_sin_igic
            igic_total += detalle.igic_importe

        # Aplicar descuento general solo al subtotal
        subtotal_con_descuento = subtotal_sin_igic - orden.descuento

        # Actualizar totales
        orden.subtotal = subtotal_sin_igic
        orden.impuestos = igic_total
        orden.total = subtotal_con_descuento + igic_total
        orden.save()
    except Exception as e:
        print(
            f'El error de recalcular total orden venta es: {type(e)}, {str(e)}')

# ============================
# VISTAS ADICIONALES
# ============================


@login_required
def dashboard_pedidos(request):
    """Dashboard principal de pedidos"""
    # Estadísticas de pedidos a proveedores
    pedidos_proveedor = PedidoProveedor.objects.all()
    stats_pedidos = {
        'total': pedidos_proveedor.count(),
        'pendientes': pedidos_proveedor.filter(estado='pendiente').count(),
        'enviados': pedidos_proveedor.filter(estado='enviado').count(),
        'recibidos': pedidos_proveedor.filter(estado__in=['recibido_parcial', 'recibido_completo']).count(),
    }

    # Estadísticas de órdenes de venta
    ordenes_venta = OrdenVenta.objects.all()
    stats_ordenes = {
        'total': ordenes_venta.count(),
        'pendientes': ordenes_venta.filter(estado='pendiente').count(),
        'procesando': ordenes_venta.filter(estado='procesando').count(),
        'entregadas': ordenes_venta.filter(estado='entregado').count(),
    }

    # Pedidos recientes
    pedidos_recientes = PedidoProveedor.objects.select_related(
        'proveedor').order_by('-fecha_pedido')[:5]
    ordenes_recientes = OrdenVenta.objects.select_related(
        'cliente').order_by('-fecha_orden')[:5]

    context = {
        'stats_pedidos': stats_pedidos,
        'stats_ordenes': stats_ordenes,
        'pedidos_recientes': pedidos_recientes,
        'ordenes_recientes': ordenes_recientes,
    }

    return render(request, 'pedidos/dashboard.html', context)


@login_required
def get_productos_json(request):
    """API para obtener productos en formato JSON (para AJAX)"""
    productos = Producto.objects.all().values(
        'id', 'nombre', 'precio_venta', 'stock_actual')
    return JsonResponse(list(productos), safe=False)
