from django.contrib import admin
from .models import kinesiologo, paciente, cita, reseña, documentoVerificacion

# Register your models here.
admin.site.register(kinesiologo)
admin.site.register(paciente)
admin.site.register(cita)
admin.site.register(reseña)

@admin.register(documentoVerificacion)
class DocumentoVerificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'kinesiologo', 'tipo', 'estado', 'fecha_subida')
    list_filter = ('estado', 'tipo')
    search_fields = ('kinesiologo__nombre', 'kinesiologo__apellido', 'kinesiologo__email')