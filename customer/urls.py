from django.urls import path
from customer import views

app_name = 'customer'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]