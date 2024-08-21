from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

# Modelo para los Proveedores
class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    contacto = models.CharField(max_length=200)
    direccion = models.TextField()

    def __str__(self):
        return self.nombre

# Modelo para los Productos
class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_medida = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

# Modelo para las Sucursales
class Sucursal(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    es_matriz = models.BooleanField(default=False)  # Indica si la sucursal es la matriz

    def save(self, *args, **kwargs):
        if self.es_matriz:
            Sucursal.objects.update(es_matriz=False)  # Desmarca cualquier otra sucursal como matriz
        super(Sucursal, self).save(*args, **kwargs)

    def __str__(self):
        return self.nombre

# Modelo para Empleados
class Empleado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre

# Modelo para las Compras
from django.db import transaction

class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    total_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Guarda la instancia de Compra para asegurarte de que tiene un ID
        super(Compra, self).save(*args, **kwargs)

        # Luego de guardar la compra, puedes trabajar con los detalles
        self.total_compra = sum(detalle.subtotal for detalle in self.detalles.all())
        super(Compra, self).save(update_fields=['total_compra'])

    def __str__(self):
        return f"Compra {self.id} - {self.proveedor.nombre}"

# Modelo para los Detalles de las Compras
class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calcula el subtotal si no está especificado
        self.subtotal = self.cantidad * self.precio
        super(DetalleCompra, self).save(*args, **kwargs)

        try:
            # Supongamos que solo hay una sucursal marcada como matriz
            matriz = Sucursal.objects.get(es_matriz=True)
            # Actualiza el inventario en la matriz
            inventario, created = Inventario.objects.get_or_create(producto=self.producto, sucursal=matriz, defaults={'cantidad': 0})
            inventario.incrementar(self.cantidad)
        except ObjectDoesNotExist:
            raise ValueError("No se ha definido una matriz para registrar la compra.")

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} unidades"

# Modelo para los Inventarios
class Inventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    cantidad = models.IntegerField()

    class Meta:
        unique_together = ('producto', 'sucursal')

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} unidades en {self.sucursal.nombre}"

    def incrementar(self, cantidad):
        """Incrementa la cantidad en inventario."""
        self.cantidad += cantidad
        self.save()

    def decrementar(self, cantidad):
        """Decrementa la cantidad en inventario, asegurando que no sea negativa."""
        if self.cantidad >= cantidad:
            self.cantidad -= cantidad
            self.save()
        else:
            raise ValueError("No hay suficiente inventario para decrementar.")

# Modelo para las Transferencias
class Transferencia(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    sucursal_origen = models.ForeignKey(Sucursal, related_name='transferencias_salida', on_delete=models.CASCADE)
    sucursal_destino = models.ForeignKey(Sucursal, related_name='transferencias_entrada', on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    fecha_transferencia = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super(Transferencia, self).save(*args, **kwargs)

        # Actualiza el inventario de la sucursal de origen
        inventario_origen, created = Inventario.objects.get_or_create(producto=self.producto, sucursal=self.sucursal_origen, defaults={'cantidad': 0})
        if inventario_origen.cantidad >= self.cantidad:
            inventario_origen.decrementar(self.cantidad)
        else:
            raise ValueError("No hay suficiente inventario en la sucursal de origen para la transferencia.")

        # Actualiza el inventario de la sucursal de destino
        inventario_destino, created = Inventario.objects.get_or_create(producto=self.producto, sucursal=self.sucursal_destino, defaults={'cantidad': 0})
        inventario_destino.cantidad += self.cantidad
        inventario_destino.save()

    def __str__(self):
        return f"Transferencia de {self.sucursal_origen.nombre} a {self.sucursal_destino.nombre}"

# Modelo para las Ventas
class Venta(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)  # Relación con Empleado
    fecha_venta = models.DateTimeField(auto_now_add=True)
    total_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total_venta = sum(detalle.subtotal for detalle in self.detalles.all())
        super(Venta, self).save(*args, **kwargs)

    def __str__(self):
        return f"Venta {self.id} - {self.sucursal.nombre} - {self.empleado.nombre}"

# Modelo para los Detalles de las Ventas
class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calcula el subtotal si no está especificado
        self.subtotal = self.cantidad * self.precio
        super(DetalleVenta, self).save(*args, **kwargs)

        # Actualiza el inventario en la sucursal correcta
        inventario, created = Inventario.objects.get_or_create(producto=self.producto, sucursal=self.venta.sucursal, defaults={'cantidad': 0})
        if inventario.cantidad >= self.cantidad:
            inventario.decrementar(self.cantidad)
        else:
            raise ValueError("No hay suficiente inventario en la sucursal para completar la venta.")

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} unidades"
