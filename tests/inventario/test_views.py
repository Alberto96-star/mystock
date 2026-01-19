import pytest
from django.urls import reverse

from inventario.models import Producto, CategoriaProducto
from tests.inventario.factories import ProductoFactory, CategoriaProductoFactory, InventarioFactory


@pytest.mark.django_db
class TestListInventoryView:
    """
    Tests para la vista list_inventory.
    """

    def test_get_list_inventory_renders_correctly(self, authenticated_client):
        """
        Test que verifica que la lista de inventario se muestra correctamente.
        """
        url = reverse('lista_inventario')
        categoria = CategoriaProductoFactory()
        producto = ProductoFactory(categoria=categoria)

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'inventario/list_inventory.html' in [
            t.name for t in response.templates]
        assert producto in response.context['productos']
        assert categoria in response.context['categorias']

    def test_filter_by_category(self, authenticated_client):
        """
        Test que verifica el filtro por categoría.
        """
        url = reverse('lista_inventario')
        categoria1 = CategoriaProductoFactory()
        categoria2 = CategoriaProductoFactory()
        producto1 = ProductoFactory(categoria=categoria1)
        producto2 = ProductoFactory(categoria=categoria2)

        response = authenticated_client.get(
            url, {'buscarCategoria': categoria1.id})

        assert response.status_code == 200
        assert producto1 in response.context['productos']
        assert producto2 not in response.context['productos']

    def test_filter_by_product_name(self, authenticated_client):
        """
        Test que verifica el filtro por nombre de producto.
        """
        url = reverse('lista_inventario')
        categoria = CategoriaProductoFactory()
        producto1 = ProductoFactory(
            categoria=categoria, nombre='Producto Especial')
        producto2 = ProductoFactory(
            categoria=categoria, nombre='Otro Producto')

        response = authenticated_client.get(
            url, {'buscarProducto': 'Especial'})

        assert response.status_code == 200
        assert producto1 in response.context['productos']
        assert producto2 not in response.context['productos']


