from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User  # ← Importar el modelo User de Django

# -----------------------------------------------------
# Modelo Usuario (Perfil Extendido)
# -----------------------------------------------------
class Usuario(models.Model):
    ROLES = [
        ('estudiante', 'Estudiante'),
        ('profesor', 'Profesor'),
        ('admin', 'Administrador'),
    ]
    ESTADOS = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    idUsuario = models.AutoField(primary_key=True)
    
    # ← NUEVO: Relación con el User de Django
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='perfil',
        null=True,  # Temporal para migración
        blank=True
    )
    
    Nombres = models.CharField(max_length=50)
    Apellidos = models.CharField(max_length=50)
    Correo = models.EmailField(max_length=100, unique=True)
    
    # ← YA NO SE NECESITA: Django maneja la contraseña en el modelo User
    # Contrasena = models.CharField(max_length=255)  # ← ELIMINADO
    
    Rol = models.CharField(max_length=11, choices=ROLES)
    Fecha_registro = models.DateTimeField(default=timezone.now)
    Estado = models.CharField(max_length=8, choices=ESTADOS, default='activo')

    class Meta:
        db_table = 'Usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.Nombres} {self.Apellidos} ({self.Rol})"


# -----------------------------------------------------
# Modelo Curso
# -----------------------------------------------------
class Curso(models.Model):
    NIVELES = [
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('C1', 'C1'),
    ]
    MODALIDADES = [
        ('sincrónica', 'Sincrónica'),
        ('asincrónica', 'Asincrónica'),
    ]
    ESTADOS = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    idCurso = models.AutoField(primary_key=True)
    Nombre = models.CharField(max_length=100)
    Nivel_mcerl = models.CharField(max_length=2, choices=NIVELES)
    Modalidad = models.CharField(max_length=12, choices=MODALIDADES)
    Estado = models.CharField(max_length=8, choices=ESTADOS, default='activo')

    class Meta:
        db_table = 'Curso'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def __str__(self):
        return f"{self.Nombre} - {self.Nivel_mcerl}"


# -----------------------------------------------------
# Modelo Inscripcion
# -----------------------------------------------------
class Inscripcion(models.Model):
    ESTADOS = [
        ('activa', 'Activa'),
        ('cancelada', 'Cancelada'),
        ('finalizada', 'Finalizada'),
    ]

    idInscripcion = models.AutoField(primary_key=True)
    idUsuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='inscripciones'
    )
    idCurso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE,
        db_column='idCurso',
        related_name='inscripciones'
    )
    Fecha_inscripcion = models.DateTimeField(default=timezone.now)
    Estado = models.CharField(max_length=10, choices=ESTADOS, default='activa')

    class Meta:
        db_table = 'Inscripcion'
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        unique_together = ['idUsuario', 'idCurso']

    def __str__(self):
        return f"{self.idUsuario} - {self.idCurso}"


# -----------------------------------------------------
# Modelo Clase
# -----------------------------------------------------
class Clase(models.Model):
    TIPOS = [
        ('sincrónica', 'Sincrónica'),
        ('asincrónica', 'Asincrónica'),
    ]

    idClase = models.AutoField(primary_key=True)
    idCurso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE,
        db_column='idCurso',
        related_name='clases'
    )
    Fecha_hora = models.DateTimeField()
    Enlace_clase = models.CharField(max_length=255)
    Tipo = models.CharField(max_length=12, choices=TIPOS)
    Material_asociado = models.CharField(max_length=255)

    class Meta:
        db_table = 'Clase'
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'
        ordering = ['Fecha_hora']

    def __str__(self):
        return f"Clase {self.idClase} - {self.idCurso.Nombre}"


# -----------------------------------------------------
# Modelo ReciboPago
# -----------------------------------------------------
class ReciboPago(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
    ]

    idRecibo = models.AutoField(primary_key=True)
    idUsuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='recibos'
    )
    Fecha_emision = models.DateTimeField(default=timezone.now)
    Valor = models.DecimalField(max_digits=10, decimal_places=2)
    Estado_pago = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')

    class Meta:
        db_table = 'ReciboPago'
        verbose_name = 'Recibo de Pago'
        verbose_name_plural = 'Recibos de Pago'
        ordering = ['-Fecha_emision']

    def __str__(self):
        return f"Recibo {self.idRecibo} - {self.idUsuario}"


