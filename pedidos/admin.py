from django.contrib import admin
from .models import PedidoProveedor, DetallePedidoProveedor, OrdenVenta, DetalleOrdenVenta


class DetallePedidoProveedorInline(admin.TabularInline):
    model = DetallePedidoProveedor
    extra = 1


@admin.register(PedidoProveedor)
class PedidoProveedorAdmin(admin.ModelAdmin):
    list_display = ("numero_pedido", "proveedor",
                    "fecha_pedido", "estado", "total")
    search_fields = ("numero_pedido", "proveedor__nombre_comercial")
    list_filter = ("estado", "fecha_pedido", "proveedor")
    date_hierarchy = "fecha_pedido"
    inlines = [DetallePedidoProveedorInline]
    readonly_fields = ("numero_pedido", "creado_el", "actualizado_el")


class DetalleOrdenVentaInline(admin.TabularInline):
    model = DetalleOrdenVenta
    extra = 1


@admin.register(OrdenVenta)
class OrdenVentaAdmin(admin.ModelAdmin):
    list_display = ("numero_orden", "cliente",
                    "fecha_orden", "estado", "total")
    search_fields = ("numero_orden", "cliente__nombre_comercial")
    list_filter = ("estado", "fecha_orden", "cliente")
    date_hierarchy = "fecha_orden"
    inlines = [DetalleOrdenVentaInline]
    readonly_fields = ("numero_orden", "creado_el", "actualizado_el")


@admin.register(DetallePedidoProveedor)
class DetallePedidoProveedorAdmin(admin.ModelAdmin):
    list_display = ("pedido", "producto", "cantidad_pedida",
                    "cantidad_recibida", "subtotal")
    search_fields = ("pedido__numero_pedido", "producto__nombre")
    list_filter = ("producto", "empleado_creador")


@admin.register(DetalleOrdenVenta)
class DetalleOrdenVentaAdmin(admin.ModelAdmin):
    list_display = ("orden", "producto", "cantidad",
                    "precio_unitario", "subtotal")
    search_fields = ("orden__numero_orden", "producto__nombre")
    list_filter = ("producto", "empleado_creador")
