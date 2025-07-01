from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from .models import Clase, Asistencia, Nota, Usuario, Horario, Nivel
from .serializers import ClaseProfesorSerializer, AsistenciaSerializer, NotaSerializer, AlumnoRegistroSerializer, UsuarioSerializer, AlumnoDetalleSerializer
from django.utils import timezone
from django.db.models import Q


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
# Utilidad: obtener clases de un profesor
# ----------------------------
def get_clases_profesor(usuario):
    return Clase.objects.filter(
        profesor_titular=usuario
    ) | Clase.objects.filter(
        profesor_asistente=usuario
    )


# ----------------------------
# Vista 3: Obtener asistencia por clase y fecha
# ----------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_asistencia(request, clase_id):
    """
    Devuelve la asistencia de todos los alumnos de la clase para todas las fechas programadas (sesiones).
    """
    try:
        clase = Clase.objects.get(id=clase_id)
    except Clase.DoesNotExist:
        return Response({"error": "Clase no encontrada"}, status=404)

    # Obtener todas las fechas programadas (sesiones)
    sesiones = clase.sesiones.order_by('fecha')
    fechas = [s.fecha for s in sesiones]
    alumnos = clase.alumnos.all()

    # Para cada alumno y cada fecha, obtener o crear la asistencia
    data = []
    for alumno in alumnos:
        fila = {
            "alumno_id": alumno.id,
            "alumno_nombre": alumno.username,
            "asistencias": []
        }
        for fecha in fechas:
            asistencia, _ = Asistencia.objects.get_or_create(
                clase=clase,
                alumno=alumno,
                fecha=fecha,
                defaults={"presente": False}
            )
            fila["asistencias"].append({
                "fecha": str(fecha),
                "presente": asistencia.presente
            })
        data.append(fila)

    return Response({
        "fechas": [str(f) for f in fechas],
        "alumnos": data
    })



# ----------------------------
# Vista 4: Guardar asistencia
# ----------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guardar_asistencia(request, clase_id):
    """
    Guarda la asistencia de todos los alumnos para todas las fechas programadas de la clase.
    Espera un JSON con: { asistencias: [ { alumno_id, asistencias: [ { fecha, presente } ] } ] }
    """
    asistencias = request.data.get("asistencias", [])

    try:
        clase = Clase.objects.get(id=clase_id)
    except Clase.DoesNotExist:
        return Response({"error": "Clase no encontrada"}, status=404)

    for alumno_asist in asistencias:
        alumno_id = alumno_asist.get("alumno_id")
        for asistencia in alumno_asist.get("asistencias", []):
            fecha = asistencia.get("fecha")
            presente = asistencia.get("presente", False)
            Asistencia.objects.update_or_create(
                clase=clase,
                alumno_id=alumno_id,
                fecha=fecha,
                defaults={"presente": presente}
            )

    return Response({"mensaje": "Asistencia guardada correctamente"})


# ----------------------------
# Vista 5: Obtener y registrar notas por clase
# ----------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notas_por_clase(request, clase_id):
    
    if request.method == 'GET':
        try:
            clase = Clase.objects.get(id=clase_id)
        except Clase.DoesNotExist:
            return Response({"error": "Clase no encontrada"}, status=404)

        alumnos = clase.alumnos.all()
        resultados = []

        for alumno in alumnos:
            nota = Nota.objects.filter(clase=clase, alumno=alumno).first()
            resultado = {
                "alumno_id": alumno.id,
                "alumno_nombre": f"{alumno.first_name} {alumno.last_name}",
                "nota1": nota.nota1 if nota else 0,
                "nota2": nota.nota2 if nota else 0,
                "nota3": nota.nota3 if nota else 0,
                "nota4": nota.nota4 if nota else 0,
                "promedio": nota.promedio if nota else 0,
                "asistencia_pct": nota.calcular_asistencia() if nota else 0,
                "estado": nota.estado_aprobacion() if nota else "Sin notas",
                "curso_nombre": clase.nombre,
                "nivel_nombre": clase.nivel.nombre,
                "horarios": [str(h) for h in clase.horarios.all()],
            }
            resultados.append(resultado)

        return Response(resultados)

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
    notas = Nota.objects.filter(alumno=alumno).order_by('clase__nombre')
    serializer = NotaSerializer(notas, many=True)
    return Response({
        "alumno_nombre": alumno.get_full_name() or alumno.username,
        "clases": serializer.data
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
            "curso": clase.nombre,
            "nivel": clase.nivel.nombre,
            "horarios": [str(h) for h in clase.horarios.all()],  
            "periodo": clase.periodo.nombre,
            "total_alumnos": total_alumnos,
            "alumnos_con_notas": notas.count(),
            "aprobados": aprobados,
            "porcentaje_aprobados": round((aprobados / total_alumnos * 100), 2) if total_alumnos else 0,
            "asistencia_promedio": round(asistencia_prom, 2)
        })
    return Response({"dashboard": data})

