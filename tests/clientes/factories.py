import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger

from clientes.models import Cliente
from tests.factories import UserFactory


class ClienteFactory(DjangoModelFactory):
    """
    Factory para crear clientes de prueba.

    Nota cómo generamos data que se parece a data real española
    para hacer los tests más realistas.
    """
    class Meta:
        model = Cliente

    # Generamos nombres comerciales realistas
    nombre_comercial = factory.Faker('company', locale='es_ES')

    # Generamos CIFs españoles realistas (simplificado)
    # En producción podrías usar un generador más sofisticado
    cif = factory.Sequence(lambda n: f'B{n:08d}')

    # Teléfonos españoles realistas
    telefono_oficina = factory.Sequence(lambda n: f'91{n:07d}')
    telefono_adicional = factory.LazyFunction(
        lambda: factory.Faker('phone_number', locale='es_ES').evaluate(
            None, None, {'locale': 'es_ES'})
    )

    email = factory.Faker('company_email', locale='es_ES')

    # Direcciones españolas
    direccion_fiscal = factory.Faker('street_address', locale='es_ES')
    ciudad_fiscal = factory.Faker('city', locale='es_ES')
    codigo_postal_fiscal = factory.Faker('postcode', locale='es_ES')

    # Dirección de entrega puede ser None o igual a la fiscal
    direccion_entrega = factory.LazyAttribute(
        lambda obj: obj.direccion_fiscal if factory.random.random.randint(
            0, 1) else None
    )
    ciudad_entrega = factory.LazyAttribute(
        lambda obj: obj.ciudad_fiscal if obj.direccion_entrega else None
    )
    codigo_postal_entrega = factory.LazyAttribute(
        lambda obj: obj.codigo_postal_fiscal if obj.direccion_entrega else None
    )

    activo = True

    # Algunos clientes tendrán empleado asignado, otros no
    empleado_asignado = factory.Maybe(
        'with_empleado',
        yes_declaration=factory.SubFactory(UserFactory),
        no_declaration=None
    )

    class Params:
        # Parámetro para controlar si tiene empleado o no
        with_empleado = True


class ClienteInactivoFactory(ClienteFactory):
    """Factory para crear clientes inactivos específicamente."""
    activo = False


class ClienteSinEmpleadoFactory(ClienteFactory):
    """Factory para crear clientes sin empleado asignado."""
    empleado_asignado = None
