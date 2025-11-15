from core.models import kinesiologo, pagoSuscripcion
from django.utils import timezone

def get_kinesiologo_from_request(request):
    """Obtiene el kinesiologo asociado al request basado en el uid de Firebase."""
    uid = getattr(request.user, 'uid', None)
    if not uid:
        return None
    return kinesiologo.objects.filter(firebase_ide=uid).first()

def kinesio_tiene_suscripcion_activa(kx) -> bool:
    """Retorna True si el kinesiologo tiene una suscripción válida."""
    if not kx:
        return False
    ultimo_pago = (pagoSuscripcion.objects
                    .filter(kinesiologo=kx, estado='pagado')
                    .order_by('-fecha_expiracion')
                    .first()
    )
    return bool(ultimo_pago and ultimo_pago.activa)