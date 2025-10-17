from rest_framework import serializers
from .models import kinesiologo, paciente, cita, reseña
from django.utils import timezone
from .modulo_ia import analizar_sentimiento
from .utils.rut import normalizar_rut, formatear_rut

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