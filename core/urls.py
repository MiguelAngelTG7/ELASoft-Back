from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import usuario_actual, ClasesDelProfesorView, obtener_asistencia, guardar_asistencia

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('usuario/', usuario_actual),  # Vista actual de usuario
    path('clases/profesor/', ClasesDelProfesorView.as_view(), name='clases-del-profesor'),  
    path('clases/<int:clase_id>/asistencia/', obtener_asistencia),
    path('clases/<int:clase_id>/asistencia/guardar/', guardar_asistencia)
]

