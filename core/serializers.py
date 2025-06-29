from datetime import date
from rest_framework import serializers
from .models import Clase, Asistencia, Nota, Usuario

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

    def validate_nota1(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError("La nota debe estar entre 0 y 20")
        return value
    
    def get_horarios(self, obj):
        return [str(h) for h in obj.clase.horarios.all()]
    
# ------------------------------
# Serializer para Registro de Alumno
# ------------------------------
    
class AlumnoRegistroSerializer(serializers.ModelSerializer):
    class_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Usuario
        fields = [
            'username', 'password', 'first_name', 'last_name', 'email',
            'fecha_nacimiento', 'direccion', 'telefono', 'grupo_sanguineo',
            'alergias',
            'interesado', 'nuevo_creyente', 'bautizado', 'tiene_ministerio',
            'class_id'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6}
        }

    def create(self, validated_data):
        class_id = validated_data.pop('class_id')
        password = validated_data.pop('password')

        user = Usuario.objects.create_user(
            **validated_data,
            password=password,
            rol='alumno'
        )

        try:
            clase = Clase.objects.get(id=class_id)
            clase.alumnos.add(user)
        except Clase.DoesNotExist:
            raise serializers.ValidationError({'class_id': 'Clase no encontrada'})

        return user

# ------------------------------
# Serializer para Buscar Alumno
# ------------------------------

class UsuarioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'rol', 'nombre_completo']

    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
# ------------------------------
# Serializer para Profesor Ve e Imprime Datos de Alumno
# ------------------------------

from rest_framework import serializers
from datetime import date
from .models import Usuario

class AlumnoDetalleSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    edad = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'nombre_completo',
            'fecha_nacimiento',
            'edad',
            'email',
            'telefono',
            'direccion',
            'interesado',
            'nuevo_creyente',
            'bautizado',
            'tiene_ministerio',
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_edad(self, obj):
        if obj.fecha_nacimiento:
            today = date.today()
            return today.year - obj.fecha_nacimiento.year - (
                (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
            )
        return None
