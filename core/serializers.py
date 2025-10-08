from datetime import date
from rest_framework import serializers
from .models import Clase, Asistencia, Nota, Usuario, RecursoCurso

# ------------------------------
# Serializer para Clase del Profesor
# ------------------------------

class ClaseProfesorSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField()
    periodo_nombre = serializers.CharField(source='clase.periodo.nombre', default='', read_only=True)
    nivel_nombre = serializers.CharField(source='nivel.nombre', default='', read_only=True)
    horarios = serializers.SerializerMethodField()
    profesor_titular = serializers.SerializerMethodField()
    profesor_asistente = serializers.SerializerMethodField()
    alumnos = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Clase
        fields = [
            'id',
            'nombre',
            'periodo_nombre',
            'nivel_nombre',
            'horarios',
            'profesor_titular',
            'profesor_asistente',
            'alumnos',
            'nombre_completo',
        ]


    def get_profesor_titular(self, obj):
        return getattr(obj.profesor_titular, 'username', None)


    def get_profesor_asistente(self, obj):
        return getattr(obj.profesor_asistente, 'username', None)


    def get_alumnos(self, obj):
        return [alumno.username for alumno in obj.alumnos.all()]


    def get_nombre_completo(self, obj):
        horarios = ", ".join(str(h) for h in obj.horarios.all())
        periodo = getattr(obj.periodo, 'nombre', 'Sin periodo')
        return f"{obj.nombre} — {periodo} ({horarios})"

    def get_horarios(self, obj):
        return [str(h) for h in obj.horarios.all()]


# ------------------------------
# Serializer para Asistencia
# ------------------------------

class AsistenciaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Asistencia
        fields = ['id', 'alumno', 'alumno_nombre', 'clase', 'fecha', 'presente']

    def get_alumno_nombre(self, obj):
        full_name = f"{obj.alumno.first_name} {obj.alumno.last_name}".strip()
        return full_name if full_name else obj.alumno.username

# ------------------------------
# Serializer para Nota
# ------------------------------

class NotaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source='alumno.username', read_only=True)
    promedio = serializers.FloatField(read_only=True)
    participacion_promedio = serializers.FloatField(read_only=True)  # Nuevo campo
    estado = serializers.SerializerMethodField()
    asistencia_pct = serializers.SerializerMethodField()
    curso_nombre = serializers.CharField(source='clase.nombre', default='', read_only=True)
    nivel_nombre = serializers.CharField(source='clase.nivel.nombre', default='', read_only=True)
    periodo_nombre = serializers.CharField(source='clase.periodo.nombre', default='', read_only=True)
    horarios = serializers.SerializerMethodField()
    clase_id = serializers.IntegerField(source='clase.id', read_only=True)
    profesor_nombre = serializers.SerializerMethodField()
    profesor_telefono = serializers.SerializerMethodField()

    class Meta:
        model = Nota
        fields = [
            'id',
            'alumno',
            'alumno_nombre',
            'curso_nombre',
            'nivel_nombre',
            'periodo_nombre',
            'horarios',
            'profesor_nombre',
            'profesor_telefono',
            'participacion_1',        # Nuevo campo
            'participacion_2',        # Nuevo campo
            'participacion_3',        # Nuevo campo
            'participacion_promedio', # Nuevo campo calculado
            'tareas',
            'examen_final',
            'promedio',
            'estado',
            'asistencia_pct',
            'clase_id',
        ]

    def get_asistencia_pct(self, obj):
        return obj.calcular_asistencia()

    def get_estado(self, obj):
        return obj.estado_aprobacion()

    # Validaciones para las tres participaciones
    def validate_participacion_1(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError("La nota debe estar entre 0 y 20")
        return value

    def validate_participacion_2(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError("La nota debe estar entre 0 y 20")
        return value

    def validate_participacion_3(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError("La nota debe estar entre 0 y 20")
        return value

    def validate_tareas(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError("La nota debe estar entre 0 y 20")
        return value

    def validate_examen_final(self, value):
        if value < 0 or value > 20:
            raise serializers.ValidationError("La nota debe estar entre 0 y 20")
        return value

    def get_horarios(self, obj):
        if hasattr(obj.clase, 'horarios'):
            return [str(h) for h in obj.clase.horarios.all()]
        return []

    def get_profesor_nombre(self, obj):
        if obj.clase.profesor_titular:
            return obj.clase.profesor_titular.get_full_name()
        return '-'

    def get_profesor_telefono(self, obj):
        if obj.clase.profesor_titular and hasattr(obj.clase.profesor_titular, 'telefono'):
            return obj.clase.profesor_titular.telefono or '-'
        return '-'


# ------------------------------
# Serializer para Registro de Alumno
# ------------------------------
class AlumnoRegistroSerializer(serializers.ModelSerializer):


    class Meta:
        model = Usuario
        fields = [
            'username', 'password', 'first_name', 'last_name', 'email',
            'fecha_nacimiento', 'direccion', 'telefono',
            'enfermedades', 'medicamentos_y_dosis',
            'interesado', 'nuevo_creyente', 'bautizado', 'tiene_ministerio'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(
            **validated_data,
            password=password,
            rol='alumno'
        )
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
# Serializer para Lista del Alumno
# ------------------------------
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
            'enfermedades',
            'medicamentos_y_dosis',
            'interesado',
            'nuevo_creyente',
            'bautizado',
            'tiene_ministerio',
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_edad(self, obj):
        if obj.fecha_nacimiento:
            today = date.today()
            return today.year - obj.fecha_nacimiento.year - (
                (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
            )
        return None

# ------------------------------
# Serializer para Lista de Profesores
# ------------------------------

class ProfesorListaSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    edad = serializers.SerializerMethodField()
    cursos = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id',
            'nombre_completo',
            'cursos',
            'fecha_nacimiento',
            'edad',
            'email',
            'telefono',
            'direccion',
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_edad(self, obj):
        if obj.fecha_nacimiento:
            today = date.today()
            return today.year - obj.fecha_nacimiento.year - (
                (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
            )
        return None

    def get_cursos(self, obj):
        # Clases donde es titular
        clases_titular = Clase.objects.filter(profesor_titular=obj).prefetch_related('horarios')
        # Clases donde es asistente
        clases_asistente = Clase.objects.filter(profesor_asistente=obj).prefetch_related('horarios')

        cursos = []

        for clase in clases_titular:
            horarios = ", ".join([str(h) for h in clase.horarios.all()])
            if horarios:
                cursos.append(f"{clase.nombre} ({horarios}) - Titular")
            else:
                cursos.append(f"{clase.nombre} - Titular")

        for clase in clases_asistente:
            if clase not in clases_titular:
                horarios = ", ".join([str(h) for h in clase.horarios.all()])
                if horarios:
                    cursos.append(f"{clase.nombre} ({horarios}) - Asistente")
                else:
                    cursos.append(f"{clase.nombre} - Asistente")

        return cursos

# ------------------------------
# Serializer para Recursos de Curso
# ------------------------------

class RecursoCursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecursoCurso
        fields = ['id', 'titulo', 'url', 'tipo', 'fecha', 'clase']
        extra_kwargs = {'clase': {'write_only': True}}

