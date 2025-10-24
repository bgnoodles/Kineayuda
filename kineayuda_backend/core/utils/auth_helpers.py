from core.models import kinesiologo

def get_kinesiologo_from_request(request):
    """Obtiene el kinesiologo asociado al request basado en el uid de Firebase."""
    uid = getattr(request.user, 'uid', None)
    if not uid:
        return None
    return kinesiologo.objects.filter(firebase_ide=uid).first()