from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages as admin_messages
from .models import (
    Usuario, Curso, Inscripcion, Clase, ReciboPago,
    ContenidoEducativo, Evaluacion, ResultadoEvaluacion,
    Mensaje, Reporte, TicketSoporte, LogActividad, IdiomaInterfaz
)

# ===== FORMULARIO PERSONALIZADO PARA VALIDACIÓN =====

class UsuarioInlineForm(forms.ModelForm):
    """
    Formulario personalizado que hace obligatorios los campos del perfil
    """
    class Meta:
        model = Usuario
        fields = ('Nombres', 'Apellidos', 'Correo', 'Rol', 'Estado')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer todos los campos obligatorios
        self.fields['Nombres'].required = True
        self.fields['Apellidos'].required = True
        self.fields['Correo'].required = True
        self.fields['Rol'].required = True
        self.fields['Estado'].required = True
        
        # Agregar ayuda visual
        self.fields['Rol'].help_text = '⚠️ Campo obligatorio: Selecciona el rol del usuario'
        self.fields['Nombres'].widget.attrs['placeholder'] = 'Ingresa los nombres'
        self.fields['Apellidos'].widget.attrs['placeholder'] = 'Ingresa los apellidos'
        self.fields['Correo'].widget.attrs['placeholder'] = 'ejemplo@correo.com'


# ===== PERSONALIZACIÓN DEL USER DE DJANGO =====

class UsuarioInline(admin.StackedInline):
    """
    Permite agregar la información del perfil Usuario 
    directamente en el formulario de creación de User
    """
    model = Usuario
    form = UsuarioInlineForm
    can_delete = False
    verbose_name_plural = '📋 Información del Perfil (OBLIGATORIO)'
    fk_name = 'user'
    fields = ('Nombres', 'Apellidos', 'Correo', 'Rol', 'Estado')
    
    # Hacer obligatorio completar el perfil
    min_num = 1  # Mínimo 1 perfil
    max_num = 1  # Máximo 1 perfil
    extra = 1    # Mostrar 1 formulario de perfil
    
    def get_extra(self, request, obj=None, **kwargs):
        """Mostrar el formulario solo al crear, no al editar"""
        if obj:
            return 0
        return 1


class CustomUserAdmin(BaseUserAdmin):
    """
    Extiende el admin de User para incluir el perfil Usuario
    """
    inlines = (UsuarioInline,)
    
    list_display = (
        'username', 
        'email', 
        'obtener_nombre_completo', 
        'obtener_rol', 
        'is_staff', 
        'is_active'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'perfil__Nombres', 'perfil__Apellidos')
    
    def obtener_nombre_completo(self, obj):
        """Muestra el nombre completo del perfil"""
        if hasattr(obj, 'perfil') and obj.perfil:
            return f"{obj.perfil.Nombres} {obj.perfil.Apellidos}"
        return '⚠️ Sin perfil'
    obtener_nombre_completo.short_description = 'Nombre Completo'
    
    def obtener_rol(self, obj):
        """Muestra el rol del usuario"""
        if hasattr(obj, 'perfil') and obj.perfil:
            return obj.perfil.get_Rol_display()
        return '⚠️ Sin rol'
    obtener_rol.short_description = 'Rol'
    obtener_rol.admin_order_field = 'perfil__Rol'
    
    def save_model(self, request, obj, form, change):
        """Guardar el modelo User"""
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        """Validar y guardar el formset del perfil"""
        instances = formset.save(commit=False)
        
        # Si es un nuevo usuario (no edición)
        if not change:
            if not instances:
                admin_messages.error(
                    request, 
                    '⚠️ ERROR: Debes completar TODOS los campos del perfil (Nombres, Apellidos, Correo y Rol) para crear el usuario.'
                )
                return
        
        # Guardar las instancias
        for instance in instances:
            instance.save()
        
        # Eliminar instancias marcadas para borrar
        for obj in formset.deleted_objects:
            obj.delete()
        
        formset.save_m2m()


# Desregistrar el User admin original de Django
admin.site.unregister(User)

# Registrar el User admin personalizado con el perfil integrado
admin.site.register(User, CustomUserAdmin)


