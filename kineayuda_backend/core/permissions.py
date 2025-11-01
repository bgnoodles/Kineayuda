from rest_framework.permissions import BasePermission
from core.utils.auth_helpers import get_kinesiologo_from_request, kinesio_tiene_suscripcion_activa

class TieneSuscripcionActiva(BasePermission):
    message = "Necesitas una suscripción activa para realizar esta acción."

    def has_permission(self, request, view):
        kx = get_kinesiologo_from_request(request)
        return bool(kx and kinesio_tiene_suscripcion_activa(kx))