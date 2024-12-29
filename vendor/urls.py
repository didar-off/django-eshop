from django.urls import path
from vendor import views

app_name = "vendor"

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.products, name='products'),
]
