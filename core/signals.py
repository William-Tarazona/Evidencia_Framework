from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Usuario

@receiver(post_save, sender=Usuario)
def sincronizar_email(sender, instance, created, **kwargs):
    """
    Sincroniza automáticamente el email del perfil Usuario 
    con el campo email de auth_user
    """
    if instance.user and instance.Correo:
        # Solo actualizar si el email cambió
        if instance.user.email != instance.Correo:
            instance.user.email = instance.Correo
            instance.user.save(update_fields=['email'])