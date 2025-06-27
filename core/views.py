from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from .models import Clase, Asistencia, Nota
from .serializers import ClaseProfesorSerializer, AsistenciaSerializer, NotaSerializer
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

    asistencias = Asistencia.objects.filter(clase_id=clase_id, fecha=fecha)

    if not asistencias.exists():
        try:
            clase = Clase.objects.get(id=clase_id)
            for alumno in clase.alumnos.all():
                Asistencia.objects.create(
                    clase=clase,
                    alumno=alumno,
                    fecha=fecha,
                    presente=False
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
# Vista 4: Guardar asistencia
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


# ----------------------------
# Vista 5: Obtener y registrar notas por clase
# ----------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notas_por_clase(request, clase_id):
    if request.method == 'GET':
        notas = Nota.objects.filter(clase_id=clase_id)

        # Crear notas vacías si no existen
        if not notas.exists():
            try:
                clase = Clase.objects.get(id=clase_id)
                for alumno in clase.alumnos.all():
                    Nota.objects.create(
                        clase=clase,
                        alumno=alumno,
                        nota1=0,
                        nota2=0,
                        nota3=0,
                        nota4=0
                    )
                notas = Nota.objects.filter(clase=clase)
            except Clase.DoesNotExist:
                return Response({"error": "Clase no encontrada"}, status=404)

        serializer = NotaSerializer(notas, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Permitir que venga como {"notas": [...] } o como lista directa
        notas_data = request.data.get("notas") or request.data

        if not isinstance(notas_data, list) or not notas_data:
            return Response({"error": "No se recibieron datos de notas."}, status=status.HTTP_400_BAD_REQUEST)

        errores = []

        for nota_data in notas_data:
            try:
                alumno_id = nota_data["alumno_id"]

                nota1 = float(nota_data.get("nota1") or 0)
                nota2 = float(nota_data.get("nota2") or 0)
                nota3 = float(nota_data.get("nota3") or 0)
                nota4 = float(nota_data.get("nota4") or 0)

                Nota.objects.update_or_create(
                    clase_id=clase_id,
                    alumno_id=alumno_id,
                    defaults={
                        "nota1": nota1,
                        "nota2": nota2,
                        "nota3": nota3,
                        "nota4": nota4,
                    }
                )
            except Exception as e:
                errores.append({
                    "alumno_id": nota_data.get("alumno_id"),
                    "error": str(e)
                })

        if errores:
            return Response({
                "mensaje": "Algunas notas no se pudieron guardar.",
                "errores": errores
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({"mensaje": "Notas registradas correctamente."})
    
# ----------------------------
# Vista 6: Obtener notas y asistencia del Alumno
# ----------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_alumno(request):
    alumno = request.user
    notas = Nota.objects.filter(alumno=alumno).order_by('clase__curso__nombre')
    serializer = NotaSerializer(notas, many=True)
    return Response({
        "alumno_nombre": alumno.get_full_name() or alumno.username,
        "cursos": serializer.data
    })

# ----------------------------
# Vista 7: Obtener datos para Director Academico
# ----------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_director(request):
    director = request.user
    # Traemos todos los cursos activos en clases actuales
    clases = Clase.objects.filter(periodo__activo=True).distinct()
    data = []
    for clase in clases:
        notas = Nota.objects.filter(clase=clase)
        total_alumnos = clase.alumnos.count()
        aprobados = sum(1 for n in notas if n.estado_aprobacion() == "Aprobado")
        asistencia_prom = (
            sum(n.calcular_asistencia() for n in notas) / notas.count()
            if notas.exists() else 0
        )
        data.append({
            "curso": clase.curso.nombre,
            "nivel": clase.curso.nivel.nombre,
            "horarios": [str(h) for h in clase.horarios.all()],  
            "periodo": clase.periodo.nombre,
            "total_alumnos": total_alumnos,
            "alumnos_con_notas": notas.count(),
            "aprobados": aprobados,
            "porcentaje_aprobados": round((aprobados / total_alumnos * 100), 2) if total_alumnos else 0,
            "asistencia_promedio": round(asistencia_prom, 2)
        })
    return Response({"dashboard": data})
