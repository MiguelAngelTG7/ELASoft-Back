from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db.models import Avg

# -----------------------------
# MODELO DE USUARIO PERSONALIZADO
# -----------------------------
class Usuario(AbstractUser):
    ROLES = (
        ('director', 'Director Académico'),
        ('profesor', 'Profesor'),
        ('alumno', 'Alumno'),
    )
    rol = models.CharField(max_length=20, choices=ROLES)

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


# -----------------------------
# MODELO DE NIVEL
# -----------------------------
class Nivel(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


# -----------------------------
# MODELO DE CURSO
# -----------------------------
class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    nivel = models.ForeignKey(Nivel, on_delete=models.CASCADE, related_name='cursos')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.nivel})"


# -----------------------------
# MODELO DE HORARIO
# -----------------------------
class Horario(models.Model):
    DIAS_SEMANA = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]
    dia = models.CharField(max_length=10, choices=DIAS_SEMANA)
    hora = models.TimeField()

    def __str__(self):
        return f"{self.get_dia_display()} - {self.hora.strftime('%I:%M %p')}"


# -----------------------------
# PROFESORES POR CURSO
# -----------------------------
class ProfesorCurso(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    profesor_titular = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='cursos_titular')
    profesor_asistente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='cursos_asistente', null=True, blank=True)

    def __str__(self):
        return f"{self.curso} | Titular: {self.profesor_titular}"


# -----------------------------
# PERIODO ACADÉMICO
# -----------------------------
class PeriodoAcademico(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    anio = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} ({self.anio})"


# -----------------------------
# CLASE
# -----------------------------
class Clase(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, null=True, blank=True)
    horarios = models.ManyToManyField(Horario)
    profesores = models.OneToOneField(ProfesorCurso, on_delete=models.CASCADE)
    alumnos = models.ManyToManyField(Usuario, limit_choices_to={'rol': 'alumno'}, blank=True)
    total_sesiones = models.PositiveIntegerField(default=8)

    def __str__(self):
        return f"Clase de {self.curso} - {self.periodo}"


# -----------------------------
# ASISTENCIA
# -----------------------------
class Asistencia(models.Model):
    alumno = models.ForeignKey(Usuario, on_delete=models.CASCADE, limit_choices_to={'rol': 'alumno'})
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    presente = models.BooleanField(default=False)

    class Meta:
        unique_together = ('alumno', 'clase', 'fecha')

    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return f"{self.alumno.username} - {estado} ({self.fecha})"


# -----------------------------
# NOTAS
# -----------------------------
class Nota(models.Model):
    alumno = models.ForeignKey(Usuario, on_delete=models.CASCADE, limit_choices_to={'rol': 'alumno'})
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)

    nota1 = models.DecimalField(max_digits=4, decimal_places=2)
    nota2 = models.DecimalField(max_digits=4, decimal_places=2)
    nota3 = models.DecimalField(max_digits=4, decimal_places=2)
    nota4 = models.DecimalField(max_digits=4, decimal_places=2)

    @property
    def promedio(self):
        return round((self.nota1 + self.nota2 + self.nota3 + self.nota4) / 4, 2)

    def calcular_asistencia(self):
        total = self.clase.total_sesiones or 1
        if total == 0:
            return 0
        presentes = Asistencia.objects.filter(clase=self.clase, alumno=self.alumno, presente=True).count()
        return round((presentes / total) * 100, 2)
    
    def estado_aprobacion(self):
        asistencia = self.calcular_asistencia()
        return "Aprobado" if self.promedio >= 10.5 and asistencia >= 75 else "Desaprobado"

    def __str__(self):
        return f"{self.alumno.username} - Prom: {self.promedio} - Asist: {self.calcular_asistencia()}% - {self.estado_aprobacion()}"
