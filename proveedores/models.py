from django.db import models
from django.core.validators import RegexValidator, EmailValidator


class Proveedor(models.Model):
    """
    Modelo para gestionar información de proveedores.
    """
    phone_regex = RegexValidator(
        regex=r'^\+?[\d\s\-]{9,20}$',
        message="Ingrese un teléfono válido. Puede usar +, espacios o guiones."
    )

    id = models.AutoField(primary_key=True)

    nombre_empresa = models.CharField(
        max_length=250,
        verbose_name='Nombre de la Empresa'
    )

    contacto_nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre del Contacto'
    )

    email = models.EmailField(
        verbose_name='Correo Electrónico',
        blank=True,
        null=True,
        validators=[EmailValidator(message="Ingrese un correo válido.")]
    )

    telefono_oficina = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name='Teléfono Oficina'
    )

    telefono_segundario = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name='Teléfono Secundario',
        blank=True,
        null=True
    )

    direccion = models.TextField(
        max_length=255,
        verbose_name='Dirección',
        blank=True,
        null=True
    )

    ciudad = models.CharField(
        max_length=100,
        verbose_name='Ciudad',
        blank=True,
        null=True
    )

    codigo_postal = models.IntegerField(
        verbose_name='Código Postal',
        blank=True,
        null=True
    )

    cif = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='CIF'
    )

    condiciones_pago = models.TextField(
        verbose_name='Condiciones de Pago',
        blank=True,
        null=True
    )

    creado_el = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado el'
    )

    actualizado_el = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado el'
    )

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['-creado_el']
        indexes = [
            models.Index(fields=['nombre_empresa']),
            models.Index(fields=['cif']),
        ]

    def __str__(self):
        return f"{self.nombre_empresa}" or "Cliente sin nombre"

    def save(self, *args, **kwargs):
        """Normalizar campos antes de guardar para evitar duplicados"""
        if self.nombre_empresa:
            self.nombre_empresa = ' '.join(self.nombre_empresa.split()).title()
        if self.ciudad:
            self.ciudad = self.ciudad.strip().title()
        if self.email:
            self.email = self.email.lower().strip()
        if self.cif:
            self.cif = self.cif.strip().upper()

        super().save(*args, **kwargs)
