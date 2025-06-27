from rest_framework import serializers
from .models import Clase, Asistencia


class ClaseProfesorSerializer(serializers.ModelSerializer):
    curso_nombre = serializers.CharField(source='curso.nombre')
    periodo_nombre = serializers.CharField(source='periodo.nombre')
    horarios = serializers.SerializerMethodField()
    profesor_titular = serializers.CharField(source='profesores.profesor_titular.username', default=None)
    profesor_asistente = serializers.CharField(source='profesores.profesor_asistente.username', default=None)
    alumnos = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Clase
        fields = [
            'id',
            'curso_nombre',
            'periodo_nombre',
            'horarios',
            'profesor_titular',
            'profesor_asistente',
            'alumnos',
            'nombre_completo',
        ]

    def get_horarios(self, obj):
        return [str(horario) for horario in obj.horarios.all()]

    def get_alumnos(self, obj):
        return [alumno.username for alumno in obj.alumnos.all()]

    def get_nombre_completo(self, obj):
        horarios = ", ".join(str(h) for h in obj.horarios.all())
        return f"{obj.curso.nombre} — {obj.periodo.nombre} ({horarios})"


class AsistenciaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source='alumno.username', read_only=True)

    class Meta:
        model = Asistencia
        fields = ['id', 'alumno', 'alumno_nombre', 'clase', 'fecha', 'presente']
