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
)

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


]
