from django.contrib import admin
from django.utils.html import format_html
from .models import CategoriaProducto, Producto, Inventario


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre_categoria', 'total_productos',
                    'creado_el', 'actualizado_el')
    list_filter = ('creado_el', 'actualizado_el')
    search_fields = ('nombre_categoria', 'descripcion')
    readonly_fields = ('creado_el', 'actualizado_el')

    fieldsets = (
        ('Información General', {
            'fields': ('nombre_categoria', 'descripcion')
        }),
        ('Información de Sistema', {
            'fields': ('creado_el', 'actualizado_el'),
            'classes': ('collapse',)
        }),
    )

    def total_productos(self, obj):
        """Muestra el total de productos en esta categoría"""
        return obj.productos.count()
    total_productos.short_description = 'Total Productos'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_producto', 'nombre', 'categoria', 'precio_compra',
                    'precio_venta', 'margen_ganancia', 'stock_actual', 'estado_stock',
                    'creado_el', 'stock_minimo')
    list_filter = ('categoria', 'creado_el', 'actualizado_el', 'unidad_medida')
    search_fields = ('codigo_producto', 'nombre', 'descripcion')
    list_editable = ('precio_compra', 'precio_venta', 'stock_minimo')
    readonly_fields = (
        'creado_el', 'actualizado_el', 'margen_ganancia_detalle'
    )
    list_per_page = 20

    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_producto', 'nombre', 'descripcion', 'categoria')
        }),
        ('Precios y Stock', {
            'fields': (
                'precio_compra', 'precio_venta', 'margen_ganancia_detalle',
                'stock_minimo', 'unidad_medida'
            )
        }),
        ('Información de Sistema', {
            'fields': ('creado_el', 'actualizado_el'),
            'classes': ('collapse',)
        }),
    )

    def margen_ganancia(self, obj):
        """Calcula y muestra el margen de ganancia"""
        if obj.precio_compra and obj.precio_venta and obj.precio_compra > 0:
            margen = ((obj.precio_venta - obj.precio_compra) /
                      obj.precio_compra) * 100
            color = 'green' if margen > 20 else 'orange' if margen > 10 else 'red'
            return format_html('<span style="color: %s;">%.1f%%</span>' % (color, margen))
        return format_html('<span style="color: gray;">-</span>')
    margen_ganancia.short_description = 'Margen (%)'

    def margen_ganancia_detalle(self, obj):
        """Versión detallada del margen para el formulario"""
        if obj.precio_compra and obj.precio_venta and obj.precio_compra > 0:
            margen = ((obj.precio_venta - obj.precio_compra) /
                      obj.precio_compra) * 100
            ganancia = obj.precio_venta - obj.precio_compra

            # Determinar color basado en el margen
            if margen > 20:
                color = 'green'
                emoji = '📈'
            elif margen > 10:
                color = 'orange'
                emoji = '📊'
            else:
                color = 'red'
                emoji = '📉'

            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {:.2f}%</span><br>'
                '<small style="color: #666;">${:.2f} ganancia por unidad</small>',
                color, emoji, margen, ganancia
            )
        elif not obj.precio_compra:
            return format_html(
                '<span style="color: red;">❌ Falta precio de compra</span>'
            )
        elif not obj.precio_venta:
            return format_html(
                '<span style="color: red;">❌ Falta precio de venta</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">❌ Precio de compra debe ser mayor a 0</span>'
            )
    margen_ganancia_detalle.short_description = 'Margen de Ganancia'

    def stock_actual(self, obj):
        """Muestra el stock actual desde el inventario"""
        try:
            inventario = obj.inventarios.first()
            if inventario:
                return inventario.cantidad_actual
            return 0
        except:
            return 0
    stock_actual.short_description = 'Stock Actual'

    def estado_stock(self, obj):
        """Indica el estado del stock basado en el mínimo"""
        try:
            inventario = obj.inventarios.first()
            if inventario:
                stock_minimo = obj.stock_minimo or 0
                if inventario.cantidad_actual <= stock_minimo:
                    return format_html(
                        '<span style="color: red; font-weight: bold;">⚠️ Bajo</span>'
                    )
                elif inventario.cantidad_actual <= stock_minimo * 1.5:
                    return format_html(
                        '<span style="color: orange;">⚡ Medio</span>'
                    )
                else:
                    return format_html(
                        '<span style="color: green;">✅ Bueno</span>'
                    )
            return format_html('<span style="color: gray;">Sin inventario</span>')
        except Exception:
            return format_html('<span style="color: gray;">Error</span>')
    estado_stock.short_description = 'Estado Stock'


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'cantidad_actual', 'cantidad_reservada',
                    'cantidad_disponible', 'estado_stock', 'ubicacion_almacen',
                    'fecha_ultimo_movimiento')
    list_filter = (
        'fecha_ultimo_movimiento', 'creado_el', 'producto__categoria'
    )
    search_fields = (
        'producto__nombre', 'producto__codigo_producto', 'ubicacion_almacen'
    )
    readonly_fields = (
        'fecha_ultimo_movimiento', 'creado_el', 'actualizado_el', 'cantidad_disponible_detalle'
    )
    list_editable = (
        'cantidad_actual', 'cantidad_reservada', 'ubicacion_almacen'
    )

    fieldsets = (
        ('Producto', {
            'fields': ('producto',)
        }),
        ('Cantidades', {
            'fields': ('cantidad_actual', 'cantidad_reservada', 'cantidad_disponible_detalle')
        }),
        ('Almacén', {
            'fields': ('ubicacion_almacen',)
        }),
        ('Información de Sistema', {
            'fields': ('fecha_ultimo_movimiento', 'creado_el', 'actualizado_el'),
            'classes': ('collapse',)
        }),
    )

    def cantidad_disponible(self, obj):
        """Calcula la cantidad disponible (actual - reservada)"""
        disponible = obj.cantidad_actual - obj.cantidad_reservada
        color = 'green' if disponible > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, disponible
        )
    cantidad_disponible.short_description = 'Disponible'

    def cantidad_disponible_detalle(self, obj):
        """Versión detallada para el formulario"""
        disponible = obj.cantidad_actual - obj.cantidad_reservada
        return "{} unidades ({} actual - {} reservada)".format(disponible, obj.cantidad_actual, obj.cantidad_reservada)
    cantidad_disponible_detalle.short_description = 'Cantidad Disponible'

    def estado_stock(self, obj):
        """Estado del stock basado en el stock mínimo del producto"""
        stock_minimo = obj.producto.stock_minimo
        if obj.cantidad_actual <= stock_minimo:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔴 Crítico</span>'
            )
        elif obj.cantidad_actual <= stock_minimo * 1.5:
            return format_html(
                '<span style="color: orange; font-weight: bold;">🟡 Bajo</span>'
            )
        else:
            return format_html(
                '<span style="color: green; font-weight: bold;">🟢 Normal</span>'
            )
    estado_stock.short_description = 'Estado'

    # Filtros personalizados en la barra lateral
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('producto', 'producto__categoria')


# Configuración adicional del admin
admin.site.site_header = "Administración de Inventario"
admin.site.site_title = "Inventario Admin"
admin.site.index_title = "Panel de Control de Inventario"