# ----------------------------
# Vista 8: Profesor Registra Nuevo Alumno
# ----------------------------

class RegistrarAlumnoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Solo profesores pueden registrar alumnos
        if request.user.rol != 'profesor':
            return Response({'error': 'Solo profesores pueden registrar alumnos'}, status=403)

        serializer = AlumnoRegistroSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'mensaje': 'Alumno registrado correctamente'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ----------------------------
# Vista 9: Buscar Alumno Existente
# ----------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_alumnos(request):
    query = request.GET.get('q', '')
    clase_id = request.GET.get('clase_id')  # 🆕 importante

    if not query:
        return Response([], status=200)

    alumnos = Usuario.objects.filter(
        Q(rol='alumno'),
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    )

    resultado = []
    for alumno in alumnos:
        asignado = False
        if clase_id:
            try:
                clase = Clase.objects.get(id=clase_id)
                asignado = clase.alumnos.filter(id=alumno.id).exists()
            except Clase.DoesNotExist:
                pass

        resultado.append({
            "id": alumno.id,
            "username": alumno.username,
            "first_name": alumno.first_name,
            "last_name": alumno.last_name,
            "email": alumno.email,
            "asignado": asignado,
        })

    return Response(resultado)
# ----------------------------
# Vista 10: Profesor Asigna Alumno Existente
# ----------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asignar_alumno_a_clase(request, clase_id):
    alumno_id = request.data.get('alumno_id')

    if not alumno_id:
        return Response({"error": "Falta el ID del alumno"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        clase = Clase.objects.get(pk=clase_id)
        alumno = Usuario.objects.get(pk=alumno_id, rol='alumno')

        if alumno in clase.alumnos.all():
            return Response({"message": "El alumno ya está asignado a esta clase."}, status=status.HTTP_200_OK)

        # ✅ Asignar alumno a clase
        clase.alumnos.add(alumno)

        # ✅ Crear registro de notas si no existe
        nota_existente = Nota.objects.filter(clase=clase, alumno=alumno).exists()
        if not nota_existente:
            Nota.objects.create(
                clase=clase,
                alumno=alumno,
                nota1=0,
                nota2=0,
                nota3=0,
                nota4=0,
            )

        return Response({"message": "Alumno asignado correctamente."}, status=status.HTTP_200_OK)

    except Clase.DoesNotExist:
        return Response({"error": "Clase no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    except Usuario.DoesNotExist:
        return Response({"error": "Alumno no encontrado."}, status=status.HTTP_404_NOT_FOUND)

# ----------------------------
# Vista 11: Profesor Remueve Alumno de Clase
# ----------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remover_alumno_de_clase(request, clase_id):
    alumno_id = request.data.get('alumno_id')

    if not alumno_id:
        return Response({"error": "Falta el ID del alumno"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        clase = Clase.objects.get(pk=clase_id)
        alumno = Usuario.objects.get(pk=alumno_id, rol='alumno')

        if alumno not in clase.alumnos.all():
            return Response({"message": "El alumno no está asignado a esta clase."}, status=status.HTTP_400_BAD_REQUEST)

        # ❌ Remover al alumno
        clase.alumnos.remove(alumno)

        # ❌ (Opcional) Eliminar sus notas de esa clase
        Nota.objects.filter(clase=clase, alumno=alumno).delete()

        return Response({"message": "Alumno removido correctamente de la clase."}, status=status.HTTP_200_OK)

    except Clase.DoesNotExist:
        return Response({"error": "Clase no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    except Usuario.DoesNotExist:
        return Response({"error": "Alumno no encontrado."}, status=status.HTTP_404_NOT_FOUND)

# ----------------------------
# Vista 12: Profesor Crea Alumno de Clase
# ----------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_alumno(request):
    if request.user.rol != 'profesor':
        return Response({'error': 'Solo los profesores pueden crear alumnos.'}, status=403)

    serializer = AlumnoRegistroSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'mensaje': 'Alumno creado exitosamente.'}, status=201)

    return Response(serializer.errors, status=400)

# ----------------------------
# Vista 13: Lista de Alumnos para Profesor
# ----------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alumnos_del_profesor(request):
    usuario = request.user
    clase_id = request.query_params.get('clase_id')  # filtro opcional

    # Buscar clases del profesor
    clases = get_clases_profesor(usuario).distinct()

    # Filtrar alumnos de esas clases
    alumnos = Usuario.objects.filter(rol='alumno', clase__in=clases).distinct()

    clase_info = {}
    if clase_id:
        alumnos = alumnos.filter(clase__id=clase_id)
        try:
            clase = Clase.objects.get(id=clase_id)
            clase_info = {
                "clase_nombre": clase.nombre,
                "nivel": clase.nivel.nombre,
                "horarios": [str(h) for h in clase.horarios.all()],
            }
        except Clase.DoesNotExist:
            clase_info = {
                "error": "Clase no encontrada",
            }

    serializer = AlumnoDetalleSerializer(alumnos, many=True)

    return Response({
        "clase": clase_info,
        "alumnos": serializer.data
    })

# ----------------------------
# Vista 14: Lista de Alumnos para Director
# ----------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alumnos_para_director(request):
    if request.user.rol != 'director':
        return Response({"error": "No autorizado"}, status=403)

    clase_id = request.query_params.get('clase_id')
    horario_id = request.query_params.get('horario_id')
    profesor_id = request.query_params.get('profesor_id')
    nivel_id = request.query_params.get('nivel_id')

    clases = Clase.objects.all()

    if clase_id:
        clases = clases.filter(id=clase_id)
    if horario_id:
        clases = clases.filter(horarios__id=horario_id)
    if profesor_id:
        clases = clases.filter(
            Q(profesores__profesor_titular__id=profesor_id) |
            Q(profesores__profesor_asistente__id=profesor_id)
        )
    if nivel_id:
        clases = clases.filter(nivel__id=nivel_id)

    clases = clases.distinct()
    alumnos = Usuario.objects.filter(rol='alumno', clase__in=clases).distinct()

    serializer = AlumnoDetalleSerializer(alumnos, many=True)

    return Response({
        "alumnos": serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_profesores(request):
    profesores = Usuario.objects.filter(rol='profesor')
    data = [{"id": p.id, "full_name": p.get_full_name() or p.username} for p in profesores]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_horarios(request):
    horarios = Horario.objects.all()
    data = [{"id": h.id, "dia": h.dia} for h in horarios]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_niveles(request):
    niveles = Nivel.objects.all()
    data = [{"id": n.id, "nombre": n.nombre} for n in niveles]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_clases(request):
    clases = Clase.objects.prefetch_related('horarios', 'nivel', 'periodo').all()
    data = []
    for c in clases:
        data.append({
            "id": c.id,
            "nombre": c.nombre,
            "nivel": c.nivel.nombre if c.nivel else '',
            "periodo_nombre": c.periodo.nombre if c.periodo else 'Sin periodo',
            "horarios": [str(h) for h in c.horarios.all()]
         })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_clases_profesor(request):
    usuario = request.user
    clases = Clase.objects.filter(
        profesor_titular=usuario
    ) | Clase.objects.filter(
        profesor_asistente=usuario
    )
    clases = clases.distinct()
    serializer = ClaseProfesorSerializer(clases, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_asistencia_clase(request, clase_id):
    """
    Devuelve el reporte de asistencia de todos los alumnos de una clase:
    nombre, total sesiones, presentes, ausentes, fechas, porcentaje, total y total de totales
    """
    try:
        clase = Clase.objects.get(id=clase_id)
    except Clase.DoesNotExist:
        return Response({"error": "Clase no encontrada"}, status=404)

    total_sesiones = clase.total_sesiones
    # Usar fechas de SesionClase si existen, si no, usar fechas de asistencia
    sesiones = clase.sesiones.order_by('fecha')
    if sesiones.exists():
        fechas = [str(s.fecha) for s in sesiones]
    else:
        fechas = sorted(list(Asistencia.objects.filter(clase=clase).values_list('fecha', flat=True).distinct()))
    # Limitar a total_sesiones
    fechas = fechas[:total_sesiones]
    alumnos = clase.alumnos.all()
    reporte = []
    total_presentes = 0
    total_ausentes = 0

    for alumno in alumnos:
        asistencias = Asistencia.objects.filter(clase=clase, alumno=alumno, fecha__in=fechas)
        presentes = asistencias.filter(presente=True).count()
        ausentes = asistencias.filter(presente=False).count()
        porcentaje = round((presentes / total_sesiones) * 100, 2) if total_sesiones else 0
        total_presentes += presentes
        total_ausentes += ausentes
        # Crear lista de asistencias por fecha (en el mismo orden que fechas)
        asistencias_por_fecha = []
        for fecha in fechas:
            a = asistencias.filter(fecha=fecha).first()
            asistencias_por_fecha.append({
                "fecha": str(fecha),
                "presente": a.presente if a else False
            })
        reporte.append({
            "alumno_id": alumno.id,
            "nombre": f"{alumno.first_name} {alumno.last_name}",
            "total_sesiones": total_sesiones,
            "presentes": presentes,
            "ausentes": ausentes,
            "fechas": fechas,
            "porcentaje": porcentaje,
            "asistencias": asistencias_por_fecha
        })

    return Response({
        "clase": clase.nombre,
        "total_sesiones": total_sesiones,
        "fechas": fechas,
        "reporte": reporte,
        "total_presentes": total_presentes,
        "total_ausentes": total_ausentes,
        "total_alumnos": alumnos.count(),
    })
