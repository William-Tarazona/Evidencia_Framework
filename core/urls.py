from django.urls import path
from . import views

urlpatterns = [
    # Páginas principales
    path('', views.index, name='index'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('cursos/', views.cursos, name='cursos'),
    path('metodologia/', views.metodologia, name='metodologia'),
    path('profesores/', views.profesores, name='profesores'),
    
    # Autenticación
    path('pantalla-inicio/', views.pantalla_inicio, name='pantalla_inicio'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('registro/', views.registro, name='registro'),
    
    # Dashboards
    path('dashboard-estudiante/', views.dashboard_estudiante, name='dashboard_estudiante'),
    path('dashboard-profesor/', views.dashboard_profesor, name='dashboard_profesor'),
    path('dashboard-administrativo/', views.dashboard_administrativo, name='dashboard_administrativo'),
    
    # Funcionalidades de cursos
    path('curso/<int:id_curso>/', views.detalle_curso, name='detalle_curso'),
    path('inscribirse/<int:curso_id>/', views.inscribirse_curso, name='inscribirse_curso'),
    
    # Páginas legales y soporte
    path('politicas-privacidad/', views.politicas_privacidad, name='politicas_privacidad'),
    path('terminos/', views.terminos, name='terminos'),
    path('soporte/', views.soporte, name='soporte'),
    
    # Sistema de tickets de soporte
    path('crear-ticket/', views.crear_ticket, name='crear_ticket'),
    path('mis-tickets/', views.mis_tickets, name='mis_tickets'),
    path('ticket/<int:id_ticket>/', views.detalle_ticket, name='detalle_ticket'),
    
    # Sistema de Chat
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/room/<int:user_id>/', views.chat_room, name='chat_room'),
    path('chat/send/', views.send_message, name='send_message'),
    path('chat/get/<int:user_id>/', views.get_messages, name='get_messages'),
]