# ===== REGISTRO Y PERSONALIZACIÓN DE MODELOS DE CORE =====

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('idUsuario', 'Nombres', 'Apellidos', 'Correo', 'Rol', 'Estado', 'Fecha_registro')
    list_filter = ('Rol', 'Estado', 'Fecha_registro')
    search_fields = ('Nombres', 'Apellidos', 'Correo')
    readonly_fields = ('Fecha_registro',)
    date_hierarchy = 'Fecha_registro'
    
    fieldsets = (
        ('🔗 Vinculación con Usuario Django', {
            'fields': ('user',),
            'description': 'Usuario de Django asociado a este perfil'
        }),
        ('👤 Información Personal', {
            'fields': ('Nombres', 'Apellidos', 'Correo')
        }),
        ('⚙️ Configuración', {
            'fields': ('Rol', 'Estado', 'Fecha_registro')
        }),
    )
    
    def has_add_permission(self, request):
        """
        Deshabilitar agregar Usuario directamente desde aquí.
        Los usuarios deben crearse desde Authentication and Authorization → Users
        """
        return True


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('idCurso', 'Nombre', 'Nivel_mcerl', 'Modalidad', 'Estado')
    list_filter = ('Nivel_mcerl', 'Modalidad', 'Estado')
    search_fields = ('Nombre',)
    
    fieldsets = (
        ('📚 Información del Curso', {
            'fields': ('Nombre', 'Nivel_mcerl')
        }),
        ('⚙️ Configuración', {
            'fields': ('Modalidad', 'Estado')
        }),
    )


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('idInscripcion', 'obtener_estudiante', 'idCurso', 'Fecha_inscripcion', 'Estado')
    list_filter = ('Estado', 'Fecha_inscripcion', 'idCurso')
    search_fields = ('idUsuario__Nombres', 'idUsuario__Apellidos', 'idCurso__Nombre')
    date_hierarchy = 'Fecha_inscripcion'
    readonly_fields = ('Fecha_inscripcion',)
    
    fieldsets = (
        ('👥 Inscripción', {
            'fields': ('idUsuario', 'idCurso')
        }),
        ('📅 Fechas y Estado', {
            'fields': ('Fecha_inscripcion', 'Estado')
        }),
    )
    
    def obtener_estudiante(self, obj):
        return f"{obj.idUsuario.Nombres} {obj.idUsuario.Apellidos}"
    obtener_estudiante.short_description = 'Estudiante'
    obtener_estudiante.admin_order_field = 'idUsuario__Nombres'


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('idClase', 'idCurso', 'Fecha_hora', 'Tipo', 'obtener_enlace_corto')
    list_filter = ('Tipo', 'Fecha_hora', 'idCurso')
    search_fields = ('idCurso__Nombre', 'Enlace_clase')
    date_hierarchy = 'Fecha_hora'
    
    fieldsets = (
        ('📚 Información de la Clase', {
            'fields': ('idCurso', 'Fecha_hora', 'Tipo')
        }),
        ('🔗 Enlaces y Material', {
            'fields': ('Enlace_clase', 'Material_asociado')
        }),
    )
    
    def obtener_enlace_corto(self, obj):
        if len(obj.Enlace_clase) > 50:
            return f"{obj.Enlace_clase[:50]}..."
        return obj.Enlace_clase
    obtener_enlace_corto.short_description = 'Enlace'


