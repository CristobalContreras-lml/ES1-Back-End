# ia.md · Uso de inteligencia artificial en la ES1

## Qué herramienta usé y para qué

Usé Claude (Anthropic). La consulté para dos cosas: ordenar el `plan.md` (redactar el problema,
el alcance y la priorización MoSCoW) y revisar la estructura del proyecto Django antes de armarlo.
No la usé como reemplazo del código: cada archivo lo revisé línea por línea y hay partes que
reescribí porque no calzaban con lo que pide la evaluación.

## Una consulta concreta

Le escribí, en resumen: *"Soy estudiante de programación back end, primer semestre. Quiero
resolver el problema de los insumos que se vencen en la bodega de una cocina central. Ayúdame a
escribir un plan de 2 planas con apartado de negocio y apartado técnico, con la regla de decisión
de 4 resultados. Restricción: se resuelve con variables, if/elif, un archivo JSON y una sola vista
Django. Sin base de datos, sin login, sin API."*

La respuesta me sirvió sobre todo para separar los Must de los Should. Yo tenía mezcladas cosas
como el filtro por color y la búsqueda por lote dentro de lo imprescindible, y quedó claro que el
programa igual resuelve el problema sin eso.

## Qué estaba mal, qué sobraba y cómo lo corregí

1. **Me propuso base de datos.** Mi idea inicial del proyecto tenía dos modelos, `Categoria` e
   `Insumo`, con `models.py` y migraciones. La primera respuesta siguió esa idea y me armó los
   modelos. Eso no sirve para esta evaluación: la Unidad 1 es sin base de datos. Lo corregí
   dejando los modelos en la lista de **Won't**, y la vista ahora abre `datos.json` directamente
   con `json.load()`. En `core/` no hay modelos ni migraciones ejecutadas.

2. **Me dejaba solo 3 resultados.** La versión inicial de la regla tenía rojo, amarillo y verde,
   pero no el caso del dato inválido. Agregué esa cuarta rama y la puse **primera** en el `if`,
   porque si una fecha viene mal escrita no se puede restar contra la fecha de hoy y el programa
   se cae antes de llegar a revisarla.

3. **Repetía la regla de decisión dentro de la vista.** El código propuesto volvía a escribir los
   `if` dentro de `views.py`. Lo cambié: `views.py` importa `clasificar_insumo` desde
   `solucion.py`. Tuve que agregar la carpeta raíz al `sys.path`, porque `solucion.py` está una
   carpeta más arriba que `miproyecto/`. Esa parte me costó entenderla y la probé hasta que el
   `import` funcionó.

4. **Un detalle que no entendía al principio:** por qué la vista vuelve a calcular los días si el
   estado ya está guardado en el JSON. Lo entendí probando: si solo mostrara lo guardado, un lote
   registrado como verde seguiría verde para siempre. Al recalcular con `date.today()`, el
   semáforo se mueve solo con el paso de los días. Ese es justamente el punto del proyecto.

## Segunda revisión, contra la rúbrica

Antes de entregar probé el programa con casos límite (mayúsculas/minúsculas, fecha con espacios,
día exacto del umbral) y encontré 3 errores que la IA no me había marcado y que yo tampoco vi a
la primera:

1. **Categoría sensible a mayúsculas.** Si escribía "carnes" en vez de "Carnes", el programa la
   marcaba como dato inválido aunque la categoría existiera. El diccionario de umbrales usa las
   categorías con mayúscula inicial y la comparación `categoria not in UMBRALES` era literal.
   Corregí `clasificar_insumo` para que normalice la categoría con `.strip().capitalize()` antes
   de compararla.

2. **Fecha con espacios se marcaba inválida.** Si `datos.json` traía `" 2026-09-01 "` con espacios
   (por ejemplo, editado a mano), `datetime.strptime` fallaba aunque la fecha fuera correcta.
   Agregué `.strip()` antes de convertir la fecha.

3. **El más importante: la tabla de consola mostraba el estado guardado, no el actual.** Cada
   registro guarda el estado que tenía el día en que se ingresó. Pero `mostrar_tabla` recalculaba
   los días con la fecha de hoy y al mismo tiempo mostraba el estado viejo del JSON, así que un
   lote con -4 días aparecía como "AMARILLO" en vez de "ROJO". Lo detecté comparando la fecha real
   del sistema contra las fechas de mi archivo de prueba. Lo corregí para que `mostrar_tabla` llame
   a `clasificar_insumo` de nuevo por cada fila, igual que ya hacía la vista Django, en vez de
   confiar en el campo `estado` guardado.

Ninguno de estos tres errores estaba en el código que la IA propuso originalmente ni en la primera
versión que yo armé; aparecieron al hacer pruebas con fechas y mayúsculas distintas a las que usé
la primera vez, así que los arreglé por mi cuenta antes de entregar.

## Tercera revisión, contra una versión actualizada del PDF de instrucciones

El docente subió una versión más detallada del PDF de instrucciones, con dos diferencias
importantes respecto a la que usé al principio:

1. **Ubicación de archivos.** El PDF nuevo trae un árbol de carpetas explícito donde
   `solucion.py` y `datos.json` van justo al lado de `manage.py`, no en una carpeta aparte. Yo los
   tenía un nivel más arriba, y por eso `core/views.py` tenía un parche con `sys.path.append` para
   poder importar `solucion.py` desde ahí. Moví ambos archivos a la ubicación correcta y saqué el
   parche: ahora la vista hace `from solucion import clasificar_insumo` directo, porque Django ya
   agrega la carpeta de `manage.py` al `sys.path` automáticamente. El código quedó más simple y
   más parecido al ejemplo de referencia que menciona el PDF.

2. **Archivo `.env`.** El PDF nuevo pide sacar la `SECRET_KEY` de `settings.py` y ponerla en un
   archivo `.env` que no se sube, usando el paquete `python-decouple`. Antes tenía la clave escrita
   directo en el código (así la deja Django por defecto al crear el proyecto). Instalé
   `python-decouple`, cambié `settings.py` para que lea `SECRET_KEY` y `DEBUG` con
   `config('SECRET_KEY')` y `config('DEBUG', default=False, cast=bool)`, y agregué `.env` (con la
   clave real, no se sube), `.env.example` (con una clave de ejemplo, sí se sube) y `.gitignore`
   con `.env` adentro. Probé que si borro el `.env`, el proyecto efectivamente deja de funcionar
   con `UndefinedValueError` en vez de arrancar con una clave inventada, que es el comportamiento
   que pide el PDF.
