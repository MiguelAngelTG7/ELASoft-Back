from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import date

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

    # Nuevos campos para alumnos
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    grupo_sanguineo = models.CharField(max_length=5, blank=True)
    alergias = models.TextField(blank=True)
    interesado = models.BooleanField(default=False)
    nuevo_creyente = models.BooleanField(default=False)
    bautizado = models.BooleanField(default=False)
    tiene_ministerio = models.BooleanField(default=False)

    def edad(self):
        if self.fecha_nacimiento:
            hoy = date.today()
            return hoy.year - self.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

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
# MODELO DE HORARIO
# -----------------------------
class Horario(models.Model):
    DIAS_SEMANA = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miercoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sabado', 'Sábado'),
        ('Domingo', 'Domingo'),
        ('Lunes a Viernes', 'Lunes a Viernes')
    ]
    dia = models.CharField(max_length=16, choices=DIAS_SEMANA)
    hora = models.TimeField()

    def __str__(self):
        return f"{self.get_dia_display()} - {self.hora.strftime('%I:%M %p')}"


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
    nombre = models.CharField(max_length=100, null=True)  
    nivel = models.ForeignKey(Nivel, on_delete=models.CASCADE, null=True, related_name='clases')
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, null=True, blank=True)
    horarios = models.ManyToManyField(Horario, blank=True)  

    profesor_titular = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='clases_titular', limit_choices_to={'rol': 'profesor'})
    profesor_asistente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='clases_asistente', limit_choices_to={'rol': 'profesor'})

    alumnos = models.ManyToManyField(Usuario, limit_choices_to={'rol': 'alumno'}, blank=True)
    total_sesiones = models.PositiveIntegerField(default=8)

    def __str__(self):
        return f"{self.nombre} — {self.nivel} ({self.periodo})"



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

    nota1 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    nota2 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    nota3 = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    nota4 = models.DecimalField(max_digits=4, decimal_places=2, default=0)

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


# -----------------------------
# SESION CLASE
# -----------------------------
class SesionClase(models.Model):
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='sesiones')
    fecha = models.DateField()

    def __str__(self):
        return f"{self.clase.nombre} - {self.fecha}"
