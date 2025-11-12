from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


class Cliente(models.Model):
    """
    Modelo para gestionar información de clientes
    """
    # Validador para teléfono
    phone_regex = RegexValidator(
        regex=r'^\+?[\d\s\-]{9,20}$',
        message="Ingrese un teléfono válido. Puede usar +, espacios o guiones."
    )

    id = models.AutoField(primary_key=True)

    nombre_comercial = models.CharField(
        max_length=250,
        verbose_name='Nombre Comercial'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Correo Electrónico',
        blank=True,
        null=True
    )
    telefono_oficina = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name='Teléfono Oficina'
    )
    telefono_adicional = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name='Teléfono Adicional',
        blank=True,
        null=True
    )
    direccion_fiscal = models.TextField(
        max_length=255,
        verbose_name='Dirección Fiscal'
    )
    direccion_entrega = models.TextField(
        max_length=255,
        verbose_name='Dirección Entrega',
        blank=True,
        null=True
    )
    ciudad_entrega = models.CharField(
        max_length=100,
        verbose_name='Ciudad',
        blank=True,
        null=True
    )
    codigo_postal_entrega = models.IntegerField(
        verbose_name='Código Postal Entrega',
        blank=True,
        null=True
    )
    ciudad_fiscal = models.CharField(
        max_length=100,
        verbose_name='Ciudad Fiscal'
    )
    codigo_postal_fiscal = models.IntegerField(
        verbose_name='Código Postal Fiscal'
    )
    cif = models.CharField(
        max_length=20,
        blank=False,
        null=False,
        unique=True,
        verbose_name='CIF'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )
    actualizado_el = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado el'
    )
    empleado_asignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_asignados',
        verbose_name='Vendedor Asignado'
    )

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-creado_el']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['cif']),
            models.Index(fields=['activo']),
            models.Index(fields=['empleado_asignado']),
        ]

    def __str__(self):
        return f"{self.nombre_comercial}" or "Cliente sin nombre"

    def save(self, *args, **kwargs):
        """Normalizar campos antes de guardar para evitar duplicados"""
        if self.nombre_comercial:
            self.nombre_comercial = ' '.join(
                self.nombre_comercial.split()).title()
        if self.email:
            self.email = self.email.lower().strip()
        if self.ciudad_entrega:
            self.ciudad_entrega = self.ciudad_entrega.strip().title()
        if self.ciudad_fiscal:
            self.ciudad_fiscal = self.ciudad_fiscal.strip().title()
        if self.cif:
            self.cif = self.cif.upper().strip()

        super().save(*args, **kwargs)
