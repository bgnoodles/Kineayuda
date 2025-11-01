from rest_framework import routers
from django.urls import path, include
from .views import (kinesiologoViewSet, pacienteViewSet, citaViewSet, reseñaViewSet, verificar_firebase_token, me, AgendaViewSet, 
                    AgendarCitaView, HorasDisponiblesView, KinesiologosPublicosView, ReseñasPublicasView, lista_metodos_pago, iniciar_pago_suscripcion, webhook_pago, estado_suscripcion)

router = routers.DefaultRouter()
router.register(r'kinesiologos', kinesiologoViewSet, basename='kinesiologo')
router.register(r'pacientes', pacienteViewSet, basename='paciente')
router.register(r'citas', citaViewSet, basename='cita')
router.register(r'reseñas', reseñaViewSet, basename='reseña')
router.register(r'agendas', AgendaViewSet, basename='agenda')

urlpatterns = [
    path('', include(router.urls)),
    path('login/verify', verificar_firebase_token, name='verificar_token'),
    path('me/', me, name='me'),
    path('public/kinesiologos/', KinesiologosPublicosView.as_view()),
    path('public/kinesiologos/<int:kinesiologo_id>/resenas/', ReseñasPublicasView.as_view()),
    path('public/kinesiologos/<int:kinesiologo_id>/horas/', HorasDisponiblesView.as_view()),
    path('public/agendar/', AgendarCitaView.as_view()),
    path('pagos/metodos/', lista_metodos_pago),
    path('pagos/iniciar/', iniciar_pago_suscripcion),
    path('pagos/webhook/<str:proveedor>/', webhook_pago),
    path('pagos/estado/', estado_suscripcion),   
]