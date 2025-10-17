from rest_framework import routers
from django.urls import path, include
from .views import kinesiologoViewSet, pacienteViewSet, citaViewSet, reseñaViewSet, verificar_firebase_token

router = routers.DefaultRouter()
router.register(r'kinesiologos', kinesiologoViewSet)
router.register(r'pacientes', pacienteViewSet)
router.register(r'citas', citaViewSet)
router.register(r'reseñas', reseñaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/verify', verificar_firebase_token, name='verificar_token'),
]