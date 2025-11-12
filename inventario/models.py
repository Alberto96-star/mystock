from django.db import models


class CategoriaProducto(models.Model):

    nombre_categoria = models.CharField(
        max_length=100, verbose_name="Nombre Categoria", unique=True)
    descripcion = models.TextField(
        blank=True, null=True, verbose_name="Descripción")
    creado_el = models.DateTimeField(
        auto_now_add=True, verbose_name="Creado el")
    actualizado_el = models.DateTimeField(
        auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = 'Categoría de Producto'
        verbose_name_plural = 'Categorías de Productos'

    def __str__(self):
        return f"{self.nombre_categoria}"

    def save(self, *args, **kwargs):
        """Normalizar campos antes de guardar para evitar duplicados"""
        if self.nombre_categoria:
            self.nombre_categoria = ' '.join(
                self.nombre_categoria.split()).title()
        super().save(*args, **kwargs)


class Producto(models.Model):
    codigo_producto = models.CharField(
        max_length=50, unique=True, verbose_name="Código del Producto")
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(
        blank=True, null=True, verbose_name="Descripción")
    categoria = models.ForeignKey(
        CategoriaProducto, on_delete=models.PROTECT, related_name='productos', verbose_name="Categoría")
    precio_compra = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Precio de Compra")
    precio_venta = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Precio de Venta")
    stock_minimo = models.PositiveIntegerField(
        verbose_name="Stock Mínimo", default=0)
    unidad_medida = models.CharField(
        max_length=50, verbose_name="Unidad de Medida")
    creado_el = models.DateTimeField(
        auto_now_add=True, verbose_name="Creado el")
    actualizado_el = models.DateTimeField(
        auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f"{self.nombre} ({self.codigo_producto})"

    def save(self, *args, **kwargs):
        """Normalizar campos antes de guardar para evitar duplicados"""
        if self.nombre:
            self.nombre = ' '.join(self.nombre.split()).title()
        super().save(*args, **kwargs)


class Inventario(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='inventarios', verbose_name="Producto")
    cantidad_actual = models.IntegerField(
        default=0, verbose_name="Cantidad Actual")
    cantidad_reservada = models.IntegerField(
        default=0, verbose_name="Cantidad Reservada")
    ubicacion_almacen = models.CharField(
        max_length=255, blank=True, null=True, default="No especificada", verbose_name="Ubicación en Almacén")
    fecha_ultimo_movimiento = models.DateTimeField(
        auto_now=True, verbose_name="Fecha del Último Movimiento")
    creado_el = models.DateTimeField(
        auto_now_add=True, verbose_name="Creado el")
    actualizado_el = models.DateTimeField(
        auto_now=True, verbose_name="Actualizado el")

    class Meta:
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventarios'

    def __str__(self):
        return f"Inventario de {self.producto.nombre}"
