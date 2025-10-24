from rest_framework import routers
from django.urls import path, include
from .views import kinesiologoViewSet, pacienteViewSet, citaViewSet, reseñaViewSet, verificar_firebase_token, me

router = routers.DefaultRouter()
router.register(r'kinesiologos', kinesiologoViewSet, basename='kinesiologo')
router.register(r'pacientes', pacienteViewSet, basename='paciente')
router.register(r'citas', citaViewSet, basename='cita')
router.register(r'reseñas', reseñaViewSet, basename='reseña')

urlpatterns = [
    path('', include(router.urls)),
    path('login/verify', verificar_firebase_token, name='verificar_token'),
    path('me/', me, name='me'),
]