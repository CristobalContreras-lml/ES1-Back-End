"""Direcciones del proyecto."""

from django.contrib import admin
from django.urls import path

from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Sesion
    path("login/", views.vista_login, name="login"),
    path("logout/", views.vista_logout, name="logout"),
    # CRUD
    path("", views.lista, name="lista"),
    path("lotes/crear/", views.crear, name="crear"),
    path("lotes/<int:pk>/", views.detalle, name="detalle"),
    path("lotes/<int:pk>/editar/", views.editar, name="editar"),
    path("lotes/<int:pk>/eliminar/", views.eliminar, name="eliminar"),
]
