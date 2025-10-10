from django import forms
from .models import TicketSoporte

class TicketSoporteForm(forms.ModelForm):
    # Campo extra para nombre (si no está logueado)
    nombre_usuario = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Tu nombre completo'
        })
    )
    
    # Campo extra para email (si no está logueado)
    email_usuario = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'tu@email.com'
        })
    )
    
    class Meta:
        model = TicketSoporte
        fields = ['Asunto', 'Descripcion']
        widgets = {
            'Asunto': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Asunto de tu consulta'
            }),
            'Descripcion': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Describe tu problema en detalle...',
                'rows': 5
            }),
        }