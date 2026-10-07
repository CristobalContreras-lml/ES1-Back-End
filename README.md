# Monitoreo de vencimiento de insumos · Eva 2

**TI3V41 · Programación Back End · Unidad 2 · INACAP**
**Estudiante:** Cristóbal Contreras
**Docente:** Juan Pablo Díaz S.

Sistema de control de vencimientos para la bodega de una cocina central.
Cada lote que entra se clasifica con un semáforo de 4 resultados y queda
guardado en base de datos, con control de acceso por rol.

Esta entrega continúa la ES1: la regla de decisión (`solucion.py`) es la
misma y no se reescribió. Lo que cambió es dónde viven los datos
(`datos.json` → SQLite) y quién puede tocarlos.

---

## 1. Puesta en marcha desde cero

Probado en un clon limpio con Python 3.12 y Django 6.1.

```bash
# 1. Entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate      # Linux / macOS

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
copy .env.example .env          # Windows
# cp .env.example .env           # Linux / macOS
```

Abre el `.env` y completa los valores. La `SECRET_KEY` se genera con:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Define también las tres contraseñas de prueba (`PASS_ADMIN`,
`PASS_NORMAL`, `PASS_VIEWER`). **No hay ninguna contraseña escrita en el
código**: si falta la variable, el usuario no se crea.

```bash
# 4. Crear las tablas
python manage.py migrate

# 5. Crear los grupos y los usuarios de prueba
python manage.py crear_roles

# 6. Pasar los datos de la ES1 a la base (opcional)
python manage.py cargar_datos

# 7. Superusuario para el administrador de Django
python manage.py createsuperuser

# 8. Levantar
python manage.py runserver
```

| Dirección | Para qué |
|---|---|
| `http://127.0.0.1:8000/` | Inventario (requiere sesión) |
| `http://127.0.0.1:8000/login/` | Entrar |
| `http://127.0.0.1:8000/admin/` | Administrador de Django |

### Verificación

```bash
python manage.py check                        # sin issues
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py test                         # 29 tests OK
```

---

## 2. Conexión a la base de datos

La conexión no está escrita a mano en `settings.py`: se arma con
variables de entorno leídas con `python-decouple`.

```python
DB_ENGINE = config("DB_ENGINE", default="django.db.backends.sqlite3")

if DB_ENGINE.endswith("sqlite3"):
    DATABASES = {"default": {"ENGINE": DB_ENGINE,
                             "NAME": BASE_DIR / config("DB_NAME", default="db.sqlite3")}}
else:
    DATABASES = {"default": {"ENGINE": DB_ENGINE,
                             "NAME": config("DB_NAME"),
                             "USER": config("DB_USER"),
                             "PASSWORD": config("DB_PASSWORD"), ...}}
```

Por defecto es SQLite, que es lo que pide la unidad y no necesita
credenciales. La rama de PostgreSQL queda escrita para que el día que se
cambie de motor sólo se edite el `.env`: **en el código no hay ni un
usuario ni una contraseña de base de datos.**

También salen del `.env` la `SECRET_KEY`, el `DEBUG` y los
`ALLOWED_HOSTS`.

---

## 3. Modelo de datos

Cada clave del antiguo `datos.json` pasó a ser un campo:

| `datos.json` | Modelo `Lote` | Tipo |
|---|---|---|
| `nombre` | `nombre` | `CharField(100)` |
| `categoria` | `categoria` | `CharField` con `choices` |
| `lote` | `numero_lote` | `CharField(30)` |
| `cantidad` | `cantidad` | `IntegerField` ≥ 1 |
| `vence` | `vence` | `DateField` |
| `estado` | `estado_registro` | `CharField` (foto al registrar) |
| `motivo` | `motivo_registro` | `CharField(300)` |
| `registrado` | `fecha_registro` | `DateTimeField` |
| — | `eliminado`, `fecha_eliminacion` | borrado lógico |

Las categorías válidas **no están escritas dos veces**: el `choices` se
genera desde el diccionario `UMBRALES` de `solucion.py`.

```python
CATEGORIA_CHOICES = [(c, c) for c in UMBRALES]
```

### Por qué hay dos estados y no uno

El guion de la unidad guarda el resultado en un campo y lo muestra. Acá
eso no sirve: **el estado de este proyecto cambia solo con el paso de los
días.** Un lote registrado como VERDE es ROJO dos semanas después aunque
nadie toque la ficha.

La solución son dos cosas distintas:

- `estado_registro`: la foto del día en que entró el lote. Es un campo
  guardado y sirve de trazabilidad.
- `estado_actual`: una `@property` que llama a `clasificar_insumo()` con
  la fecha de hoy. Es lo que se muestra en el inventario.

Cuando los dos no coinciden, la lista lo avisa («registrado como VERDE»).
Es la misma decisión que ya había tomado la vista de la ES1.

---

## 4. Administrador de Django

`LoteAdmin` incluye:

- `list_display` con 8 columnas, incluido un semáforo con color.
- `list_filter` por categoría, estado de baja y fecha de vencimiento.
- `search_fields` por nombre y número de lote, y `date_hierarchy`.
- `readonly_fields` sobre los campos calculados: el estado de registro y
  las fechas no se editan a mano, porque si se pudieran escribir la ficha
  podría mentir.
