from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .serializers import UserSerializer, UserRegistrationSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar usuarios.
    Endpoints automáticos:
    - GET /api/v1/users/ - Listar todos los usuarios
    - POST /api/v1/users/ - Crear un usuario
    - GET /api/v1/users/{id}/ - Ver un usuario específico
    - PUT /api/v1/users/{id}/ - Actualizar un usuario
    - DELETE /api/v1/users/{id}/ - Eliminar un usuario
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """Permitir registro sin autenticación, el resto requiere login"""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Usar serializer diferente para registro"""
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Endpoint personalizado para obtener info del usuario autenticado
        GET /api/v1/users/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)