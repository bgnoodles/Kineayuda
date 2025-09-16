from django.shortcuts import render
from rest_framework import viewsets
from .models import kinesiologo, paciente, cita, reseña
from .serializer import kinesiologoSerializer, pacienteSerializer, citaSerializer, reseñaSerializer
# Create your views here.

class kinesiologoViewSet(viewsets.ModelViewSet):
    queryset = kinesiologo.objects.all()
    serializer_class = kinesiologoSerializer

class pacienteViewSet(viewsets.ModelViewSet):
    queryset = paciente.objects.all()
    serializer_class = pacienteSerializer

class citaViewSet(viewsets.ModelViewSet):
    queryset = cita.objects.all()
    serializer_class = citaSerializer

class reseñaViewSet(viewsets.ModelViewSet):
    queryset = reseña.objects.all()
    serializer_class = reseñaSerializer