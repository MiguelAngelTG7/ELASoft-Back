from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    usuario_actual,
    ClasesDelProfesorView,
    obtener_asistencia,
    guardar_asistencia,
    notas_por_clase,
    dashboard_alumno,
    dashboard_director,
    RegistrarAlumnoAPIView,
    crear_alumno,
    alumnos_del_profesor,
)
from . import views
from core.views import remover_alumno_de_clase

urlpatterns = [
    # Autenticación
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Usuario
    path('usuario/', usuario_actual, name='usuario_actual'),

    # Clases del profesor
    path('clases/profesor/', ClasesDelProfesorView.as_view(), name='clases-del-profesor'),

    # Asistencia
    path('clases/<int:clase_id>/asistencia/', obtener_asistencia, name='obtener_asistencia'),
    path('clases/<int:clase_id>/asistencia/guardar/', guardar_asistencia, name='guardar_asistencia'),

    # Notas
    path('clases/<int:clase_id>/notas/', notas_por_clase, name='notas-por-clase'),

    # Notas Asistencia para Alumno
    path('alumno/dashboard/', dashboard_alumno, name='dashboard-alumno'),

    # Dashboard Director Académico
    path('director/dashboard/', dashboard_director, name='dashboard-director'),

    # Profesor Registra Nuevo Alumno
    path('profesor/registrar-alumno/', RegistrarAlumnoAPIView.as_view(), name='registrar-alumno'),

    # Busqueda de Alumnos Existentes
    path('alumnos/buscar/', views.buscar_alumnos, name='buscar_alumnos'),

    # Asigna Alumnos Existentes
    path('profesor/clases/<int:clase_id>/asignar-alumno/', views.asignar_alumno_a_clase, name='asignar_alumno'),

    # Remueve Alumno de Clase
    path('profesor/clases/<int:clase_id>/remover-alumno/', remover_alumno_de_clase, name='remover_alumno'),

    #Clases existentes del Profesor
    path('profesor/clases/', views.ClasesDelProfesorView.as_view(), name='clases_del_profesor'),

    #Crear Alumno
    path('profesor/crear-alumno/', crear_alumno, name='crear_alumno'),

    #Lista de Alumnos del Profesor
    path('profesor/alumnos/', alumnos_del_profesor, name='alumnos-del-profesor'),



]
