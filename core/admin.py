from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Nivel, Usuario, Horario, Clase, Asistencia, Nota, PeriodoAcademico, SesionClase, RecursoCurso

admin.site.site_header = "ELASoft Admin"
admin.site.site_title = "ELASoft Admin"
admin.site.index_title = "Panel de Administración de ELASoft"

# Usuario admin
class UsuarioResource(resources.ModelResource):
    class Meta:
        model = Usuario

@admin.register(Usuario)
class UsuarioAdmin(ImportExportModelAdmin, UserAdmin):
    resource_class = UsuarioResource
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'telefono')
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

admin.site.register(Nivel)
admin.site.register(Horario)

class SesionClaseInline(admin.TabularInline):
    model = SesionClase
    extra = 1

# Clase admin personalizado con ID visible y sesiones reales
@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'nivel', 'periodo', 'sesiones_count')
    search_fields = ("nombre",)
    list_filter = ("nivel", "periodo")
    fieldsets = (
        (None, {
            'fields': ('nombre', 'nivel', 'periodo', 'horarios', 'profesor_titular', 'profesor_asistente', 'alumnos')
        }),
    )
    inlines = [SesionClaseInline]

admin.site.register(Asistencia)
admin.site.register(Nota)
admin.site.register(PeriodoAcademico)

class RecursoCursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'clase', 'tipo', 'url', 'fecha')

admin.site.register(RecursoCurso, RecursoCursoAdmin)
