import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory para crear usuarios/empleados de prueba."""
    class Meta:
        model = User
        skip_postgeneration_save = True

    # EMP0001, EMP0002, etc.
    username = factory.Sequence(lambda n: f'EMP{n:04d}')
    email = factory.Sequence(lambda n: f'empleado{n}@empresa.com')
    first_name = factory.Faker('first_name', locale='es_ES')
    last_name = factory.Faker('last_name', locale='es_ES')

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """
        Post-generation hook para setear el password correctamente.
        """
        if not create:
            # Si usamos build() en lugar de create(), no hacer nada
            return

        # Setear el password
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')

        # IMPORTANTE: Guardar explícitamente después de setear el password
        # Esto asegura que el password hasheado se guarde en la DB
        obj.save()