# -----------------------------------------------------
# Modelo ContenidoEducativo
# -----------------------------------------------------
class ContenidoEducativo(models.Model):
    TIPOS = [
        ('PDF', 'PDF'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('enlace', 'Enlace'),
    ]

    idContenido = models.AutoField(primary_key=True)
    Titulo = models.CharField(max_length=100)
    Tipo = models.CharField(max_length=6, choices=TIPOS)
    Archivo_url = models.CharField(max_length=255)
    idCurso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE,
        db_column='idCurso',
        related_name='contenidos'
    )
    Subido_por = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='Subido_por',
        related_name='contenidos_subidos'
    )

    class Meta:
        db_table = 'ContenidoEducativo'
        verbose_name = 'Contenido Educativo'
        verbose_name_plural = 'Contenidos Educativos'

    def __str__(self):
        return f"{self.Titulo} - {self.Tipo}"


# -----------------------------------------------------
# Modelo Evaluacion
# -----------------------------------------------------
class Evaluacion(models.Model):
    idEvaluacion = models.AutoField(primary_key=True)
    idCurso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE,
        db_column='idCurso',
        related_name='evaluaciones'
    )
    Nombre = models.CharField(max_length=100)
    Descripcion = models.TextField()
    Fecha = models.DateField()

    class Meta:
        db_table = 'Evaluacion'
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'
        ordering = ['Fecha']

    def __str__(self):
        return f"{self.Nombre} - {self.idCurso.Nombre}"


# -----------------------------------------------------
# Modelo ResultadoEvaluacion
# -----------------------------------------------------
class ResultadoEvaluacion(models.Model):
    idResultado = models.AutoField(primary_key=True)
    idUsuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='resultados'
    )
    idEvaluacion = models.ForeignKey(
        Evaluacion, 
        on_delete=models.CASCADE,
        db_column='idEvaluacion',
        related_name='resultados'
    )
    Nota = models.DecimalField(max_digits=5, decimal_places=2)
    Retroalimentacion = models.TextField()

    class Meta:
        db_table = 'ResultadoEvaluacion'
        verbose_name = 'Resultado de Evaluación'
        verbose_name_plural = 'Resultados de Evaluaciones'

    def __str__(self):
        return f"{self.idUsuario} - {self.idEvaluacion} - Nota: {self.Nota}"


# -----------------------------------------------------
# Modelo Mensaje
# -----------------------------------------------------
class Mensaje(models.Model):
    idMensaje = models.AutoField(primary_key=True)
    Remitente = models.ForeignKey(
        Usuario, 
        related_name='mensajes_enviados', 
        on_delete=models.CASCADE,
        db_column='Remitente'
    )
    Destinatario = models.ForeignKey(
        Usuario, 
        related_name='mensajes_recibidos', 
        on_delete=models.CASCADE,
        db_column='Destinatario'
    )
    Contenido = models.TextField()
    Fecha_hora = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'Mensaje'
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['-Fecha_hora']

    def __str__(self):
        return f"De: {self.Remitente} Para: {self.Destinatario}"


# -----------------------------------------------------
# Modelo Reporte
# -----------------------------------------------------
class Reporte(models.Model):
    idReporte = models.AutoField(primary_key=True)
    idUsuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='reportes'
    )
    idCurso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE,
        db_column='idCurso',
        related_name='reportes'
    )
    Asistencia = models.DecimalField(max_digits=5, decimal_places=2)
    Progreso = models.DecimalField(max_digits=5, decimal_places=2)
    Comentarios_profesor = models.TextField()

    class Meta:
        db_table = 'Reporte'
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'

    def __str__(self):
        return f"Reporte {self.idReporte} - {self.idUsuario}"