@admin.register(ReciboPago)
class ReciboPagoAdmin(admin.ModelAdmin):
    list_display = ('idRecibo', 'obtener_usuario', 'Fecha_emision', 'Valor', 'Estado_pago')
    list_filter = ('Estado_pago', 'Fecha_emision')
    search_fields = ('idUsuario__Nombres', 'idUsuario__Apellidos')
    date_hierarchy = 'Fecha_emision'
    readonly_fields = ('Fecha_emision',)
    
    # Acciones disponibles
    actions = ['enviar_recibo_email', 'marcar_como_pagado']
    
    fieldsets = (
        ('👤 Usuario', {
            'fields': ('idUsuario',)
        }),
        ('💰 Información del Pago', {
            'fields': ('Valor', 'Estado_pago')
        }),
        ('📅 Fecha', {
            'fields': ('Fecha_emision',)
        }),
    )
    
    def obtener_usuario(self, obj):
        return f"{obj.idUsuario.Nombres} {obj.idUsuario.Apellidos}"
    obtener_usuario.short_description = 'Usuario'
    obtener_usuario.admin_order_field = 'idUsuario__Nombres'
    
    def enviar_recibo_email(self, request, queryset):
        """Envía el recibo de pago por email al usuario"""
        enviados = 0
        errores = 0
        
        for recibo in queryset:
            try:
                # Obtener datos del usuario y recibo
                usuario = recibo.idUsuario
                destinatario = usuario.Correo
                
                # Formatear el valor en pesos colombianos
                valor_formateado = f"${recibo.Valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                # Crear el asunto y mensaje
                asunto = f'Recibo de Pago #{recibo.idRecibo} - Academia de Idiomas'
                
                mensaje = f"""
Estimado/a {usuario.Nombres} {usuario.Apellidos},

Le informamos que hemos generado su recibo de pago con los siguientes detalles:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   RECIBO DE PAGO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Número de Recibo: #{recibo.idRecibo}
Fecha de Emisión: {recibo.Fecha_emision.strftime('%d/%m/%Y %H:%M')}
Valor: {valor_formateado} COP
Estado: {recibo.get_Estado_pago_display()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{'✅ Este recibo ha sido PAGADO.' if recibo.Estado_pago == 'pagado' else '⚠️ Este recibo está PENDIENTE de pago.'}

Si tiene alguna pregunta, no dude en contactarnos.

Atentamente,
Academia de Idiomas
                """
                
                # Enviar email
                send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email='Academia de Idiomas <noreply@academia.com>',
                    recipient_list=[destinatario],
                    fail_silently=False,
                )
                
                enviados += 1
                
            except Exception as e:
                errores += 1
                self.message_user(
                    request,
                    f'❌ Error al enviar recibo #{recibo.idRecibo}: {str(e)}',
                    level=admin_messages.ERROR
                )
        
        # Mensajes de resultado
        if enviados > 0:
            self.message_user(
                request,
                f'✅ Se enviaron {enviados} recibo(s) correctamente.',
                level=admin_messages.SUCCESS
            )
        
        if errores > 0:
            self.message_user(
                request,
                f'⚠️ Hubo {errores} error(es) al enviar recibos.',
                level=admin_messages.WARNING
            )
    
    enviar_recibo_email.short_description = "📧 Enviar recibo por email"
    
    def marcar_como_pagado(self, request, queryset):
        """Marca los recibos seleccionados como pagados"""
        actualizados = queryset.update(Estado_pago='pagado')
        self.message_user(
            request,
            f'✅ Se marcaron {actualizados} recibo(s) como pagados.',
            level=admin_messages.SUCCESS
        )
    
    marcar_como_pagado.short_description = "✅ Marcar como pagado"


@admin.register(ContenidoEducativo)
class ContenidoEducativoAdmin(admin.ModelAdmin):
    list_display = ('idContenido', 'Titulo', 'Tipo', 'idCurso', 'Subido_por')
    list_filter = ('Tipo', 'idCurso')
    search_fields = ('Titulo', 'idCurso__Nombre')
    
    fieldsets = (
        ('📄 Información del Contenido', {
            'fields': ('Titulo', 'Tipo', 'Archivo_url')
        }),
        ('🔗 Relaciones', {
            'fields': ('idCurso', 'Subido_por')
        }),
    )


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('idEvaluacion', 'Nombre', 'idCurso', 'Fecha')
    list_filter = ('Fecha', 'idCurso')
    search_fields = ('Nombre', 'idCurso__Nombre', 'Descripcion')
    date_hierarchy = 'Fecha'
    
    fieldsets = (
        ('📝 Información de la Evaluación', {
            'fields': ('Nombre', 'Descripcion', 'idCurso')
        }),
        ('📅 Programación', {
            'fields': ('Fecha',)
        }),
    )


