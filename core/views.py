from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from .models import (
    Usuario, Curso, Inscripcion, Clase, ContenidoEducativo,
    Evaluacion, ResultadoEvaluacion, Mensaje, ReciboPago, TicketSoporte
)
from .forms import TicketSoporteForm

# ===================================
# VISTAS ESTÁTICAS (TUS PÁGINAS HTML)
# ===================================
def index(request):
    """Página principal"""
    cursos_activos = Curso.objects.filter(Estado='activo')[:6]
    context = {
        'cursos': cursos_activos,
        'usuario': get_usuario_sesion(request)
    }
    return render(request, 'pagina_web/index.html', context)

def nosotros(request):
    return render(request, 'pagina_web/2_Nosotros.html')

def cursos(request):
    """Lista de cursos desde la base de datos agrupados por idioma"""
    cursos_list = Curso.objects.filter(Estado='activo').order_by('Nombre', 'Nivel_mcerl')
    
    # Agrupar cursos por idioma
    cursos_agrupados = {}
    for curso in cursos_list:
        # Extraer el idioma del nombre (ej: "Inglés - A1" -> "Inglés")
        if ' - ' in curso.Nombre:
            idioma = curso.Nombre.split(' - ')[0].strip()
        else:
            idioma = curso.Nombre  # Si no tiene formato "Idioma - Nivel"
        
        if idioma not in cursos_agrupados:
            cursos_agrupados[idioma] = []
        cursos_agrupados[idioma].append(curso)
    
    context = {
        'cursos_agrupados': cursos_agrupados,
        'usuario': get_usuario_sesion(request)
    }
    return render(request, 'pagina_web/3_Cursos.html', context)


def metodologia(request):
    return render(request, 'pagina_web/4_Metodologia.html')

def profesores(request):
    return render(request, 'pagina_web/5_Profesores.html')

def pantalla_inicio(request):
    return render(request, 'pagina_web/6_Pantalla_Inicio.html')

def politicas_privacidad(request):
    return render(request, 'pagina_web/11_Politicas_Privacidad.html')

def terminos(request):
    return render(request, 'pagina_web/12_Terminos.html')

def soporte(request):
    return render(request, 'pagina_web/13_Soporte.html')


# ===================================
# SISTEMA DE AUTENTICACIÓN
# ===================================
def registro(request):
    """Registro de nuevos usuarios conectado a la BD"""
    if request.method == 'POST':
        nombres = request.POST.get('nombres')
        apellidos = request.POST.get('apellidos')
        correo = request.POST.get('correo')
        contrasena = request.POST.get('contrasena')
        contrasena2 = request.POST.get('contrasena2')
        
        # Validaciones
        if not all([nombres, apellidos, correo, contrasena, contrasena2]):
            messages.error(request, 'Todos los campos son obligatorios')
            return redirect('registro')
        
        if contrasena != contrasena2:
            messages.error(request, 'Las contraseñas no coinciden')
            return redirect('registro')
        
        if len(contrasena) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return redirect('registro')
        
        if Usuario.objects.filter(Correo=correo).exists():
            messages.error(request, 'El correo ya está registrado')
            return redirect('registro')
        
        if User.objects.filter(email=correo).exists():
            messages.error(request, 'El correo ya está registrado')
            return redirect('registro')
        
        # Crear usuario
        try:
            # 1. Crear el User de Django
            user = User.objects.create_user(
                username=correo,  # Usar el email como username
                email=correo,
                password=contrasena
            )
            
            # 2. Crear el perfil Usuario vinculado al User
            usuario = Usuario.objects.create(
                user=user,  # ← Vincular con el User de Django
                Nombres=nombres,
                Apellidos=apellidos,
                Correo=correo,
                Rol='estudiante',
                Fecha_registro=timezone.now(),
                Estado='activo'
            )
            
            # Iniciar sesión automáticamente
            request.session['usuario_id'] = usuario.idUsuario
            request.session['usuario_nombre'] = f"{usuario.Nombres} {usuario.Apellidos}"
            request.session['usuario_rol'] = usuario.Rol
            request.session.modified = True
            
            messages.success(request, f'¡Bienvenido {usuario.Nombres}! Explora nuestros cursos y elige el que más te interese.')
            return redirect('dashboard_estudiante')
            
        except Exception as e:
            messages.error(request, f'Error al registrar usuario: {str(e)}')
            return redirect('registro')
    
    return render(request, 'pagina_web/7_Registro.html')

