# control/models.py

import qrcode
from io import BytesIO

from django.conf import settings
from django.core.files import File
from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser  # IMPORTAR solo UNA vez aquí
from django.urls import reverse


# -----------------------------
# UsuarioPersonalizado (único)
# -----------------------------
class UsuarioPersonalizado(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('gestor', 'Gestor de categorías'),
        ('ventas', 'Equipo de Ventas'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='ventas')
    telefono = models.CharField(max_length=20, blank=True)
    departamento = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        permissions = [
            ("puede_ver_reportes", "Puede ver reportes avanzados"),
            ("puede_gestionar_usuarios", "Puede gestionar usuarios"),
            ("puede_eliminar_productos", "Puede eliminar productos"),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.rol})"


# -----------------------------
# Resto de los modelos
# -----------------------------

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, default='Sin categoria')
    descripcion = models.TextField(blank=True)
    total_stock = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#4e73df')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Atributo(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Atributo'
        verbose_name_plural = 'Atributos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class OpcionAtributo(models.Model):
    atributo = models.ForeignKey(Atributo, on_delete=models.CASCADE, related_name='opciones')
    valor = models.CharField(max_length=50)
    orden = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, default='#4e73df')

    class Meta:
        verbose_name = 'Opción de Atributo'
        verbose_name_plural = 'Opciones de Atributo'
        ordering = ['atributo', 'orden', 'valor']
        unique_together = [['atributo', 'valor']]

    def __str__(self):
        return f"{self.atributo}: {self.valor}"


class Producto(models.Model):
    ESTADO_STOCK = (
        ('NORMAL', 'Stock Normal'),
        ('BAJO', 'Stock Bajo'),
        ('AGOTADO', 'Stock Agotado'),
    )

    nombre = models.CharField(max_length=100)
    codigo_barras = models.CharField(max_length=100, unique=True, verbose_name='Código de Barras')
    atributos = models.ManyToManyField(Atributo, through='ProductoAtributo')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, default=1)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    estado = models.CharField(max_length=10, choices=ESTADO_STOCK, default='NORMAL')
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='productos_qr/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['codigo_barras']),
            models.Index(fields=['categoria']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo_barras})"

    def generate_qrcode(self):
        if not self.id:
            self.save()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"PROD:{self.id}:{self.codigo_barras}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        filename = f'qr_{self.codigo_barras}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        if self.stock_actual <= 0:
            self.estado = "AGOTADO"
        elif self.stock_actual < self.stock_minimo:
            self.estado = "BAJO"
        else:
            self.estado = "NORMAL"

        super().save(*args, **kwargs)

        if not self.qr_code:
            self.generate_qrcode()
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('detalle_producto', kwargs={'pk': self.pk})

    @property
    def valor_inventario(self):
        return self.stock_actual * self.precio_compra


class MovimientoStock(models.Model):
    TIPO_MOVIMIENTO = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
        ('TRASPASO', 'Traspaso'),
    )

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    ubicacion_origen = models.ForeignKey(
        Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_salida'
    )
    ubicacion_destino = models.ForeignKey(
        Ubicacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_entrada'
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    observaciones = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.cantidad} {self.producto} - {self.fecha}"

    def save(self, *args, **kwargs):
        modificar_stock = kwargs.pop('modificar_stock', True)

        if not self.pk and modificar_stock:
            if self.tipo == 'ENTRADA':
                self.producto.stock_actual += self.cantidad
            elif self.tipo == 'SALIDA':
                if self.producto.stock_actual >= self.cantidad:
                    self.producto.stock_actual -= self.cantidad
                else:
                    raise ValueError("Stock insuficiente para esta salida")
            self.producto.save()

        super().save(*args, **kwargs)


class ProductoAtributo(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    atributo = models.ForeignKey(Atributo, on_delete=models.CASCADE)
    opcion = models.ForeignKey(OpcionAtributo, on_delete=models.CASCADE, default=34)

    class Meta:
        ordering = ['atributo__nombre']

    def __str__(self):
        return f"{self.producto} - {self.atributo}: {self.opcion}"