@pytest.mark.django_db
class TestCreateProductView:
    """
    Tests para la vista create_product.
    """

    def test_get_create_product_form_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el formulario de creación se muestra correctamente.
        """
        url = reverse('crear_producto')
        categoria = CategoriaProductoFactory()

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'inventario/create_product.html' in [
            t.name for t in response.templates]
        assert categoria in response.context['categorias']

    def test_create_product_successfully(self, authenticated_client):
        """
        Test del caso feliz: crear un producto con todos los campos.
        """
        url = reverse('crear_producto')
        categoria = CategoriaProductoFactory(nombre_categoria='Electrónica')

        product_data = {
            'nombreProducto': 'Producto Test',
            'categoria': categoria.id,
            'stockMinimo': 10,
            'precioCompra': 100.50,
            'precioVenta': 150.75,
            'unidadMedida': 'Unidad',
            'descripcion': 'Descripción del producto'
        }

        response = authenticated_client.post(url, data=product_data)

        assert response.status_code == 302
        assert response.url == reverse('lista_inventario')

        assert Producto.objects.count() == 1
        producto = Producto.objects.first()
        assert producto.nombre == 'Producto Test'
        assert producto.categoria == categoria
        assert producto.stock_minimo == 10
        assert producto.precio_compra == 100.50
        assert producto.precio_venta == 150.75
        assert producto.unidad_medida == 'Unidad'
        assert producto.descripcion == 'Descripción del producto'
        assert producto.codigo_producto.startswith('EL')

    def test_create_product_missing_required_fields(self, authenticated_client):
        """
        Test que verifica validación de campos obligatorios.
        """
        url = reverse('crear_producto')
        categoria = CategoriaProductoFactory()

        product_data = {
            'nombreProducto': '',
            'categoria': categoria.id,
            'precioCompra': 100.50,
            'precioVenta': 150.75,
        }

        response = authenticated_client.post(url, data=product_data)

        assert response.status_code == 200
        assert Producto.objects.count() == 0

    def test_create_product_invalid_category(self, authenticated_client):
        """
        Test que verifica manejo de categoría inválida.
        """
        url = reverse('crear_producto')
        product_data = {
            'nombreProducto': 'Producto Test',
            'categoria': 9999,
            'precioCompra': 100.50,
            'precioVenta': 150.75,
        }

        response = authenticated_client.post(url, data=product_data)

        assert response.status_code == 200
        assert Producto.objects.count() == 0


@pytest.mark.django_db
class TestDetailProductView:
    """
    Tests para la vista detail_product.
    """

    def test_get_detail_product_renders_correctly(self, authenticated_client):
        """
        Test que verifica que el detalle del producto se muestra correctamente.
        """
        categoria = CategoriaProductoFactory()
        producto = ProductoFactory(categoria=categoria)
        inventario = InventarioFactory(
            producto=producto, cantidad_actual=50, cantidad_reservada=10)

        url = reverse('detalle_producto', kwargs={'producto_id': producto.id})

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'inventario/detail_product.html' in [
            t.name for t in response.templates]
        assert response.context['producto'] == producto
        assert response.context['inventario'] == inventario
        assert response.context['cantidad_disponible'] == 40

    def test_update_product_successfully(self, authenticated_client):
        """
        Test que verifica la actualización exitosa de un producto.
        """
        categoria1 = CategoriaProductoFactory()
        categoria2 = CategoriaProductoFactory()
        producto = ProductoFactory(categoria=categoria1)
        inventario = InventarioFactory(producto=producto)

        url = reverse('detalle_producto', kwargs={'producto_id': producto.id})

        update_data = {
            'nombre': 'Producto Actualizado',
            'descripcion': 'Nueva descripción',
            'codigo_producto': producto.codigo_producto,
            'categoria': categoria2.id,
            'precio_compra': 200.00,
            'precio_venta': 300.00,
            'stock_minimo': 20,
            'unidad_medida': 'Kg',
            'cantidad_actual': 100,
            'cantidad_reservada': 20,
            'ubicacion_almacen': 'Nueva ubicación'
        }

        response = authenticated_client.post(url, data=update_data)

        assert response.status_code == 302
        assert response.url == url

        producto.refresh_from_db()
        inventario.refresh_from_db()
        assert producto.nombre == 'Producto Actualizado'
        assert producto.categoria == categoria2
        assert producto.precio_compra == 200.00
        assert inventario.cantidad_actual == 100
        assert inventario.cantidad_reservada == 20

    def test_update_product_invalid_data(self, authenticated_client):
        """
        Test que verifica validación de datos inválidos en actualización.
        """
        categoria = CategoriaProductoFactory()
        producto = ProductoFactory(categoria=categoria)
        inventario = InventarioFactory(producto=producto)

        url = reverse('detalle_producto', kwargs={'producto_id': producto.id})

        update_data = {
            'nombre': '',
            'codigo_producto': producto.codigo_producto,
            'categoria': categoria.id,
            'precio_compra': -10,
            'precio_venta': 100,
            'stock_minimo': 10,
            'unidad_medida': 'Unidad',
            'cantidad_actual': 50,
            'cantidad_reservada': 60,
            'ubicacion_almacen': 'Ubicación'
        }

        response = authenticated_client.post(url, data=update_data)

        assert response.status_code == 302
        assert response.url == url

        producto.refresh_from_db()
        assert producto.nombre != ''


@pytest.mark.django_db
class TestCreateCategoryView:
    """
    Tests para la vista create_category.
    """

    def test_create_category_successfully(self, authenticated_client):
        """
        Test del caso feliz: crear una categoría.
        """
        url = reverse('crear_categoria')
        category_data = {
            'nombreCategoria': 'Nueva Categoría',
            'descripcionCategoria': 'Descripción de la categoría'
        }

        response = authenticated_client.post(url, data=category_data)

        assert response.status_code == 302
        assert response.url == reverse('crear_producto')

        assert CategoriaProducto.objects.count() == 1
        categoria = CategoriaProducto.objects.first()
        assert categoria.nombre_categoria == 'Nueva Categoría'
        assert categoria.descripcion == 'Descripción de la categoría'

    def test_create_category_missing_name(self, authenticated_client):
        """
        Test que verifica validación de nombre obligatorio.
        """
        url = reverse('crear_categoria')
        category_data = {
            'nombreCategoria': '',
            'descripcionCategoria': 'Descripción'
        }

        response = authenticated_client.post(url, data=category_data)

        assert response.status_code == 200
        assert CategoriaProducto.objects.count() == 0

    def test_create_category_duplicate_name(self, authenticated_client):
        """
        Test que verifica que no se permiten nombres duplicados.
        """
        CategoriaProductoFactory(nombre_categoria='Categoría Existente')

        url = reverse('crear_categoria')
        category_data = {
            'nombreCategoria': 'Categoría Existente',
            'descripcionCategoria': 'Descripción'
        }

        response = authenticated_client.post(url, data=category_data)

        assert response.status_code == 200
        assert CategoriaProducto.objects.count() == 1