- `fieldsets` que separan datos del lote, clasificación y trazabilidad.
- Dos acciones masivas: dar de baja (borrado lógico) y restaurar.
- `save_model` reclasifica al guardar, igual que el CRUD web.
- `has_delete_permission` reserva el **borrado físico** al superusuario:
  la merma tiene que quedar registrada.

Los permisos de cada grupo (`view_lote`, `add_lote`, `change_lote`) se
asignan en `crear_roles`, así que el administrador respeta los mismos
roles que la aplicación.

---

## 5. CRUD y roles

| Vista | URL | Quién puede |
|---|---|---|
| Listar (READ) | `/` | admin, normal, viewer |
| Crear (CREATE) | `/lotes/crear/` | admin, normal |
| Ver ficha | `/lotes/<pk>/` | admin |
| Editar (UPDATE) | `/lotes/<pk>/editar/` | admin |
| Dar de baja (DELETE lógico) | `/lotes/<pk>/eliminar/` | admin |

El permiso se aplica con el decorador `@requiere_rol(...)` de
`core/permisos.py`, **en el servidor**. La plantilla también esconde los
botones que no corresponden, pero eso es sólo comodidad: el
`{% if es_admin %}` va *además* del decorador, nunca en su lugar.

Comprobado escribiendo las direcciones a mano con cada usuario:

```
lector      /lotes/crear/ -> BLOQUEADO   /lotes/1/editar/ -> BLOQUEADO
bodeguero   /lotes/crear/ -> permitido   /lotes/1/editar/ -> BLOQUEADO
jefe        /lotes/crear/ -> permitido   /lotes/1/editar/ -> permitido
sin sesión  /lotes/crear/ -> /login/?next=/lotes/crear/
```

### Validación y mensajes

La validación vive en `LoteForm` (`core/forms.py`), no repartida dentro
de la vista, así el mismo formulario sirve para crear y para editar:

- nombre de al menos 3 caracteres, número de lote normalizado a mayúsculas;
- cantidad entera entre 1 y 100.000 (`"diez"` devuelve el formulario con
  el error, no un error 500);
- año de vencimiento razonable;
- regla de negocio en `clean()`: **no se recibe en bodega un lote ya
  vencido**, usando la misma clasificación de `solucion.py`.

Cada acción deja un mensaje con `django.contrib.messages`.

---

## 6. Seguridad

| Medida | Dónde |
|---|---|
| Contraseñas cifradas (PBKDF2) | `User` de Django, nunca un modelo propio |
| CSRF | `{% csrf_token %}` en los 4 formularios POST, incluido el logout |
| Permisos por rol | decorador en el servidor |
| Secretos fuera del código | `.env` + `python-decouple` |
| Cookie de sesión | `HttpOnly`, expira en 8 h o al cerrar el navegador |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | activas cuando `DEBUG=False` |
| Clickjacking y sniffing | `X_FRAME_OPTIONS=DENY`, `nosniff` |
| Mensaje de login genérico | no revela si falló el usuario o la contraseña |

El logout es POST, no un enlace GET: así no se puede cerrar la sesión de
alguien desde una imagen o un link externo.

---

## 7. Pruebas

29 tests en `core/tests.py`, todos en verde:

| Clase | Qué cubre |
|---|---|
| `ReglaDeDecisionTest` | los 4 resultados y que cada categoría use su propio umbral |
| `ModeloTest` | borrado lógico y que el estado guardado envejezca mientras el actual no |
| `CrudTest` | crear, editar (reclasifica), dar de baja, 404, buscador, datos inválidos |
| `PermisosTest` | cada rol contra cada URL, incluido POST directo sin pasar por el botón |
| `SesionTest` | login, logout, mensaje genérico, contraseña nunca en texto plano |
| `CsrfTest` | POST sin token devuelve 403 |

```
Ran 29 tests in 13.2s
OK
```

---

## 8. Estructura

```
miproyecto/
├── solucion.py            # regla de decision de la ES1, intacta
├── datos.json             # datos de la ES1, ya migrados
├── manage.py
├── .env.example           # plantilla, sin valores
├── requirements.txt
├── plan.md  ia.md  README.md
├── miproyecto/
│   ├── settings.py        # BD y secretos por variables de entorno
│   └── urls.py
└── core/
    ├── models.py          # Lote
    ├── forms.py           # LoteForm con validaciones
    ├── views.py           # CRUD + login/logout
    ├── admin.py           # LoteAdmin
    ├── permisos.py        # requiere_rol
    ├── context_processors.py
    ├── tests.py           # 29 pruebas
    ├── migrations/0001_initial.py
    ├── management/commands/
    │   ├── crear_roles.py
    │   └── cargar_datos.py
    └── templates/         # base, lista, form, confirmar, detalle, login
```

---

## 9. Nota sobre los datos migrados

De los 8 registros de `datos.json` se cargaron 6. Los otros dos tenían
categorías fuera de la lista (`Abarrotes`, `Conservas y salsas`) y la base
los rechaza:

```
Rechazado 'Harina sin cernir' (H-0104): categoria: Valor 'Abarrotes' no es una opción válida.
Rechazado 'Tomate triturado' (TM-8834A): categoria: Valor 'Conservas y salsas' no es una opción válida.
```

No es un error del script: es la diferencia entre el JSON y una base de
datos. Antes el dato malo entraba y quedaba guardado como `INVALIDO`;
ahora el `choices` lo frena en la puerta. El resultado `INVALIDO` sigue
existiendo en la regla y sigue probado, porque los datos antiguos que ya
están en la base pueden quedar en ese estado.
