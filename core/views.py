from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.views import APIView
from .models import Clase
from .serializers import ClaseProfesorSerializer

# Vista 1: Información del usuario autenticado
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usuario_actual(request):
    return Response({
        "usuario": request.user.username,
        "rol": request.user.rol,
    })


# Vista 2: Clases asignadas al profesor (titular o asistente)
class ClasesDelProfesorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        clases = Clase.objects.filter(
            profesores__profesor_titular=usuario
        ) | Clase.objects.filter(
            profesores__profesor_asistente=usuario
        )

        clases = clases.distinct()
        serializer = ClaseProfesorSerializer(clases, many=True)
        return Response(serializer.data)
