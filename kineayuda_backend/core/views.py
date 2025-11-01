from django.shortcuts import render
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from .models import kinesiologo, paciente, cita, reseña, agenda, metodoPago, pagoSuscripcion
from firebase_admin import auth
from .serializer import kinesiologoSerializer, pacienteSerializer, citaSerializer, reseñaSerializer, agendaSerializer, metodoPagoSerializer, pagoSuscripcionSerializer
from .utils.auth_helpers import get_kinesiologo_from_request, kinesio_tiene_suscripcion_activa
import uuid
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

class AgendaViewSet(viewsets.ModelViewSet):
    serializer_class = agendaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        kx = get_kinesiologo_from_request(self.request)
        if not kx:
            return agenda.objects.none()
        #Devuelve solo los horarios de la agenda del kinesiologo autenticado
        return agenda.objects.filter(kinesiologo=kx).order_by('inicio')

    def perform_create(self, serializer):
        kx = get_kinesiologo_from_request(self.request)
        if not kx:
            raise PermissionError("Kinesiologo no autenticado.")
        inicio = serializer.validated_data['inicio']
        fin = serializer.validated_data['fin']
        #Validar que no exista un horario solapado
        solapa = agenda.objects.filter(kinesiologo=kx, estado__in=['disponible', 'reservado', 'no_disponible'],).filter(Q(inicio__lt=fin) & Q(fin__gt=inicio)).exists()
        if solapa:
            raise ValueError("El horario solapa con otro existente.")
        #Asocia el horario al kinesiologo autenticado
        serializer.save(kinesiologo=kx, estado='disponible')
    
    def perform_destroy(self, instance):
        if instance.estado == 'reservado':
            raise ValueError("No se puede eliminar un horario que ya está reservado. Cancele la cita primero.")
        instance.delete()

class AgendarCitaView(APIView):
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        """Permite a un paciente agendar una cita en un horario disponible."""
        #validar que existe el cupo
        slot_id = request.data.get('id')
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
        paciente_obj = paciente.objects.filter(rut__iexact=rut).first()
        if not paciente_obj:
            paciente_serializer = pacienteSerializer(data=request.data)
            paciente_serializer.is_valid(raise_exception=True)
            paciente_obj = paciente_serializer.save()
        
        #Crear la cita asociada al cupo
        nueva_cita = cita.objects.create(
            paciente=paciente_obj,
            kinesiologo=slot.kinesiologo,
            fecha_hora=slot.inicio,
            estado='pendiente',
            nota=""
        )

        #Marcar el cupo como reservado
        slot.estado = 'reservado'
        slot.paciente = paciente_obj
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

@api_view(['GET'])
@permission_classes([AllowAny])
def lista_metodos_pago(request):
    qs = metodoPago.objects.filter(activo=True)
    return Response(metodoPagoSerializer(qs, many=True).data, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def iniciar_pago_suscripcion(request):
    kx = get_kinesiologo_from_request(request)
    if not kx:
        return Response({"error": "Perfil de kinesiólogo no encontrado"}, status=404)

    metodo_code = request.data.get('metodo')
    monto = request.data.get('monto')

    if not metodo_code or monto is None:
        return Response({"error": "Campos 'metodo' y 'monto' son requeridos"}, status=400)

    metodo = metodoPago.objects.filter(codigo_interno=metodo_code, activo=True).first()
    if not metodo:
        return Response({"error": "Método de pago no disponible"}, status=400)

    # Generar identificador de orden interno
    orden = str(uuid.uuid4())[:12]

    pago = pagoSuscripcion.objects.create(
        kinesiologo=kx,
        metodo=metodo,
        monto=monto,
        estado='pendiente',
        orden_comercio=orden,
        fecha_creacion=timezone.now()
    )

    # Placeholder de URL (Transbank o MercadoPago)
    redirect_url = f"https://sandbox.proveedor.com/pagar?orden={orden}"

    return Response({
        "mensaje": "Orden creada exitosamente",
        "orden_comercio": orden,
        "pago": pagoSuscripcionSerializer(pago).data,
        "redirect_url": redirect_url
    }, status=201)

@api_view(['POST'])
@permission_classes([AllowAny])  # proveedor no manda token
def webhook_pago(request, proveedor: str):
    data = request.data
    orden = data.get('orden_comercio')
    estado = data.get('estado')
    transa_id = data.get('transa_id_externo')

    if not orden:
        return Response({"error": "orden_comercio requerido"}, status=400)

    try:
        pago = pagoSuscripcion.objects.get(orden_comercio=orden)
    except pagoSuscripcion.DoesNotExist:
        return Response({"error": "Orden no encontrada"}, status=404)

    pago.raw_payload = data
    pago.transa_id_externo = transa_id

    if estado == 'pagado':
        pago.estado = 'pagado'
        pago.fecha_expiracion = timezone.now() + timedelta(days=30)
    elif estado in ['pendiente', 'fallido', 'expirado']:
        pago.estado = estado
    else:
        pago.estado = 'fallido'

    pago.save()
    return Response({"mensaje": "actualizado correctamente"}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_suscripcion(request):
    kx = get_kinesiologo_from_request(request)
    if not kx:
        return Response({"error": "Perfil no encontrado"}, status=404)

    ultimo_pago = pagoSuscripcion.objects.filter(kinesiologo=kx).order_by('-fecha_pago').first()

    activa = kinesio_tiene_suscripcion_activa(kx)
    vence = ultimo_pago.fecha_expiracion if ultimo_pago else None

    return Response({
        "activa": activa,
        "vence": vence,
        "ultimo_pago": pagoSuscripcionSerializer(ultimo_pago).data if ultimo_pago else None
    }, status=200)
