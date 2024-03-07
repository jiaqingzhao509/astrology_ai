from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.chatbot, name = 'chatbot'),
    path('start-chat/', views.start_chat, name='start_chat'),
]


