from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, permissions
from .models import Clase, Asistencia
from .serializers import ClaseProfesorSerializer, AsistenciaSerializer
from django.utils import timezone


# ----------------------------
# Vista 1: Usuario actual
# ----------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def usuario_actual(request):
    return Response({
        "usuario": request.user.username,
        "rol": request.user.rol,
    })


# ----------------------------
# Vista 2: Clases del Profesor
# ----------------------------
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


# ----------------------------
# Vista 3: Obtener asistencia por clase y fecha
# ----------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_asistencia(request, clase_id):
    fecha = request.query_params.get('fecha', timezone.now().date())

    # Buscar registros de asistencia existentes
    asistencias = Asistencia.objects.filter(clase_id=clase_id, fecha=fecha)

    if not asistencias.exists():
        try:
            clase = Clase.objects.get(id=clase_id)
            for alumno in clase.alumnos.all():
                Asistencia.objects.create(
                    clase=clase,
                    alumno=alumno,
                    fecha=fecha,
                    presente=False  # por defecto
                )
            asistencias = Asistencia.objects.filter(clase=clase, fecha=fecha)
        except Clase.DoesNotExist:
            return Response({"error": "Clase no encontrada"}, status=404)

    data = [
        {
            "alumno_id": a.alumno.id,
            "alumno_nombre": a.alumno.username,
            "presente": a.presente,
        }
        for a in asistencias
    ]
    return Response(data)


# ----------------------------
# Vista 4: Guardar asistencia (masiva)
# ----------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guardar_asistencia(request, clase_id):
    fecha = request.data.get("fecha")
    asistencias = request.data.get("asistencias", [])

    if not fecha or not asistencias:
        return Response({"error": "Datos incompletos"}, status=400)

    for a in asistencias:
        Asistencia.objects.update_or_create(
            clase_id=clase_id,
            alumno_id=a["alumno_id"],
            fecha=fecha,
            defaults={"presente": a["presente"]}
        )

    return Response({"mensaje": "Asistencia guardada correctamente"})