# ===================================
# LOGIN / LOGOUT
# ===================================

def login(request):
    """Inicio de sesión"""
    if request.method == 'POST':
        correo = request.POST.get('correo')
        contrasena = request.POST.get('contrasena')
        
        if not correo or not contrasena:
            messages.error(request, 'Por favor ingresa correo y contraseña')
            return redirect('login')
        
        try:
            usuario = Usuario.objects.get(Correo=correo)
            print(f"✅ Usuario encontrado: {usuario.Nombres}")
            print(f"✅ Rol: {usuario.Rol}")
            print(f"✅ User vinculado: {usuario.user}")
            
            if usuario.Estado == 'inactivo':
                messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador')
                return redirect('login')
            
            # Verificar contraseña usando el User de Django
            if usuario.user and usuario.user.check_password(contrasena):
                print(f"✅ Contraseña correcta")
                
                # Guardar datos en sesión
                request.session['usuario_id'] = usuario.idUsuario
                request.session['usuario_nombre'] = f"{usuario.Nombres} {usuario.Apellidos}"
                request.session['usuario_rol'] = usuario.Rol
                request.session.modified = True
                
                print(f"✅ Sesión guardada: usuario_id={request.session.get('usuario_id')}")
                print(f"✅ Sesión guardada: usuario_rol={request.session.get('usuario_rol')}")
                
                messages.success(request, f'¡Bienvenido {usuario.Nombres}! ¡Inicio de sesión exitosos!')
                
                # Redirigir según el rol
                if usuario.Rol == 'admin':
                    print("🔴 Redirigiendo a admin")
                    return redirect('dashboard_administrativo')
                elif usuario.Rol == 'profesor':
                    print("🟡 Redirigiendo a profesor")
                    return redirect('dashboard_profesor')
                else:
                    print("🟢 Redirigiendo a estudiante")
                    return redirect('dashboard_estudiante')
            else:
                print(f"❌ Contraseña incorrecta o usuario sin vinculación")
                messages.error(request, 'Contraseña incorrecta')
                return redirect('login')
                
        except Usuario.DoesNotExist:
            print(f"❌ Usuario no encontrado con correo: {correo}")
            messages.error(request, 'El correo no está registrado')
            return redirect('login')
    
    return render(request, 'pagina_web/6_Pantalla_Inicio.html')


def logout(request):
    """Cerrar sesión"""
    request.session.flush()
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('index')


# ===================================
# DASHBOARDS
# ===================================
def dashboard_estudiante(request):
    """Panel del estudiante con datos de la BD"""
    print(f"Dashboard estudiante - usuario_id en sesión: {request.session.get('usuario_id')}")
    print(f"Dashboard estudiante - usuario_rol en sesión: {request.session.get('usuario_rol')}")
    
    if not verificar_sesion(request, 'estudiante'):
        print("❌ Sesión inválida, redirigiendo a login")
        messages.error(request, 'Debes iniciar sesión como estudiante')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, idUsuario=usuario_id)
    
    # Obtener inscripciones activas
    inscripciones = Inscripcion.objects.filter(
        idUsuario=usuario,
        Estado='activa'
    ).select_related('idCurso')
    
    # Obtener próximas clases
    proximas_clases = []
    for inscripcion in inscripciones:
        clases = Clase.objects.filter(
            idCurso=inscripcion.idCurso,
            Fecha_hora__gte=timezone.now()
        ).order_by('Fecha_hora')[:3]
        proximas_clases.extend(clases)
    
    # Obtener resultados de evaluaciones
    resultados = ResultadoEvaluacion.objects.filter(
        idUsuario=usuario
    ).select_related('idEvaluacion')[:5]
    
    # Obtener recibos pendientes
    recibos_pendientes = ReciboPago.objects.filter(
        idUsuario=usuario,
        Estado_pago='pendiente'
    )
    
    context = {
        'usuario': usuario,
        'inscripciones': inscripciones,
        'proximas_clases': proximas_clases,
        'resultados': resultados,
        'recibos_pendientes': recibos_pendientes
    }
    return render(request, 'pagina_web/8_Dashboard_Estudiante.html', context)


