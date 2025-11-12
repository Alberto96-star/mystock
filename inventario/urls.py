from django.urls import path
from .views import list_inventory, create_product, create_category, detail_product


urlpatterns = [
    path('lista_inventario/', list_inventory, name='lista_inventario'),
    path('crear_producto/', create_product, name='crear_producto'),
    path('crear_categoria/', create_category, name='crear_categoria'),
    path(
        'detalle_producto/<int:producto_id>', detail_product, name='detalle_producto'),
]