@admin.register(ResultadoEvaluacion)
class ResultadoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('idResultado', 'obtener_estudiante', 'idEvaluacion', 'Nota', 'obtener_estado_nota')
    list_filter = ('Nota', 'idEvaluacion')
    search_fields = ('idUsuario__Nombres', 'idEvaluacion__Nombre')
    
    fieldsets = (
        ('👤 Estudiante y Evaluación', {
            'fields': ('idUsuario', 'idEvaluacion')
        }),
        ('📊 Calificación', {
            'fields': ('Nota', 'Retroalimentacion')
        }),
    )
    
    def obtener_estudiante(self, obj):
        return f"{obj.idUsuario.Nombres} {obj.idUsuario.Apellidos}"
    obtener_estudiante.short_description = 'Estudiante'
    obtener_estudiante.admin_order_field = 'idUsuario__Nombres'
    
    def obtener_estado_nota(self, obj):
        nota = float(obj.Nota)
        if nota >= 70:
            return f"✅ Aprobado ({nota})"
        else:
            return f"❌ Reprobado ({nota})"
    obtener_estado_nota.short_description = 'Estado'


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('idMensaje', 'Remitente', 'Destinatario', 'obtener_contenido_corto', 'Fecha_hora')
    list_filter = ('Fecha_hora',)
    search_fields = ('Remitente__Nombres', 'Destinatario__Nombres', 'Contenido')
    date_hierarchy = 'Fecha_hora'
    readonly_fields = ('Fecha_hora',)
    
    fieldsets = (
        ('👥 Participantes', {
            'fields': ('Remitente', 'Destinatario')
        }),
        ('💬 Mensaje', {
            'fields': ('Contenido',)
        }),
        ('📅 Fecha', {
            'fields': ('Fecha_hora',)
        }),
    )
    
    def obtener_contenido_corto(self, obj):
        if len(obj.Contenido) > 50:
            return f"{obj.Contenido[:50]}..."
        return obj.Contenido
    obtener_contenido_corto.short_description = 'Contenido'


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('idReporte', 'obtener_estudiante', 'idCurso', 'Asistencia', 'Progreso')
    list_filter = ('Asistencia', 'Progreso', 'idCurso')
    search_fields = ('idUsuario__Nombres', 'idCurso__Nombre')
    
    fieldsets = (
        ('👤 Estudiante y Curso', {
            'fields': ('idUsuario', 'idCurso')
        }),
        ('📊 Métricas', {
            'fields': ('Asistencia', 'Progreso')
        }),
        ('📝 Observaciones', {
            'fields': ('Comentarios_profesor',)
        }),
    )
    
    def obtener_estudiante(self, obj):
        return f"{obj.idUsuario.Nombres} {obj.idUsuario.Apellidos}"
    obtener_estudiante.short_description = 'Estudiante'
    obtener_estudiante.admin_order_field = 'idUsuario__Nombres'


@admin.register(TicketSoporte)
class TicketSoporteAdmin(admin.ModelAdmin):
    list_display = ('idTicket', 'get_nombre_contacto', 'Asunto', 'Estado', 'Fecha_creacion')
    list_filter = ('Estado', 'Fecha_creacion')
    search_fields = ('Asunto', 'Descripcion', 'nombre_usuario', 'email_usuario', 'idUsuario__Nombres')
    date_hierarchy = 'Fecha_creacion'
    readonly_fields = ('Fecha_creacion',)
    
    fieldsets = (
        ('👤 Información del Usuario', {
            'fields': ('idUsuario', 'nombre_usuario', 'email_usuario'),
            'description': 'Si es un usuario registrado, selecciónalo. Si no, completa nombre y email.'
        }),
        ('🎫 Ticket', {
            'fields': ('Asunto', 'Descripcion', 'Estado')
        }),
        ('📅 Fecha', {
            'fields': ('Fecha_creacion',)
        }),
    )


@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ('idLog', 'idUsuario', 'Accion', 'Fecha_hora')
    list_filter = ('Accion', 'Fecha_hora')
    search_fields = ('idUsuario__Nombres', 'Accion', 'Detalle')
    date_hierarchy = 'Fecha_hora'
    readonly_fields = ('Fecha_hora',)
    
    fieldsets = (
        ('👤 Usuario', {
            'fields': ('idUsuario',)
        }),
        ('📋 Actividad', {
            'fields': ('Accion', 'Detalle')
        }),
        ('📅 Fecha', {
            'fields': ('Fecha_hora',)
        }),
    )
    
    def has_add_permission(self, request):
        """Los logs no deben crearse manualmente"""
        return True


@admin.register(IdiomaInterfaz)
class IdiomaInterfazAdmin(admin.ModelAdmin):
    list_display = ('idIdioma', 'Nombre', 'Codigo_idioma', 'Por_defecto', 'idUsuario')
    list_filter = ('Por_defecto',)
    search_fields = ('Nombre', 'Codigo_idioma', 'idUsuario__Nombres')
    
    fieldsets = (
        ('🌐 Idioma', {
            'fields': ('Codigo_idioma', 'Nombre', 'Por_defecto')
        }),
        ('👤 Usuario', {
            'fields': ('idUsuario',)
        }),
    )


# ===== PERSONALIZACIÓN DEL SITIO ADMIN =====

admin.site.site_header = "🎓 Academia - Panel de Administración"
admin.site.site_title = "Academia Admin"
admin.site.index_title = "Bienvenido al Sistema de Gestión Académica"