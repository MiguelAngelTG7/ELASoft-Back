from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Nivel, Usuario, Horario, Clase, Asistencia, Nota, PeriodoAcademico, SesionClase

admin.site.site_header = "ELASoft Admin"
admin.site.site_title = "ELASoft Admin"
admin.site.index_title = "Panel de Administración de ELASoft"

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
                'tiene_ministerio'
            ),
        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'telefono')

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Nivel)
admin.site.register(Horario)

class SesionClaseInline(admin.TabularInline):
    model = SesionClase
    extra = 1

@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nivel", "periodo", "total_sesiones")
    search_fields = ("nombre",)
    list_filter = ("nivel", "periodo")
    fieldsets = (
        (None, {
            'fields': ('nombre', 'nivel', 'periodo', 'horarios', 'profesor_titular', 'profesor_asistente', 'alumnos', 'total_sesiones')
        }),
    )
    inlines = [SesionClaseInline]

admin.site.register(Asistencia)
admin.site.register(Nota)
admin.site.register(PeriodoAcademico)
