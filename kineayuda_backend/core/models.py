from django.db import models

# Create your models here.

#CLASE KINESIOLOGO QUE CREA LA TABLA KINESIOLOGO EN LA BD POSTGRE
class kinesiologo (models.Model):
    ESTADO_VERIFICACION = [
        ('pendiente', 'pendiente'),
        ('aprobado', 'aprobado'),
        ('rechazado', 'rechazado')
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    firebase_ide = models.CharField(max_length=100, unique=True, blank=True, null=True)
    nro_titulo = models.CharField(max_length=50)
    rut = models.CharField(max_length=15, unique=True)
    doc_verificacion = models.CharField(max_length=50)
    especialidad = models.CharField(max_length=50)
    estado_verificacion = models.CharField(max_length=20, choices=ESTADO_VERIFICACION, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

#CLASE PACIENTE QUE CREA LA TABLA PACIENTE EN LA BD POSTGRE
class paciente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
#CLASE CITA QUE CREA LA TABLA CITA EN LA BD POSTGRE
class cita(models.Model):
    ESTADO_CITA = [
        ('pendiente', 'pendiente'),
        ('completada', 'completada'),
        ('cancelada', 'cancelada')       
    ]

    paciente = models.ForeignKey(paciente, on_delete=models.CASCADE, related_name='cita')
    kinesiologo = models.ForeignKey(kinesiologo, on_delete=models.CASCADE, related_name='cita')
    fecha_hora = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CITA, default='pendiente')
    nota = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cita {self.id} - {self.paciente} con {self.kinesiologo}"
    
#CLASE RESEÑA QUE CREA LA TABLA RESEÑA EN LA BD POSTGRE
class reseña(models.Model):
    OPCIONES_SENTIMIENTO = [
        ('positiva', 'positiva'),
        ('neutral', 'neutral'),
        ('negativa', 'negativa')       
    ]

    cita = models.ForeignKey(cita, on_delete=models.CASCADE, related_name='reseña')
    comentario = models.TextField()
    sentimiento = models.CharField(max_length=10, choices=OPCIONES_SENTIMIENTO, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña cita {self.cita.id} - {self.sentimiento}"