from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from .models import Clase, Asistencia, Nota, Usuario, Horario, Nivel, PeriodoAcademico
from .serializers import ClaseProfesorSerializer, NotaSerializer, AlumnoRegistroSerializer, AlumnoDetalleSerializer, ProfesorListaSerializer
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
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
        "id": request.user.id,
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
            "alumno_nombre": alumno.get_full_name() or alumno.username,  # <--- Nombre completo o username si está vacío
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
                "participacion": nota.participacion if nota else 0,
                "tareas": nota.tareas if nota else 0,
                "examen_final": nota.examen_final if nota else 0,
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
        notas_data = request.data.get("notas") or request.data

        if not isinstance(notas_data, list) or not notas_data:
            return Response({"error": "No se recibieron datos de notas."}, status=status.HTTP_400_BAD_REQUEST)

        errores = []

        for nota_data in notas_data:
            try:
                alumno_id = nota_data["alumno_id"]

                participacion = float(nota_data.get("participacion") or 0)
                tareas = float(nota_data.get("tareas") or 0)
                examen_final = float(nota_data.get("examen_final") or 0)

                Nota.objects.update_or_create(
                    clase_id=clase_id,
                    alumno_id=alumno_id,
                    defaults={
                        "participacion": participacion,
                        "tareas": tareas,
                        "examen_final": examen_final,
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
    periodo_id = request.query_params.get('periodo_id')

    # Filtrar por periodo si se proporciona, de lo contrario por periodos activos
    if periodo_id:
        clases = Clase.objects.filter(periodo_id=periodo_id).distinct()
    else:
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

        # Construir objeto para profesor titular
        if clase.profesor_titular:
            titular_data = {
                'id': clase.profesor_titular.id,
                'nombre_completo': clase.profesor_titular.get_full_name()
            }
        else:
            titular_data = None

        # Construir objeto para profesor asistente
        if clase.profesor_asistente:
            asistente_data = {
                'id': clase.profesor_asistente.id,
                'nombre_completo': clase.profesor_asistente.get_full_name()
            }
        else:
            asistente_data = None

        data.append({
            "curso": clase.nombre,
            "nivel": clase.nivel.nombre if clase.nivel else "—",
            "horarios": [str(h) for h in clase.horarios.all()],
            "periodo": clase.periodo.nombre if clase.periodo else "—",
            "maestro_titular": titular_data,     # ahora es un objeto o null
            "maestro_asistente": asistente_data, # ahora es un objeto o null
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

        clase.alumnos.add(alumno)

        # Crear registro de notas si no existe
        nota_existente = Nota.objects.filter(clase=clase, alumno=alumno).exists()
        if not nota_existente:
            Nota.objects.create(
                clase=clase,
                alumno=alumno,
                participacion=0,
                tareas=0,
                examen_final=0,
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

# Listar todos los profesores (sin detalles de clases)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_profesores(request):
    profesores = Usuario.objects.filter(rol='profesor')
    data = [{"id": p.id, "full_name": p.get_full_name() or p.username} for p in profesores]
    return Response(data)

# Listar todos los horarios (sin detalles de clases)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_horarios(request):
    horarios = Horario.objects.all()
    data = [{"id": h.id, "dia": h.dia} for h in horarios]
    return Response(data)

# Listar todos los niveles (sin detalles de clases)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_niveles(request):
    niveles = Nivel.objects.all()
    data = [{"id": n.id, "nombre": n.nombre} for n in niveles]
    return Response(data)

# Listar todas las clases (con detalles de horarios, nivel y periodo)

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

# Listar clases de un profesor (tanto titular como asistente)

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

# Reporte de asistencia de una clase

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

# Lista de profesores para el director

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_profesores_director(request):
    if request.user.rol != 'director':
       return Response({"profesores": []}, status=403)
    periodo_id = request.query_params.get('periodo_id')
    if not periodo_id:
        return Response({"profesores": []}, status=200)
    profesores_ids_titular = list(Clase.objects.filter(periodo_id=periodo_id).values_list('profesor_titular', flat=True))
    profesores_ids_asistente = list(Clase.objects.filter(periodo_id=periodo_id).values_list('profesor_asistente', flat=True))
    profesores_ids = profesores_ids_titular + profesores_ids_asistente
    profesores = Usuario.objects.filter(id__in=profesores_ids, rol='profesor').distinct()
    serializer = ProfesorListaSerializer(profesores, many=True)
    return Response({"profesores": serializer.data})

# Perido académico: listar todos los periodos

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_periodos(request):
    periodos = PeriodoAcademico.objects.all().order_by('-id')
    data = [{"id": p.id, "nombre": p.nombre} for p in periodos]
    return Response({"periodos": data})

# ----------------------------
# Nueva Vista: Crear Alumno (solo Director)
# ----------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def director_crear_alumno(request):
    # Solo permitir si el usuario es director
    if request.user.rol != 'director':
        return Response({'detail': 'No autorizado'}, status=403)
    serializer = AlumnoRegistroSerializer(data=request.data)
    if serializer.is_valid():
        alumno = serializer.save()
        return Response({'detail': 'Alumno creado', 'id': alumno.id})
    return Response(serializer.errors, status=400)