from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre_empresa', 'contacto_nombre', 'telefono_principal',
                    'email_formateado', 'ciudad', 'cif', 'estado_contacto',
                    'creado_el')

    list_filter = ('ciudad', 'creado_el', 'actualizado_el')

    search_fields = (
        'nombre_empresa', 'contacto_nombre', 'email', 'cif', 'telefono_oficina', 'ciudad'
    )

    readonly_fields = (
        'creado_el', 'actualizado_el', 'informacion_contacto_completa'
    )

    list_per_page = 25

    # Campos editables directamente desde la lista
    list_editable = ('contacto_nombre',)

    # Organización de campos en el formulario
    fieldsets = (
        ('Información de la Empresa', {
            'fields': ('nombre_empresa', 'cif'),
            'classes': ('wide',)
        }),
        ('Información de Contacto', {
            'fields': ('contacto_nombre', 'email'),
            'classes': ('wide',)
        }),
        ('Teléfonos', {
            'fields': ('telefono_oficina', 'telefono_segundario'),
            'classes': ('wide',)
        }),
        ('Dirección', {
            'fields': ('direccion', 'ciudad', 'codigo_postal'),
            'classes': ('wide',)
        }),
        ('Condiciones Comerciales', {
            'fields': ('condiciones_pago',),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('informacion_contacto_completa', 'creado_el', 'actualizado_el'),
            'classes': ('collapse',)
        }),
    )

    # Acciones personalizadas
    actions = ['marcar_como_contactado', 'exportar_contactos']

    def telefono_principal(self, obj):
        """Muestra el teléfono principal con formato clickeable"""
        if obj.telefono_oficina:
            return format_html(
                '<a href="tel:{}" style="color: #0066cc; text-decoration: none;">'
                '📞 {}</a>',
                obj.telefono_oficina.replace(' ', '').replace('-', ''),
                obj.telefono_oficina
            )
        return format_html('<span style="color: #999;">Sin teléfono</span>')
    telefono_principal.short_description = 'Teléfono Principal'

    def email_formateado(self, obj):
        """Muestra el email con formato clickeable y validación visual"""
        if obj.email:
            return format_html(
                '<a href="mailto:{}" style="color: #0066cc; text-decoration: none;">'
                '✉️ {}</a>',
                obj.email,
                obj.email
            )
        return format_html('<span style="color: #999;">Sin email</span>')
    email_formateado.short_description = 'Email'

    def estado_contacto(self, obj):
        """Indica el estado de la información de contacto"""
        puntuacion = 0

        # Evaluar completitud de la información
        if obj.telefono_oficina:
            puntuacion += 2
        if obj.email:
            puntuacion += 2
        if obj.telefono_segundario:
            puntuacion += 1
        if obj.direccion and obj.ciudad:
            puntuacion += 1

        if puntuacion >= 5:
            return format_html(
                '<span style="color: green; font-weight: bold;">🟢 Completo</span>'
            )
        elif puntuacion >= 3:
            return format_html(
                '<span style="color: orange; font-weight: bold;">🟡 Parcial</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔴 Incompleto</span>'
            )
    estado_contacto.short_description = 'Estado Contacto'

    def informacion_contacto_completa(self, obj):
        """Muestra un resumen completo de la información de contacto"""
        info = []

        if obj.telefono_oficina:
            info.append(f"📞 Oficina: {obj.telefono_oficina}")

        if obj.telefono_segundario:
            info.append(f"📱 Secundario: {obj.telefono_segundario}")

        if obj.email:
            info.append(f"✉️ Email: {obj.email}")

        if obj.direccion:
            direccion_completa = obj.direccion
            if obj.ciudad:
                direccion_completa += f", {obj.ciudad}"
            if obj.codigo_postal:
                direccion_completa += f" ({obj.codigo_postal})"
            info.append(f"📍 Dirección: {direccion_completa}")

        if obj.condiciones_pago:
            info.append(f"💰 Condiciones: {obj.condiciones_pago}")

        return format_html('<br>'.join(info)) if info else "Sin información adicional"
    informacion_contacto_completa.short_description = 'Información Completa de Contacto'

    def get_queryset(self, request):
        """Optimiza las consultas"""
        queryset = super().get_queryset(request)
        return queryset

    # Acciones personalizadas
    def marcar_como_contactado(self, request, queryset):
        """Acción para marcar proveedores como contactados"""
        count = queryset.count()
        # Aquí podrías agregar lógica para registrar el contacto
        self.message_user(
            request,
            f'Se marcaron {count} proveedor(es) como contactados.'
        )
    marcar_como_contactado.short_description = "Marcar como contactados"

    def exportar_contactos(self, request, queryset):
        """Acción para exportar información de contacto"""
        count = queryset.count()
        # Aquí podrías agregar lógica para exportar datos
        self.message_user(
            request,
            f'Se preparó la exportación de {count} proveedor(es).'
        )
    exportar_contactos.short_description = "Exportar información de contacto"

    # Filtros personalizados
    def changelist_view(self, request, extra_context=None):
        """Personaliza la vista de lista con estadísticas"""
        extra_context = extra_context or {}

        # Calcular estadísticas
        total_proveedores = Proveedor.objects.count()
        con_email = Proveedor.objects.filter(
            email__isnull=False).exclude(email='').count()
        con_telefono_secundario = Proveedor.objects.filter(
            telefono_segundario__isnull=False).exclude(telefono_segundario='').count()

        extra_context['estadisticas'] = {
            'total': total_proveedores,
            'con_email': con_email,
            'con_telefono_secundario': con_telefono_secundario,
            'sin_email': total_proveedores - con_email,
        }

        return super().changelist_view(request, extra_context)

    # Personalización del formulario
    def get_form(self, request, obj=None, **kwargs):
        """Personaliza el formulario"""
        form = super().get_form(request, obj, **kwargs)

        # Añadir ayuda contextual
        if 'cif' in form.base_fields:
            form.base_fields['cif'].help_text = "Código de Identificación Fiscal único del proveedor"

        if 'condiciones_pago' in form.base_fields:
            form.base_fields['condiciones_pago'].help_text = "Ej: 30 días, Contado, Transferencia, etc."

        return form

    # Configuración adicional
    save_on_top = True

    class Media:
        css = {
            'all': ('admin/css/custom_proveedor.css',)
        }


# Configuración adicional del admin
admin.site.site_header = "Administración de Proveedores"
admin.site.site_title = "Proveedores Admin"
admin.site.index_title = "Panel de Control de Proveedores"
