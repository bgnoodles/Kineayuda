from rest_framework import serializers
from .models import kinesiologo, paciente, cita, reseña
from django.utils import timezone

class kinesiologoSerializer(serializers.ModelSerializer):
    class Meta:
        model = kinesiologo
        fields = '__all__'

    def validate_estado_verificacion(self, value):
        if value not in dict(kinesiologo.ESTADO_VERIFICACION):
            raise serializers.ValidationError("Estado de verificación inválido.")
        return value

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
        if not data.get('paciente'):
            raise serializers.ValidationError("Se debe asignar un paciente válido.")
        if not data.get('kinesiologo'):
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
        if hasattr(cita, 'reseña'):
            raise serializers.ValidationError("Ya existe una reseña para esta cita.")
        
        return data