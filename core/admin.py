from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Nivel, Curso, Usuario, Horario, ProfesorCurso, Clase, Asistencia, Nota, PeriodoAcademico

class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Información adicional", {
            'fields': (
                'rol',
                'fecha_nacimiento',
                'direccion',
                'telefono',
                'grupo_sanguineo',
                'alergias',
                'interesado',
                'nuevo_creyente',
                'bautizado',
                'tiene_ministerio',
                'otros',
            ),
        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'telefono')

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Nivel)
admin.site.register(Curso)
admin.site.register(Horario)
admin.site.register(ProfesorCurso)
admin.site.register(Clase)
admin.site.register(Asistencia)
admin.site.register(Nota)
admin.site.register(PeriodoAcademico)
