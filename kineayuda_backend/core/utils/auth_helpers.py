from core.models import kinesiologo, pagoSuscripcion
from django.utils import timezone

def get_kinesiologo_from_request(request):
    """Obtiene el kinesiologo asociado al request basado en el uid de Firebase."""
    uid = getattr(request.user, 'uid', None)
    if not uid:
        return None
    return kinesiologo.objects.filter(firebase_ide=uid).first()

def kinesio_tiene_suscripcion_activa(kx) -> bool:
    """Retorna True si el kinesiologo tiene una suscripción pagada."""
    if not kx:
        return False
    ahora = timezone.now()
    return pagoSuscripcion.objects.filter(
        kinesiologo=kx,
        estado='pagado',
        fecha_expiracion__gt=ahora
    ).exists()