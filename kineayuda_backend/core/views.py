from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import kinesiologo, paciente, cita, reseña
from firebase_admin import auth
from .serializer import kinesiologoSerializer, pacienteSerializer, citaSerializer, reseñaSerializer
from .utils.auth_helpers import get_kinesiologo_from_request
# Create your views here.

class kinesiologoViewSet(viewsets.ModelViewSet):
    queryset = kinesiologo.objects.all()
    serializer_class = kinesiologoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        kx = get_kinesiologo_from_request(self.request)
        if not kx:
            #Si aun no tiene perfil, no ve nada en el listado
            return kinesiologo.objects.none()
        #Solo puede ver su propio perfil
        return kinesiologo.objects.filter(id=kx.id)
    
    def perform_create(self, serializer):
        uid = self.request.user #UID de Firebase del kinesiologo autenticado
        #Asocia el firebase_ide al crear el kinesiologo
        serializer.save(firebase_ide=uid)
    
    def perform_update(self, serializer):
        uid = self.request.user
        #Asegura que el firebase_ide no cambie a otro valor
        serializer.save(firebase_ide=uid)

class pacienteViewSet(viewsets.ModelViewSet):
    queryset = paciente.objects.all()
    serializer_class = pacienteSerializer

class citaViewSet(viewsets.ModelViewSet):
    queryset = cita.objects.all()
    serializer_class = citaSerializer

class reseñaViewSet(viewsets.ModelViewSet):
    queryset = reseña.objects.all()
    serializer_class = reseñaSerializer

@api_view(['POST'])
def verificar_firebase_token(request):
    #Verifica el token de Firebase enviado en la solicitud y devuelve la información del usuario si es válido.
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token no proporcionado.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        decoded = auth.verify_id_token(token)
        return Response({'uid': decoded['uid'], 
                         'email': decoded.get('email')}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    kx = get_kinesiologo_from_request(request)
    if not kx:
        return Response({'detail': 'Kinesiologo no encontrado. ¿Ya registraste tu cuenta?'}, status=404)
    return Response(kinesiologoSerializer(kx).data)