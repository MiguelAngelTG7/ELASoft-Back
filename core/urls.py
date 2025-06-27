from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import usuario_actual, ClasesDelProfesorView  # 👈 importa también la nueva vista

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('usuario/', usuario_actual),  # Vista actual de usuario
    path('clases/profesor/', ClasesDelProfesorView.as_view(), name='clases-del-profesor'),  
]