def dashboard_profesor(request):
    """Panel del profesor con datos de la BD"""
    if not verificar_sesion(request, 'profesor'):
        messages.error(request, 'Debes iniciar sesión como profesor')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, idUsuario=usuario_id)
    
    # Obtener cursos donde el profesor ha subido contenido
    contenidos = ContenidoEducativo.objects.filter(
        Subido_por=usuario
    ).select_related('idCurso')
    
    # Obtener cursos únicos
    cursos_profesor = list(set([contenido.idCurso for contenido in contenidos]))
    
    # Obtener estudiantes inscritos en los cursos del profesor
    inscripciones = Inscripcion.objects.filter(
        idCurso__in=cursos_profesor,
        Estado='activa'
    ).select_related('idUsuario', 'idCurso')
    
    inscripciones_activas = inscripciones.filter(Estado='activa')
    
    # Obtener evaluaciones creadas por los cursos del profesor
    evaluaciones = Evaluacion.objects.filter(
        idCurso__in=cursos_profesor
    ).select_related('idCurso')
    
    context = {
        'usuario': usuario,
        'cursos': cursos_profesor,
        'contenidos': contenidos,
        'inscripciones': inscripciones,
        'inscripciones_activas': inscripciones_activas,
        'evaluaciones': evaluaciones,
    }
    return render(request, 'pagina_web/9_Dashboard_Profesor.html', context)


def dashboard_administrativo(request):
    """Panel administrativo con estadísticas"""
    if not verificar_sesion(request, 'admin'):
        messages.error(request, 'Debes iniciar sesión como administrador')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, idUsuario=usuario_id)
    
    # Estadísticas generales
    total_usuarios = Usuario.objects.count()
    total_cursos = Curso.objects.count()
    total_inscripciones = Inscripcion.objects.filter(Estado='activa').count()
    
    # Pagos pendientes
    pagos_pendientes = ReciboPago.objects.filter(Estado_pago='pendiente').count()
    
    # Obtener datos para mostrar en tablas
    usuarios = Usuario.objects.all().order_by('-Fecha_registro')
    cursos = Curso.objects.all()
    pagos = ReciboPago.objects.filter(Estado_pago='pendiente').select_related('idUsuario')[:10]
    tickets = TicketSoporte.objects.filter(Estado='abierto').order_by('-Fecha_creacion')[:10]
    
    context = {
        'usuario': usuario,
        'total_usuarios': total_usuarios,
        'total_cursos': total_cursos,
        'total_inscripciones': total_inscripciones,
        'pagos_pendientes': pagos_pendientes,
        'usuarios': usuarios,
        'cursos': cursos,
        'pagos': pagos,
        'tickets': tickets,
    }
    return render(request, 'pagina_web/10_Dashboard_Administrativo.html', context)


