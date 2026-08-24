"""Direcciones del proyecto. Solo hay una pantalla."""

from django.urls import path

from core.views import resumen

urlpatterns = [
    # Una sola direccion: la raiz del sitio muestra el panel.
    path("", resumen, name="resumen"),
]
