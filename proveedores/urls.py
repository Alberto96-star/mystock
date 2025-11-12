from django.urls import path
from .views import supplier_register, list_supplier, details_supplier

urlpatterns = [
    path('registro_proveedores/', supplier_register, name='registro_proveedores'),
    path('listado_proveedor/', list_supplier, name='listado_proveedor'),
    path(
        'detalle_proveedor/<int:supplier_id>/', details_supplier, name='editar_proveedor'),
]
