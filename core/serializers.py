from rest_framework import serializers
from .models import Clase, Asistencia, Nota

# ------------------------------
# Serializer para Clase del Profesor
# ------------------------------
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


# ------------------------------
# Serializer para Asistencia
# ------------------------------
class AsistenciaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source='alumno.username', read_only=True)

    class Meta:
        model = Asistencia
        fields = ['id', 'alumno', 'alumno_nombre', 'clase', 'fecha', 'presente']


# ------------------------------
# Serializer para Nota
# ------------------------------
class NotaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source='alumno.username', read_only=True)
    promedio = serializers.FloatField(read_only=True)
    estado = serializers.SerializerMethodField()
    asistencia_pct = serializers.SerializerMethodField()
    curso_nombre = serializers.CharField(source='clase.curso.nombre', read_only=True) 
    nivel_nombre = serializers.CharField(source='clase.curso.nivel.nombre', read_only=True)
    horarios = serializers.SerializerMethodField()

    
    class Meta:
        model = Nota
        fields = [
            'id',
            'alumno',
            'alumno_nombre',
            'curso_nombre',
            'nivel_nombre', 
            'horarios',
            'nota1',
            'nota2',
            'nota3',
            'nota4',
            'promedio',
            'estado',
            'asistencia_pct',
        ]

    def get_asistencia_pct(self, obj):
        return obj.calcular_asistencia()

    def get_estado(self, obj):
        return obj.estado_aprobacion()

    # Validación de rango de notas
    def validate_nota1(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError("La nota debe estar entre 0 y 20")
        return value
    
    def get_horarios(self, obj):
        return [str(h) for h in obj.clase.horarios.all()]

