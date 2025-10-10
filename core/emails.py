from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def enviar_recibo_pago(recibo):
    """
    Envía un correo al estudiante con la información del recibo de pago
    y las opciones de pago disponibles.
    
    Args:
        recibo: Instancia del modelo ReciboPago
    
    Returns:
        bool: True si se envió correctamente, False si hubo error
    """
    try:
        # Obtener el correo del estudiante
        correo_estudiante = recibo.idUsuario.Correo
        nombre_estudiante = f"{recibo.idUsuario.Nombres} {recibo.idUsuario.Apellidos}"
        
        # Datos para el template
        context = {
            'nombre_estudiante': nombre_estudiante,
            'numero_recibo': recibo.idRecibo,
            'fecha_emision': recibo.Fecha_emision,
            'valor': recibo.Valor,
            'estado_pago': recibo.Estado_pago,
            # Información de pasarelas de pago
            'pasarelas': [
                {
                    'nombre': 'Bancolombia',
                    'tipo': 'Transferencia Bancaria',
                    'cuenta': '123-456789-01',
                    'tipo_cuenta': 'Ahorros',
                    'titular': 'Academia de Idiomas',
                    'nit': '900.123.456-7'
                },
                {
                    'nombre': 'Nequi',
                    'tipo': 'Pago por celular',
                    'numero': '300 123 4567',
                    'titular': 'Academia de Idiomas'
                },
                {
                    'nombre': 'Daviplata',
                    'tipo': 'Pago por celular',
                    'numero': '300 123 4567',
                    'titular': 'Academia de Idiomas'
                },
                {
                    'nombre': 'PSE',
                    'tipo': 'Pago electrónico',
                    'link': 'https://www.tuacademia.com/pagar',
                    'descripcion': 'Débito desde tu cuenta bancaria'
                },
                {
                    'nombre': 'PayU',
                    'tipo': 'Tarjeta de crédito/débito',
                    'link': 'https://www.tuacademia.com/pagar',
                    'descripcion': 'Visa, Mastercard, American Express'
                }
            ]
        }
        
        # Renderizar el template HTML
        html_content = render_to_string('emails/recibo_pago.html', context)
        text_content = strip_tags(html_content)  # Versión texto plano
        
        # Crear el correo
        asunto = f'Recibo de Pago #{recibo.idRecibo} - Academia de Idiomas'
        
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[correo_estudiante]
        )
        
        # Adjuntar versión HTML
        email.attach_alternative(html_content, "text/html")
        
        # Enviar
        email.send()
        
        print(f"✅ Correo enviado exitosamente a {correo_estudiante}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar correo: {str(e)}")
        return False


def enviar_confirmacion_pago(recibo):
    """
    Envía un correo de confirmación cuando el pago ha sido aprobado.
    
    Args:
        recibo: Instancia del modelo ReciboPago
    """
    try:
        correo_estudiante = recibo.idUsuario.Correo
        nombre_estudiante = f"{recibo.idUsuario.Nombres} {recibo.idUsuario.Apellidos}"
        
        context = {
            'nombre_estudiante': nombre_estudiante,
            'numero_recibo': recibo.idRecibo,
            'fecha_pago': recibo.Fecha_emision,
            'valor': recibo.Valor,
        }
        
        html_content = render_to_string('emails/confirmacion_pago.html', context)
        text_content = strip_tags(html_content)
        
        asunto = f'✅ Pago Confirmado - Recibo #{recibo.idRecibo}'
        
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[correo_estudiante]
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print(f"✅ Confirmación de pago enviada a {correo_estudiante}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar confirmación: {str(e)}")
        return False