"""inventario URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.urls import include, path
from cuentas import views as cuentas_views
from usuarios import views as usuarios_views
from productos.views import foto_producto

urlpatterns = [
    path("configuracion/modulos/", usuarios_views.configurar_modulos, name="configuracion_modulos"),
    path("", cuentas_views.dashboard, name="inicio"),
    path('admin/', admin.site.urls),
    path(
        "iniciar-sesion/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("recuperar/", auth_views.PasswordResetView.as_view(
        template_name="registration/recuperar.html",
        email_template_name="registration/correo_recuperacion.txt",
        subject_template_name="registration/asunto_recuperacion.txt",
    ), name="password_reset"),
    path("recuperar/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/enviado.html"), name="password_reset_done"),
    path("recuperar/clave/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/nueva_clave.html"), name="password_reset_confirm"),
    path("recuperar/listo/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/clave_guardada.html"), name="password_reset_complete"),
    path("cerrar-sesion/", auth_views.LogoutView.as_view(), name="logout"),
    path("media/productos/<path:nombre>", foto_producto, name="foto_producto"),
    path("productos/", include("productos.urls") ),
    path("clientes/", include("clientes.urls") ),
    path("cuentas/", include("cuentas.urls") ),
    path(
        "usuarios/",
        include("usuarios.urls"),
    ),
    path(
        "compras/",
        include("compras.urls"),
    ),
    path(
        "ventas/",
        include("ventas.urls"),
    ),
    path(
    "caja/",
    include("caja.urls"),
    ),
    
]
