from django.shortcuts import render
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from .models import kinesiologo, paciente, cita, reseña, agenda
from firebase_admin import auth
from .serializer import kinesiologoSerializer, pacienteSerializer, citaSerializer, reseñaSerializer
from .utils.auth_helpers import get_kinesiologo_from_request
# Create your views here.

class kinesiologoViewSet(viewsets.ModelViewSet):
    serializer_class = kinesiologoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        #Devuelve solo el perfil del kine logeado
        kx = get_kinesiologo_from_request(self.request)
        if not kx:
            #Si aun no tiene perfil, no ve nada en el listado
            return kinesiologo.objects.none()
        #Solo puede ver su propio perfil
        return kinesiologo.objects.filter(id=kx.id)
    
    def perform_create(self, serializer):
        uid = self.request.user.uid #UID de Firebase del kinesiologo autenticado
        #Asocia el firebase_ide al crear el kinesiologo
        serializer.save(firebase_ide=uid)
    
    def perform_update(self, serializer):
        uid = self.request.user.uid
        #Asegura que el firebase_ide no cambie a otro valor
        serializer.save(firebase_ide=uid)

class pacienteViewSet(viewsets.ModelViewSet):
    queryset = paciente.objects.all()
    serializer_class = pacienteSerializer

class citaViewSet(viewsets.ModelViewSet):
    serializer_class = citaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        kx = get_kinesiologo_from_request(self.request)
        if not kx:
            return cita.objects.none()
        #Devuelve solo las citas del kinesiologo autenticado
        return cita.objects.filter(kinesiologo=kx).select_related('paciente', 'kinesiologo')
    
    def perform_create(self, serializer):
        kx = get_kinesiologo_from_request(self.request)
        if not kx:
            raise PermissionError("Kinesiologo no autenticado.")
        #Asocia la cita al kinesiologo autenticado
        serializer.save(kinesiologo=kx)

class reseñaViewSet(viewsets.ModelViewSet):
    serializer_class = reseñaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        kx = get_kinesiologo_from_request(self.request)
        if not kx:
            return reseña.objects.none()
        #Devuelve solo las reseñas de las citas del kinesiologo autenticado
        return reseña.objects.filter(cita__kinesiologo=kx).select_related('cita', 'cita__paciente')

class KinesiologosPublicosView(ListAPIView):
    """Vista pública para listar todos los kinesiologos aprobados."""
    serializer_class = kinesiologoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        especialidad = self.request.query_params.get('especialidad')
        qset = kinesiologo.objects.filter(estado_verificacion='aprobado')
        if especialidad:
            qset = qset.filter(especialidad__iexact=especialidad)
        return qset

class ReseñasPublicasView(ListAPIView):
    """Vista pública para listar todas las reseñas."""
    permission_classes = [AllowAny]

    def get(self, request, kinesiologo_id):
        qset = reseña.objects.filter(cita__kinesiologo_id=kinesiologo_id)
        data = reseñaSerializer(qset, many=True).data
        return Response(data, status=status.HTTP_200_OK)

class HorasDisponiblesView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, kinesiologo_id):
        """Devuelve las horas disponibles para reserva de un kinesiologo específico."""
        ahora = timezone.now()
        slots = agenda.objects.filter(kinesiologo_id=kinesiologo_id, estado='disponible', inicio__gte=ahora).order_by('inicio')
        data = [{
            'id': slot.id,
            'inicio': slot.inicio,
            'fin': slot.fin
        } for slot in slots]
        return Response(data, status=status.HTTP_200_OK)

class AgendarCitaView(APIView):
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        """Permite a un paciente agendar una cita en un horario disponible."""
        #validar que existe el cupo
        slot_id = request.data.get('slot_id')
        if not slot_id:
            return Response({'error': 'slot_id es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            slot = agenda.objects.select_for_update().get(id=slot_id)
        except agenda.DoesNotExist:
            return Response({'error': 'Cupo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        #Validar que el cupo esta disponible
        if slot.estado != 'disponible' or slot.inicio < timezone.now():
            return Response({'error': 'Cupo no disponible para reserva.'}, status=status.HTTP_400_BAD_REQUEST)
        
        #Crear o reutilizar paciente según el RUT
        rut = request.data.get('rut')
        paciente = paciente.objects.filter(rut__iexact=rut).first()
        if not paciente:
            paciente_serializer = pacienteSerializer(data=request.data)
            paciente_serializer.is_valid(raise_exception=True)
            paciente = paciente_serializer.save()
        
        #Crear la cita asociada al cupo
        nueva_cita = cita.objects.create(
            paciente=paciente,
            kinesiologo=slot.kinesiologo,
            fecha_hora=slot.inicio,
            estado='pendiente',
            nota=""
        )

        #Marcar el cupo como reservado
        slot.estado = 'reservado'
        slot.paciente = paciente
        slot.cita = nueva_cita
        slot.save()

        return Response({'mensaje': 'Cita agendada exitosamente.', 'cita': citaSerializer(nueva_cita).data}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
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