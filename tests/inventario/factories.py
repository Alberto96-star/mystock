import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal, FuzzyInteger

from inventario.models import CategoriaProducto, Producto, Inventario


class CategoriaProductoFactory(DjangoModelFactory):
    """
    Factory para crear categorías de producto de prueba.
    """
    class Meta:
        model = CategoriaProducto

    nombre_categoria = factory.Sequence(lambda n: f'Categoría {n}')
    descripcion = factory.Faker('sentence', locale='es_ES')


class ProductoFactory(DjangoModelFactory):
    """
    Factory para crear productos de prueba.
    """
    class Meta:
        model = Producto

    nombre = factory.Sequence(lambda n: f'Producto {n}')
    descripcion = factory.Faker('sentence', locale='es_ES')
    categoria = factory.SubFactory(CategoriaProductoFactory)
    precio_compra = FuzzyDecimal(10.0, 1000.0, precision=2)
    precio_venta = FuzzyDecimal(20.0, 2000.0, precision=2)
    stock_minimo = FuzzyInteger(0, 100)
    unidad_medida = FuzzyChoice(['Unidad', 'Kg', 'Litro', 'Metro'])
    codigo_producto = factory.Sequence(lambda n: f"TEST{n:04d}")


class InventarioFactory(DjangoModelFactory):
    """
    Factory para crear inventarios de prueba.
    """
    class Meta:
        model = Inventario

    producto = factory.SubFactory(ProductoFactory)
    cantidad_actual = FuzzyInteger(0, 1000)
    cantidad_reservada = FuzzyInteger(0, 100)
    ubicacion_almacen = factory.Faker('address', locale='es_ES')