# ===================================
# FUNCIONALIDADES ADICIONALES
# ===================================
def detalle_curso(request, id_curso):
    """Detalle de un curso específico"""
    curso = get_object_or_404(Curso, idCurso=id_curso)
    
    # Obtener información adicional del curso
    clases = Clase.objects.filter(idCurso=curso).order_by('Fecha_hora')
    contenidos = ContenidoEducativo.objects.filter(idCurso=curso)
    evaluaciones = Evaluacion.objects.filter(idCurso=curso)
    
    # Verificar si el usuario está inscrito
    esta_inscrito = False
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        esta_inscrito = Inscripcion.objects.filter(
            idUsuario_id=usuario_id,
            idCurso=curso,
            Estado='activa'
        ).exists()
    
    context = {
        'curso': curso,
        'clases': clases,
        'contenidos': contenidos,
        'evaluaciones': evaluaciones,
        'esta_inscrito': esta_inscrito,
        'usuario': get_usuario_sesion(request)
    }
    return render(request, 'pagina_web/detalle_curso.html', context)

# ===================================
# FUNCIONES AUXILIARES
# ===================================
def verificar_sesion(request, rol=None):
    """Verifica si hay una sesión activa y opcionalmente el rol"""
    if not request.session.get('usuario_id'):
        print(f"❌ No hay usuario_id en sesión")
        return False
    
    if rol and request.session.get('usuario_rol') != rol:
        print(f"❌ Rol incorrecto. Esperado: {rol}, Actual: {request.session.get('usuario_rol')}")
        return False
    
    print(f"✅ Sesión válida")
    return True


def get_usuario_sesion(request):
    """Obtiene el usuario de la sesión actual"""
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        try:
            return Usuario.objects.get(idUsuario=usuario_id)
        except Usuario.DoesNotExist:
            return None
    return None

# ===================================
# SISTEMA DE TICKETS DE SOPORTE
# ===================================

