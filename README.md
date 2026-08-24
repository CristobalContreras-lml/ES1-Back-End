# Monitoreo de vencimiento de insumos · ES1

## Cómo ejecutar

1. Instalar los paquetes:

   ```
   pip install -r requirements.txt
   ```

2. Crear tu archivo `.env` (no viene en el repo, solo la plantilla `.env.example`):

   ```
   cp .env.example .env
   ```

   Si quieres, cambia el valor de `SECRET_KEY` por otro. `DEBUG=True` está bien para trabajar
   local.

3. Programa de consola (registra lotes y muestra la tabla):

   ```
   python solucion.py
   ```

4. Pantalla web:

   ```
   python manage.py runserver
   ```

   Abrir http://127.0.0.1:8000/

## Archivos

| Archivo | Qué es |
|---|---|
| `plan.md` | Apartado de negocio y apartado técnico |
| `solucion.py` | Programa de consola: regla de decisión, JSON y tabulate |
| `datos.json` | Los lotes registrados (lo crea `solucion.py`) |
| `requirements.txt` | Paquetes instalados con pip |
| `.env.example` | Plantilla de las variables de entorno (sí se sube) |
| `.env` | Claves reales (NO se sube, está en `.gitignore`) |
| `core/` | App Django con la vista y el template |
| `ia.md` | Qué le consulté a la IA y qué corregí yo |

Sin base de datos: no hay modelos ni migraciones. La vista lee `datos.json` directamente.
