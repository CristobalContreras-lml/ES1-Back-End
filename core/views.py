"""Vista unica del panel de vencimientos.

No hay base de datos: la vista abre datos.json y reutiliza la regla de
decision que ya escribi en solucion.py (Fase 1). No se vuelve a escribir.
"""

import json
import os
from datetime import date

from django.shortcuts import render

# solucion.py esta justo al lado de manage.py, por eso Django ya lo puede
# importar directo: no hace falta tocar sys.path.
from solucion import clasificar_insumo

ARCHIVO_DATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos.json")


def resumen(request):
    # 1. La vista lee el archivo JSON (aca no hay modelos ni migraciones).
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, encoding="utf-8") as f:
            registros = json.load(f)
    else:
        registros = []

    # 2. Se vuelve a clasificar cada lote con la fecha de HOY.
    #    Asi el semaforo cambia solo con el paso de los dias.
    lotes = []
    for r in registros:
        resultado = clasificar_insumo(r["categoria"], r["cantidad"], r["vence"])
        lotes.append({
            "nombre": r["nombre"],
            "categoria": r["categoria"],
            "lote": r["lote"],
            "cantidad": r["cantidad"],
            "vence": r["vence"],
            "dias": resultado["dias"],
            # Si la fecha no se pudo leer, en pantalla se muestra "?" y no "None".
            "dias_texto": "?" if resultado["dias"] is None else resultado["dias"],
            "estado": resultado["estado"],
            "color": resultado["color"],
            "motivo": resultado["motivo"],
        })

    # 3. Se ordenan por fecha de vencimiento: lo que vence antes va primero.
    lotes = sorted(lotes, key=lambda x: x["vence"])

    # 4. Contadores del semaforo.
    rojos = 0
    amarillos = 0
    verdes = 0
    invalidos = 0
    for lote in lotes:
        if lote["estado"] == "ROJO":
            rojos = rojos + 1
        elif lote["estado"] == "AMARILLO":
            amarillos = amarillos + 1
        elif lote["estado"] == "VERDE":
            verdes = verdes + 1
        else:
            invalidos = invalidos + 1

    contexto = {
        "lotes": lotes,
        "hoy": date.today().strftime("%d-%m-%Y"),
        "total": len(lotes),
        "rojos": rojos,
        "amarillos": amarillos,
        "verdes": verdes,
        "invalidos": invalidos,
        "unidades_en_riesgo": sum(l["cantidad"] for l in lotes if l["estado"] == "ROJO"),
    }
    return render(request, "resumen.html", contexto)
