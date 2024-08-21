from datetime import date
from .models import Venta

def obtener_o_crear_venta_del_dia(empleado):
    hoy = date.today()
    venta_del_dia, created = Venta.objects.get_or_create(
        empleado=empleado,
        fecha_venta__date=hoy,
        defaults={'sucursal': empleado.sucursal}
    )
    return venta_del_dia
