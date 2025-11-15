from django.db import models
from django.utils import timezone
from decimal import Decimal
import os
import uuid

# Create your models here.

def kx_profile_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"kinesiologos/{instance.id}/pefil{ext}"

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
    foto_perfil = models.ImageField(upload_to=kx_profile_upload_path, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class paciente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    rut = models.CharField(max_length=15, unique=True, null=False)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

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
    estado_pago = models.CharField(max_length=20,
                                    choices=[('pendiente', 'pendiente'), ('pagado', 'pagado'), ('fallido', 'fallido')],
                                    default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cita {self.id} - {self.paciente} con {self.kinesiologo}"

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

class agenda(models.Model):
    ESTADO_HORARIO = [
        ('disponible', 'disponible'),
        ('reservado', 'reservado'),
        ('no_disponible', 'no_disponible'),
        ('expirado', 'expirado'),
    ]

    kinesiologo = models.ForeignKey(kinesiologo, on_delete=models.CASCADE, related_name='agenda')
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_HORARIO, default='disponible')
    paciente = models.ForeignKey('paciente', on_delete=models.SET_NULL, blank=True, null=True, related_name='cupo_reservado')
    cita = models.OneToOneField('cita', on_delete=models.SET_NULL, blank=True, null=True, related_name='cupo_agenda')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kinesiologo.nombre} {self.kinesiologo.apellido} - {self.inicio} a {self.fin} ({self.estado})"
    
    def activa_para_reserva(self):
        return (self.estado == 'disponible' and self.inicio >= timezone.now())

class metodoPago(models.Model):
    nombre = models.CharField(max_length=100)
    codigo_interno = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class pagoSuscripcion(models.Model):
    ESTADO_TRANSACCION = [
        ('pendiente', 'pendiente'),
        ('pagado', 'pagado'),
        ('fallido', 'fallido'),
        ('expirado', 'expirado'),
    ]

    kinesiologo = models.ForeignKey(kinesiologo, on_delete=models.CASCADE, related_name='pagos_suscripcion')
    metodo = models.ForeignKey(metodoPago, on_delete=models.SET_NULL, null=True, related_name='transacciones')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_TRANSACCION, default='pendiente', db_index=True)
    orden_comercio= models.CharField(max_length=120, unique=True, blank=True, null=True)
    transa_id_externo = models.CharField(max_length=200, blank=True, null=True)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(blank=True, null=True, db_index=True)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    #Auditoria
    raw_payload = models.JSONField(blank=True, null=True) #Cuerpo del webhook recibido para trazabilidad

    def __str__(self):
        return f"{self.kinesiologo.nombre} {self.kinesiologo.apellido} - {self.estado} - {self.monto} CLP"
    
    @property
    def activa(self) -> bool:
        return self.estado == 'pagado' and self.fecha_expiracion and self.fecha_expiracion > timezone.now()

def kx_doc_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    name = f"{uuid.uuid4().hex}{ext}"
    return f"kinesiologos/{instance.kinesiologo_id}/verificacion/{instance.tipo}/{name}"

class documentoVerificacion(models.Model):
    TIPOS = [
        ('ID_FRENTE', 'Carnet frente'),
        ('ID_REVERSO', 'Carnet reverso'),
        ('TITULO', 'Título/diploma'),
        ('CERTIFICADO', 'Certificado adicional'),
        ('OTRO', 'Otro'),
    ]

    ESTADO = [
        ('pendiente', 'pendiente'),
        ('aprobado', 'aprobado'),
        ('rechazado', 'rechazado'),
    ]

    kinesiologo = models.ForeignKey(kinesiologo, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    archivo = models.FileField(upload_to=kx_doc_upload_path)
    estado = models.CharField(max_length=10, choices=ESTADO, default='pendiente')
    comentario_revisor = models.TextField(blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kinesiologo} - {self.tipo} - {self.estado}"

class pagoCita(models.Model):
    ESTADO_TRANSACCION = [
        ('pendiente', 'pendiente'),
        ('pagado', 'pagado'),
        ('fallido', 'fallido'),
    ]

    cita = models.OneToOneField('cita', on_delete=models.CASCADE, related_name='pago_cita')
    kinesiologo = models.ForeignKey('kinesiologo', on_delete=models.CASCADE, related_name='pagos_citas')
    paciente = models.ForeignKey('paciente', on_delete=models.CASCADE, related_name='pagos_citas')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_TRANSACCION, default='pendiente', db_index=True)
    buy_order = models.CharField(max_length=120, unique=True, blank=True, null=True)
    session_id = models.CharField(max_length=120, blank=True, null=True)
    token_ws = models.CharField(max_length=200, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_pago = models.DateTimeField(blank=True, null=True)

    raw_payload = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Cita {self.cita_id} - {self.estado} - {self.monto} CLP"