from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usuario_actual(request):
    return Response({
        "usuario": request.user.username,
        "rol": request.user.rol,
    })
