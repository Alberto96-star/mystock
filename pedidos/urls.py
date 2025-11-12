from django.urls import path
from .views import (
    # Dashboard
    dashboard_pedidos,

    # Pedidos a Proveedores
    registro_pedido_proveedor,
    listado_pedidos_proveedor,
    detalle_pedido_proveedor,
    agregar_producto_pedido_proveedor,
    eliminar_producto_pedido_proveedor,
    eliminar_pedido_proveedor,

    # Órdenes de Venta
    registro_orden_venta,
    listado_ordenes_venta,
    detalle_orden_venta,
    agregar_producto_orden_venta,
    eliminar_producto_orden_venta,
    eliminar_orden_venta,

    # API/AJAX
    get_productos_json,
)

urlpatterns = [
    # Dashboard principal
    path('', dashboard_pedidos, name='dashboard_pedidos'),

    # URLs para Pedidos a Proveedores
    path(
        'pedidos-proveedor/registro/', registro_pedido_proveedor, name='registro_pedido_proveedor'),
    path(
        'pedidos-proveedor/listado/', listado_pedidos_proveedor, name='listado_pedidos_proveedor'),
    path(
        'pedidos-proveedor/detalle/<int:pedido_id>/', detalle_pedido_proveedor, name='detalle_pedido_proveedor'),
    path(
        'pedidos-proveedor/<int:pedido_id>/agregar-producto/', agregar_producto_pedido_proveedor, name='agregar_producto_pedido_proveedor'),
    path(
        'pedidos-proveedor/eliminar-producto/<int:detalle_id>/', eliminar_producto_pedido_proveedor, name='eliminar_producto_pedido_proveedor'),
    path(
        'pedidos-proveedor/eliminar/<int:pedido_id>/', eliminar_pedido_proveedor, name='eliminar_pedido_proveedor'),

    # URLs para Órdenes de Venta
    path(
        'ordenes-venta/registro/', registro_orden_venta, name='registro_orden_venta'),
    path(
        'ordenes-venta/listado/', listado_ordenes_venta, name='listado_ordenes_venta'),
    path(
        'ordenes-venta/detalle/<int:orden_id>/', detalle_orden_venta, name='detalle_orden_venta'),
    path(
        'ordenes-venta/<int:orden_id>/agregar-producto/', agregar_producto_orden_venta, name='agregar_producto_orden_venta'),
    path(
        'ordenes-venta/eliminar-producto/<int:detalle_id>/', eliminar_producto_orden_venta, name='eliminar_producto_orden_venta'),
    path(
        'ordenes-venta/eliminar/<int:detalle_id>/', eliminar_orden_venta, name='eliminar_orden_venta'),

    # API endpoints
    path('api/productos/', get_productos_json, name='api_productos'),
]
