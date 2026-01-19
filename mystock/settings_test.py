from .settings import *

# Sobreescribir la configuración de base de datos para tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_mystock',  # Nombre diferente para test DB
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        # IMPORTANTE para tests
        'TEST': {
            'NAME': 'test_mystock_db',  # Nombre explícito de la DB de test
        }
    }
}

# Desactivar logging verboso en tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# Hacer el password hashing más rápido en tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
