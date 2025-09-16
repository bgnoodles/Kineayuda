from django.contrib import admin
from .models import kinesiologo, paciente, cita, reseña

# Register your models here.
admin.site.register(kinesiologo)
admin.site.register(paciente)
admin.site.register(cita)
admin.site.register(reseña)