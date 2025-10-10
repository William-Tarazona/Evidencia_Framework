from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
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
        
        # Crear usuario
        try:
            usuario = Usuario.objects.create(
                Nombres=nombres,
                Apellidos=apellidos,
                Correo=correo,
                Contrasena=make_password(contrasena),
                Rol='estudiante',
                Fecha_registro=timezone.now(),
                Estado='activo'
            )
            
            # Iniciar sesión automáticamente
            request.session['usuario_id'] = usuario.idUsuario
            request.session['usuario_nombre'] = f"{usuario.Nombres} {usuario.Apellidos}"
            request.session['usuario_rol'] = usuario.Rol
            
            messages.success(request, f'¡Bienvenido {usuario.Nombres}! Explora nuestros cursos y elige el que más te interese.')
            return redirect('cursos')  # Redirige a la página de cursos
            
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
            
            if usuario.Estado == 'inactivo':
                messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador')
                return redirect('login')
            
            if check_password(contrasena, usuario.Contrasena):
                # Guardar datos en sesión
                request.session['usuario_id'] = usuario.idUsuario
                request.session['usuario_nombre'] = f"{usuario.Nombres} {usuario.Apellidos}"
                request.session['usuario_rol'] = usuario.Rol
                
                messages.success(request, f'¡Bienvenido {usuario.Nombres}!')
                
                # Redirigir según el rol
                if usuario.Rol == 'admin':
                    return redirect('dashboard_administrativo')
                elif usuario.Rol == 'profesor':
                    return redirect('dashboard_profesor')
                else:
                    return redirect('dashboard_estudiante')
            else:
                messages.error(request, 'Contraseña incorrecta')
                return redirect('login')
                
        except Usuario.DoesNotExist:
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
    if not verificar_sesion(request, 'estudiante'):
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
    
    cursos_profesor = set([contenido.idCurso for contenido in contenidos])
    
    context = {
        'usuario': usuario,
        'cursos': cursos_profesor,
        'contenidos': contenidos
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
    
    context = {
        'usuario': usuario,
        'total_usuarios': total_usuarios,
        'total_cursos': total_cursos,
        'total_inscripciones': total_inscripciones
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
        return False
    
    if rol and request.session.get('usuario_rol') != rol:
        return False
    
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