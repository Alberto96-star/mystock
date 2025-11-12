from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Cliente
    """
    list_display = [
        'nombre_comercial', 'email', 'telefono_oficina',
        'telefono_adicional', 'ciudad_fiscal', 'activo', 'empleado_asignado'
    ]
    list_filter = [
        'activo', 'ciudad_fiscal', 'empleado_asignado'
    ]
    search_fields = [
        'nombre_comercial', 'email',
        'telefono_oficina', 'telefono_adicional', 'cif'
    ]
    list_editable = ['activo']
    readonly_fields = ['creado_el', 'actualizado_el']

    fieldsets = (
        ('Información Cliente', {
            'fields': ('nombre_comercial', 'email', 'telefono_oficina', 'telefono_adicional', 'cif', 'empleado_asignado')
        }),
        ('Dirección Fiscal', {
            'fields': ('direccion_fiscal', 'ciudad_fiscal', 'codigo_postal_fiscal')
        }),
        ('Dirección Entrega', {
            'fields': ('direccion_entrega', 'ciudad_entrega', 'codigo_postal_entrega')
        }),
        ('Estado y Fechas', {
            'fields': ('activo', 'creado_el', 'actualizado_el')
        }),
    )
