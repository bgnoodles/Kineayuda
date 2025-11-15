from rest_framework import serializers
from .models import kinesiologo, paciente, cita, reseña, agenda, metodoPago, pagoSuscripcion, documentoVerificacion
from django.utils import timezone
from .modulo_ia import analizar_sentimiento
from .utils.rut import normalizar_rut, formatear_rut
from django.db import transaction

class kinesiologoSerializer(serializers.ModelSerializer):
    class Meta:
        model = kinesiologo
        fields = '__all__'

    def validate_estado_verificacion(self, value):
        if value not in dict(kinesiologo.ESTADO_VERIFICACION):
            raise serializers.ValidationError("Estado de verificación inválido.")
        return value
    
    def validate_rut(self, value):
        try:
            return normalizar_rut(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['rut'] = formatear_rut(data['rut'])
        except Exception:
            pass
        return data

class pacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = paciente
        fields = '__all__'
    
    def validate_nombre(self, value):
        if not value:
            raise serializers.ValidationError("El nombre del paciente es obligatorio.")
        return value
    
    def validate_apellido(self, value):
        if not value:
            raise serializers.ValidationError("El apellido del paciente es obligatorio.")
        return value
    
    def validate_rut(self, value):
        try:
            return normalizar_rut(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['rut'] = formatear_rut(data['rut'])
        except Exception:
            pass
        return data

class citaSerializer(serializers.ModelSerializer):
    class Meta:
        model = cita
        fields = '__all__'
    
    def validate_fecha_hora(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Fecha de cita inválida.")
        return value

    def validate_estado(self, value):
        if value not in dict(cita.ESTADO_CITA):
            raise serializers.ValidationError("Estado de cita inválido.")
        return value
    
    def validate(self, data):
        paciente = data.get('paciente') or getattr(self.instance, 'paciente', None)
        kinesiologo = data.get('kinesiologo') or getattr(self.instance, 'kinesiologo', None)
        if not paciente:
            raise serializers.ValidationError("Se debe asignar un paciente válido.")
        if not kinesiologo:
            raise serializers.ValidationError("Se debe asignar un kinesiólogo válido")
        return data

class reseñaSerializer(serializers.ModelSerializer):
    class Meta:
        model = reseña
        fields = '__all__'
    
    def validate(self, data):
        cita = data.get('cita')
        if cita.estado != 'completada':
            raise serializers.ValidationError("No se puede crear una reseña para una cita que no está completada.")
        
        #Verificar que no exista una reseña para la misma cita
        if reseña.objects.filter(cita=cita).exists():
            raise serializers.ValidationError("Ya existe una reseña para esta cita.")
        
        return data
    
    def create(self, validated_data): #se sobreescribe el método create para agregar el análisis de sentimiento
        # Analizar el sentimiento del texto de la reseña utilizando el módulo de IA
        texto = validated_data.get('comentario')
        sentimiento = analizar_sentimiento(texto) #devuelve 'positiva', 'neutral' o 'negativa'
        validated_data['sentimiento'] = sentimiento
        return super().create(validated_data)
    
class agendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = agenda
        fields = '__all__'
        read_only_fields = ['estado', 'paciente', 'cita', 'kinesiologo', 'fecha_creacion']
    
    def validate(self, data):
        inicio = data.get('inicio')
        fin = data.get('fin')
        if not inicio or not fin:
            raise serializers.ValidationError("Se deben proporcionar tanto la hora de inicio como la de fin.")
        
        if inicio >= fin:
            raise serializers.ValidationError("La hora de inicio debe ser anterior a la hora de fin.")
        
        if inicio < timezone.now():
            raise serializers.ValidationError("La hora de inicio no puede ser en el pasado.")
        
        return data

class metodoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = metodoPago
        fields = '__all__'


class kinesiologoFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = kinesiologo
        fields = ['id','foto_perfil']
    
    def validate_foto_perfil(self, file):
        if not file:
            return file
        if file.size > 5 * 1024 * 1024:  # 5 MB limit
            raise serializers.ValidationError("El tamaño de la imagen no debe exceder los 5 MB.")
        valid_types = ['image/jpeg', 'image/png', 'image/webp']
        if hasattr(file, 'content_type') and file.content_type not in valid_types:
            raise serializers.ValidationError("Tipo de archivo no soportado. Use JPEG, PNG o WEBP.")
        return file

class documentoVerificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = documentoVerificacion
        fields = '__all__'
        read_only_fields = ['kinesiologo', 'fecha_subida', 'estado', 'comentario_revisor']

        def validate_archivo(self, file):
            if file.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("El tamaño del archivo no debe exceder los 10 MB.")
            valid_types = ['image/jpeg', 'image/png', 'application/pdf', 'image/webp']
            if hasattr(file, 'content_type') and file.content_type not in valid_types:
                raise serializers.ValidationError("Tipo de archivo no soportado. Use JPEG, PNG, WEBP o PDF.")
            return file

class KinesiologoRegistroSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    apellido = serializers.CharField(max_length=100)
    nro_titulo = serializers.CharField(max_length=100)
    rut = serializers.CharField(max_length=12)
    doc_verificacion = serializers.CharField(max_length=50, required = False, allow_blank = True)
    especialidad = serializers.CharField(max_length = 50)
    
    #Campos de los documentos de verificación
    doc_id_frente = serializers.FileField(write_only=True, required=True)
    doc_id_reverso = serializers.FileField(write_only=True, required=True)
    doc_titulo = serializers.FileField(write_only=True, required=True)
    doc_certificado = serializers.ListField(child=serializers.FileField(),write_only=True, required=False, allow_empty=True)

    def validate_rut(self, value):
        try:
            return normalizar_rut(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['rut'] = formatear_rut(data['rut'])
        except Exception:
            pass
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        #Crea el kinesiologo en estado pendiente y los documentos de verificación asociados
        request = self.context['request']
        user = getattr(request, 'user', None)
        uid = getattr(user, 'uid', None)
        email = getattr(user, 'email', None)

        if not uid or not email:
            raise serializers.ValidationError("Usuario no autenticado correctamente.")
        
        #pop a los datos de documentos de verificacion, que no pertenecen al modelo kinesiologo
        doc_id_frente = validated_data.pop('doc_id_frente')
        doc_id_reverso = validated_data.pop('doc_id_reverso')
        doc_titulo = validated_data.pop('doc_titulo')
        doc_certificados = validated_data.pop('doc_certificado', [])

        #Se crea el kinesiologo
        kx = kinesiologo.objects.create(
            nombre=validated_data['nombre'],
            apellido=validated_data['apellido'],
            email=email,
            firebase_ide=uid,
            nro_titulo=validated_data['nro_titulo'],
            rut=validated_data['rut'],
            doc_verificacion=validated_data.get('doc_verificacion', ''),
            especialidad=validated_data['especialidad'],
            estado_verificacion='pendiente'
        )

        #Crear los documentos de verificación asociados
        documentoVerificacion.objects.create(kinesiologo=kx, tipo='ID_FRENTE', archivo=doc_id_frente, estado='pendiente')
        documentoVerificacion.objects.create(kinesiologo=kx, tipo='ID_REVERSO', archivo=doc_id_reverso, estado='pendiente')
        documentoVerificacion.objects.create(kinesiologo=kx, tipo='TITULO', archivo=doc_titulo, estado='pendiente')
        for cert in doc_certificados:
            documentoVerificacion.objects.create(kinesiologo=kx, tipo='CERTIFICADO', archivo=cert, estado='pendiente')
        return kx