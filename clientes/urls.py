from django.urls import path
from .views import client_register, list_client, detail_client

urlpatterns = [
    path('registro_cliente/', client_register, name='registro_cliente'),
    path('listado_clientes/', list_client, name='listado_clientes'),
    path(
        'detalle_cliente/<int:cliente_id>', detail_client, name='detalle_cliente'
    ),
]
