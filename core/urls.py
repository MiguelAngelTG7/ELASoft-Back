from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    usuario_actual,
    obtener_asistencia,
    guardar_asistencia,
    notas_por_clase,
    dashboard_alumno,
    dashboard_director,
    crear_alumno,
    alumnos_del_profesor,
    alumnos_para_director,
    listar_clases,
    buscar_alumnos,
    asignar_alumno_a_clase,
    listar_clases_profesor,
    remover_alumno_de_clase,
    reporte_asistencia_clase,
    lista_profesores_director,
    listar_periodos,
    director_crear_alumno,
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Autenticación
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Usuario actual
    path('usuario/', usuario_actual, name='usuario_actual'),

    # Asistencia
    path('clases/<int:clase_id>/asistencia/', obtener_asistencia, name='obtener_asistencia'),
    path('clases/<int:clase_id>/asistencia/guardar/', guardar_asistencia, name='guardar_asistencia'),

    # Notas
    path('clases/<int:clase_id>/notas/', notas_por_clase, name='notas-por-clase'),

    # Dashboard del alumno
    path('alumno/dashboard/', dashboard_alumno, name='dashboard-alumno'),

    # Dashboard del director
    path('director/dashboard/', dashboard_director, name='dashboard-director'),
    path('director/crear-alumno/', director_crear_alumno, name='director_crear_alumno'),
    path('director/alumnos/', alumnos_para_director, name='alumnos-para-director'),
    path('director/clases/', listar_clases, name='listar_clases'),
    path('director/profesores/', lista_profesores_director),
    path('director/periodos/', listar_periodos, name='listar_periodos'),

    # path('profesor/registrar-alumno/', RegistrarAlumnoAPIView.as_view(), name='registrar-alumno'),
    path('profesor/crear-alumno/', crear_alumno, name='crear_alumno'),

    # Gestión de alumnos existentes
    path('alumnos/buscar/', buscar_alumnos, name='buscar_alumnos'),
    path('profesor/clases/<int:clase_id>/asignar-alumno/', asignar_alumno_a_clase, name='asignar_alumno'),
    path('profesor/clases/<int:clase_id>/remover-alumno/', remover_alumno_de_clase, name='remover_alumno'),

    # Alumnos por clase (profesor y director)
    path('profesor/alumnos/', alumnos_del_profesor, name='alumnos-del-profesor'),
    path('profesor/clases/', listar_clases_profesor, name='listar_clases_profesor'),
    path('clases/<int:clase_id>/reporte-asistencia/', reporte_asistencia_clase, name='reporte_asistencia_clase'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or 'static')