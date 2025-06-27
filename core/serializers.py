from rest_framework import serializers
from .models import Clase

class ClaseProfesorSerializer(serializers.ModelSerializer):
    curso_nombre = serializers.CharField(source='curso.nombre')
    periodo_nombre = serializers.CharField(source='periodo.nombre')

    class Meta:
        model = Clase
        fields = ['id', 'curso_nombre', 'periodo_nombre']