def crear_ticket(request):
    """Crear un nuevo ticket de soporte"""
    if request.method == 'POST':
        form = TicketSoporteForm(request.POST)
        
        if form.is_valid():
            asunto = form.cleaned_data['Asunto']
            descripcion = form.cleaned_data['Descripcion']
            
            try:
                # Verificar si hay un usuario autenticado usando TU sistema de sesiones
                usuario_id = request.session.get('usuario_id')
                usuario_autenticado = None
                
                if usuario_id:
                    try:
                        usuario_autenticado = Usuario.objects.get(idUsuario=usuario_id)
                    except Usuario.DoesNotExist:
                        pass
                
                if usuario_autenticado:
                    # Usuario AUTENTICADO
                    ticket = TicketSoporte.objects.create(
                        idUsuario=usuario_autenticado,
                        Asunto=asunto,
                        Descripcion=descripcion,
                        Estado='abierto'
                    )
                else:
                    # Usuario NO AUTENTICADO
                    nombre = form.cleaned_data.get('nombre_usuario', '').strip()
                    email = form.cleaned_data.get('email_usuario', '').strip()
                    
                    if not nombre or not email:
                        messages.error(request, 'Por favor completa tu nombre y correo electrónico.')
                        return render(request, 'pagina_web/crear_ticket.html', {
                            'form': form,
                            'usuario': None
                        })
                    
                    ticket = TicketSoporte.objects.create(
                        idUsuario=None,
                        nombre_usuario=nombre,
                        email_usuario=email,
                        Asunto=asunto,
                        Descripcion=descripcion,
                        Estado='abierto'
                    )
                
                messages.success(request, 'Ticket creado exitosamente.')
                return redirect('soporte')
                
            except Exception as e:
                messages.error(request, f'Error al crear el ticket: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = TicketSoporteForm()
    
    # Determinar si hay usuario autenticado
    context = {
        'form': form,
        'usuario': get_usuario_sesion(request)
    }
    return render(request, 'pagina_web/crear_ticket.html', context)


def mis_tickets(request):
    """Ver mis tickets de soporte"""
    # Verificar usando tu sistema de sesiones
    if not verificar_sesion(request):
        messages.warning(request, 'Debes iniciar sesión para ver tus tickets.')
        return redirect('login')
    
    try:
        usuario_id = request.session.get('usuario_id')
        usuario = Usuario.objects.get(idUsuario=usuario_id)
        
        tickets = TicketSoporte.objects.filter(idUsuario=usuario).order_by('-Fecha_creacion')
        
        context = {
            'tickets': tickets,
            'usuario': usuario
        }
        return render(request, 'pagina_web/mis_tickets.html', context)
        
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('index')


def detalle_ticket(request, id_ticket):
    """Ver detalles de un ticket específico"""
    if not verificar_sesion(request):
        messages.warning(request, 'Debes iniciar sesión para ver los detalles del ticket.')
        return redirect('login')
    
    try:
        usuario_id = request.session.get('usuario_id')
        usuario = Usuario.objects.get(idUsuario=usuario_id)
        
        # Obtener el ticket solo si pertenece al usuario
        ticket = get_object_or_404(TicketSoporte, idTicket=id_ticket, idUsuario=usuario)
        
        context = {
            'ticket': ticket,
            'usuario': usuario
        }
        return render(request, 'pagina_web/detalle_ticket.html', context)
        
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('index')

# ===================================
# INSCRIPCION A CURSOS
# ===================================

def inscribirse_curso(request, curso_id):
    """Vista para inscribir a un usuario en un curso específico"""
    if request.method == 'POST':
        if not request.session.get('usuario_id'):
            messages.error(request, 'Debes iniciar sesión para inscribirte')
            return redirect('login')
        
        curso = get_object_or_404(Curso, idCurso=curso_id, Estado='activo')
        usuario_id = request.session.get('usuario_id')
        usuario = get_object_or_404(Usuario, idUsuario=usuario_id)
        
        # Verificar si ya está inscrito
        inscripcion_existente = Inscripcion.objects.filter(
            idUsuario=usuario,
            idCurso=curso,
            Estado='activa'
        ).exists()
        
        if inscripcion_existente:
            messages.warning(request, f'Ya estás inscrito en el curso {curso.Nombre}')
        else:
            # Crear nueva inscripción
            Inscripcion.objects.create(
                idUsuario=usuario,
                idCurso=curso,
                Estado='activa',
                Fecha_inscripcion=timezone.now()
            )
            messages.success(request, f'¡Te has inscrito exitosamente en {curso.Nombre}!')
        
        return redirect('cursos')
    
    # Si no es POST, redirigir a la lista de cursos
    return redirect('cursos')

# ===================================
# SISTEMA DE MENSAJERÍA INTERNA
# ===================================

from django.db.models import Q, Max, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Chat

def chat_list(request):
    """Lista de usuarios disponibles para chatear (excluye admins)"""
    if not verificar_sesion(request):
        messages.error(request, 'Debes iniciar sesión para acceder al chat')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario_actual = get_object_or_404(Usuario, idUsuario=usuario_id)
    
    # Obtener usuarios (estudiantes y profesores, sin admins)
    usuarios_disponibles = Usuario.objects.filter(
        Estado='activo'
    ).exclude(
        idUsuario=usuario_id
    ).exclude(
        Rol='admin'
    ).order_by('Nombres', 'Apellidos')
    
    # Obtener conversaciones con mensajes no leídos
    conversaciones = []
    for user in usuarios_disponibles:
        # Último mensaje entre ambos usuarios
        ultimo_mensaje = Chat.objects.filter(
            Q(sender=usuario_actual, receiver=user) | 
            Q(sender=user, receiver=usuario_actual)
        ).order_by('-timestamp').first()
        
        # Contar mensajes no leídos de este usuario
        unread_count = Chat.objects.filter(
            sender=user,
            receiver=usuario_actual,
            is_read=False
        ).count()
        
        conversaciones.append({
            'usuario': user,
            'ultimo_mensaje': ultimo_mensaje,
            'unread_count': unread_count
        })
    
    # Ordenar por último mensaje más reciente
    conversaciones.sort(
        key=lambda x: x['ultimo_mensaje'].timestamp if x['ultimo_mensaje'] else timezone.now(),
        reverse=True
    )
    
    context = {
        'usuario': usuario_actual,
        'conversaciones': conversaciones
    }
    return render(request, 'chat/chat_list.html', context)


def chat_room(request, user_id):
    """Sala de chat con un usuario específico"""
    if not verificar_sesion(request):
        messages.error(request, 'Debes iniciar sesión para acceder al chat')
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    usuario_actual = get_object_or_404(Usuario, idUsuario=usuario_id)
    otro_usuario = get_object_or_404(Usuario, idUsuario=user_id)
    
    # Verificar que el otro usuario no sea admin
    if otro_usuario.Rol == 'admin':
        messages.error(request, 'No puedes chatear con administradores')
        return redirect('chat_list')
    
    # Marcar mensajes como leídos
    Chat.objects.filter(
        sender=otro_usuario,
        receiver=usuario_actual,
        is_read=False
    ).update(is_read=True)
    
    # Obtener historial de mensajes
    mensajes = Chat.objects.filter(
        Q(sender=usuario_actual, receiver=otro_usuario) | 
        Q(sender=otro_usuario, receiver=usuario_actual)
    ).order_by('timestamp')
    
    context = {
        'usuario': usuario_actual,
        'otro_usuario': otro_usuario,
        'mensajes': mensajes
    }
    return render(request, 'chat/chat_room.html', context)


def send_message(request):
    """Enviar mensaje vía AJAX"""
    if request.method == 'POST' and verificar_sesion(request):
        usuario_id = request.session.get('usuario_id')
        usuario_actual = get_object_or_404(Usuario, idUsuario=usuario_id)
        
        receiver_id = request.POST.get('receiver_id')
        message_text = request.POST.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'success': False, 'error': 'Mensaje vacío'})
        
        receiver = get_object_or_404(Usuario, idUsuario=receiver_id)
        
        # Verificar que no sea admin
        if receiver.Rol == 'admin':
            return JsonResponse({'success': False, 'error': 'No puedes enviar mensajes a administradores'})
        
        # Crear mensaje
        mensaje = Chat.objects.create(
            sender=usuario_actual,
            receiver=receiver,
            message=message_text
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': mensaje.id,
                'text': mensaje.message,
                'timestamp': mensaje.timestamp.strftime('%H:%M'),
                'sender_name': f"{usuario_actual.Nombres} {usuario_actual.Apellidos}"
            }
        })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def get_messages(request, user_id):
    """Obtener mensajes nuevos vía AJAX"""
    if verificar_sesion(request):
        usuario_id = request.session.get('usuario_id')
        usuario_actual = get_object_or_404(Usuario, idUsuario=usuario_id)
        otro_usuario = get_object_or_404(Usuario, idUsuario=user_id)
        
        last_message_id = request.GET.get('last_id', 0)
        
        # Obtener mensajes nuevos
        nuevos_mensajes = Chat.objects.filter(
            Q(sender=usuario_actual, receiver=otro_usuario) | 
            Q(sender=otro_usuario, receiver=usuario_actual),
            id__gt=last_message_id
        ).order_by('timestamp')
        
        # Marcar como leídos los mensajes recibidos
        Chat.objects.filter(
            sender=otro_usuario,
            receiver=usuario_actual,
            is_read=False
        ).update(is_read=True)
        
        mensajes_data = []
        for msg in nuevos_mensajes:
            mensajes_data.append({
                'id': msg.id,
                'text': msg.message,
                'timestamp': msg.timestamp.strftime('%H:%M'),
                'is_mine': msg.sender.idUsuario == usuario_actual.idUsuario,
                'sender_name': f"{msg.sender.Nombres} {msg.sender.Apellidos}"
            })
        
        return JsonResponse({
            'success': True,
            'messages': mensajes_data
        })
    
    return JsonResponse({'success': False, 'error': 'No autorizado'})