from django.contrib import admin
from .models import Proveedor, Producto, Sucursal, Compra, DetalleCompra, Inventario, Transferencia, Venta, DetalleVenta

admin.site.register(Proveedor)
admin.site.register(Producto)
admin.site.register(Sucursal)
admin.site.register(Compra)
admin.site.register(DetalleCompra)
admin.site.register(Inventario)
admin.site.register(Transferencia)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
