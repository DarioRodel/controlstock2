"""
URL configuration for ControlStock project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
# from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
# ControlStock/urls.py
from django.contrib import admin
from django.urls import path, include
from control.views import RegistroUsuarioView, CustomLoginView, CustomLogoutView, PerfilView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('control.urls')),               # Rutas de tu app “control”
    path('cuentas/register/', RegistroUsuarioView.as_view(), name='register'),
    path('cuentas/login/',    CustomLoginView.as_view(),     name='login'),
    path('cuentas/logout/',   CustomLogoutView.as_view(),    name='logout'),
    path('cuentas/perfil/',   PerfilView.as_view(),          name='perfil'),
]

