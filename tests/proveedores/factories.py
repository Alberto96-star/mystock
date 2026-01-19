import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger

from proveedores.models import Proveedor


class ProveedorFactory(DjangoModelFactory):
    """
    Factory para crear proveedores de prueba.
    """
    class Meta:
        model = Proveedor

    nombre_empresa = factory.Sequence(lambda n: f'Empresa Proveedora {n}')
    contacto_nombre = factory.Faker('name', locale='es_ES')
    email = factory.Faker('company_email', locale='es_ES')
    telefono_oficina = factory.Sequence(lambda n: f'91{n:07d}')
    telefono_segundario = factory.Sequence(lambda n: f'65{n:07d}')
    direccion = factory.Faker('street_address', locale='es_ES')
    ciudad = factory.Faker('city', locale='es_ES')
    codigo_postal = FuzzyInteger(10000, 99999)
    cif = factory.Sequence(lambda n: f'B{n:08d}')
    condiciones_pago = factory.Faker('sentence', locale='es_ES')