# -----------------------------------------------------
# Modelo TicketSoporte
# -----------------------------------------------------
class TicketSoporte(models.Model):
    ESTADOS = [
        ('abierto', 'Abierto'),
        ('cerrado', 'Cerrado'),
        ('pendiente', 'Pendiente'),
    ]

    idTicket = models.AutoField(primary_key=True)
    
    # Relación OPCIONAL con Usuario (para usuarios autenticados)
    idUsuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='tickets',
        null=True,
        blank=True
    )
    
    # Campos para usuarios NO autenticados
    nombre_usuario = models.CharField(max_length=100, blank=True, null=True)
    email_usuario = models.EmailField(max_length=100, blank=True, null=True)
    
    # Campos comunes
    Fecha_creacion = models.DateTimeField(default=timezone.now)
    Estado = models.CharField(max_length=10, choices=ESTADOS, default='abierto')
    Asunto = models.CharField(max_length=100)
    Descripcion = models.TextField()

    class Meta:
        db_table = 'TicketSoporte'
        verbose_name = 'Ticket de Soporte'
        verbose_name_plural = 'Tickets de Soporte'
        ordering = ['-Fecha_creacion']

    def __str__(self):
        if self.idUsuario:
            return f"Ticket {self.idTicket} - {self.Asunto} (Usuario: {self.idUsuario})"
        else:
            return f"Ticket {self.idTicket} - {self.Asunto} (Anónimo: {self.nombre_usuario})"
    
    def get_nombre_contacto(self):
        """Retorna el nombre del contacto, sea usuario autenticado o no"""
        if self.idUsuario:
            return f"{self.idUsuario.Nombres} {self.idUsuario.Apellidos}"
        return self.nombre_usuario
    
    def get_email_contacto(self):
        """Retorna el email del contacto, sea usuario autenticado o no"""
        if self.idUsuario:
            return self.idUsuario.Correo
        return self.email_usuario


# -----------------------------------------------------
# Modelo LogActividad
# -----------------------------------------------------
class LogActividad(models.Model):
    idLog = models.AutoField(primary_key=True)
    idUsuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='logs'
    )
    Accion = models.CharField(max_length=100)
    Fecha_hora = models.DateTimeField(default=timezone.now)
    Detalle = models.TextField()

    class Meta:
        db_table = 'LogActividad'
        verbose_name = 'Log de Actividad'
        verbose_name_plural = 'Logs de Actividad'
        ordering = ['-Fecha_hora']

    def __str__(self):
        return f"{self.idUsuario} - {self.Accion}"


# -----------------------------------------------------
# Modelo IdiomaInterfaz
# -----------------------------------------------------
class IdiomaInterfaz(models.Model):
    idIdioma = models.AutoField(primary_key=True)
    Codigo_idioma = models.CharField(max_length=2)
    Nombre = models.CharField(max_length=50)
    Por_defecto = models.BooleanField(default=False)
    idUsuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idUsuario',
        related_name='idiomas_preferidos'
    )

    class Meta:
        db_table = 'IdiomaInterfaz'
        verbose_name = 'Idioma de Interfaz'
        verbose_name_plural = 'Idiomas de Interfaz'

    def __str__(self):
        return f"{self.Nombre} ({self.Codigo_idioma})"


# -----------------------------------------------------
# Profesor curso (Relación Muchos a Muchos)
# -----------------------------------------------------

class ProfesorCurso(models.Model):
    """
    Tabla de unión entre Profesor y Curso
    Permite que un profesor enseñe múltiples cursos
    y un curso tenga múltiples profesores
    """
    idProfesor = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        db_column='idProfesor',
        related_name='cursos_enseña',
        limit_choices_to={'Rol': 'profesor'}
    )
    idCurso = models.ForeignKey(
        Curso, 
        on_delete=models.CASCADE,
        db_column='idCurso',
        related_name='profesores'
    )
    Fecha_asignacion = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'ProfesorCurso'
        verbose_name = 'Profesor-Curso'
        verbose_name_plural = 'Profesores-Cursos'
        unique_together = ['idProfesor', 'idCurso']
    
    def __str__(self):
        return f"{self.idProfesor.Nombres} - {self.idCurso.Nombre}"

# -----------------------------------------------------
# Modelo de chat
# -----------------------------------------------------

class Chat(models.Model):
    """Modelo para mensajería interna entre estudiantes y profesores"""
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='chats_enviados',
        db_column='sender',
        to_field='idUsuario'
    )
    receiver = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='chats_recibidos',
        db_column='receiver',
        to_field='idUsuario'
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'Chat'
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.Nombres} -> {self.receiver.Nombres}: {self.message[:30]}"