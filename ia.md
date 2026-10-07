# ia.md · Uso de inteligencia artificial

**TI3V41 · Programación Back End**
**Estudiante:** Cristóbal Contreras

> Actualizado para la Eva 2. La sección de la ES1 queda al final como
> antecedente, porque describe decisiones que siguen vigentes.

---

# Parte 1 · Eva 2 (base de datos, CRUD, roles)

## Qué herramienta usé y para qué

Usé Claude (Anthropic). La consulté para planificar la migración del
proyecto desde `datos.json` a base de datos: cómo traducir las claves del
JSON a campos de un modelo, cómo armar los roles con grupos de Django y
cómo probar que los permisos realmente cortan en el servidor.

No la usé para que escribiera el proyecto de corrido. Lo que pedí fue
estructura y explicación; cada archivo lo revisé, lo corrí y en varios
casos lo cambié, por las razones que están más abajo.

## Consultas concretas

**Sobre el modelo:**

> *«Tengo un proyecto Django que guarda lotes de insumos en un
> datos.json. Cada registro tiene nombre, categoria, lote, cantidad,
> vence, estado y motivo. El estado sale de una función
> `clasificar_insumo()` que compara la fecha de vencimiento contra la
> fecha de hoy y devuelve ROJO, AMARILLO, VERDE o INVALIDO. ¿Cómo
> traduzco eso a un modelo de Django sin reescribir la función? ¿El
> estado va como campo guardado o se calcula?»*

**Sobre los roles:**

> *«Necesito tres roles: uno que sólo mire, uno que pueda crear y uno que
> pueda todo. ¿Grupos de Django o un campo `rol` en un modelo propio?
> ¿Cómo pruebo que el permiso no se puede saltar escribiendo la URL?»*

## Qué corregí de lo que me respondió

### 1. El estado no podía ser un campo guardado y punto

El guion de la unidad y la primera respuesta de la IA proponen lo mismo:
guardar el resultado en un campo `resultado` y mostrarlo en la lista. En
casi cualquier proyecto eso está bien, pero en este **no**: acá el estado
depende de la fecha de hoy, así que un lote guardado como VERDE seguiría
viéndose verde dos semanas después de vencido. Es justo el error que el
sistema debe evitar.

Lo resolví con dos cosas distintas en vez de una:

```python
estado_registro = models.CharField(max_length=20)   # foto al registrar

@property
def estado_actual(self):                             # semaforo de hoy
    return self.clasificacion["estado"]
```

Y agregué `cambio_de_estado`, que compara las dos y hace que la lista
avise «registrado como VERDE» cuando ya no lo está. Es la misma decisión
que había tomado en la ES1 para la vista, sólo que ahora vive en el
modelo. Está probado en `ModeloTest.test_el_estado_guardado_envejece_y_el_actual_no`.

### 2. El modelo de ejemplo no era el de mi proyecto

El ejemplo de referencia usa un modelo genérico (`nombre`, `cantidad`,
`estado`) con dos opciones, «al día» y «moroso». Si lo copiaba tal cual,
el proyecto dejaba de ser el mío: no hay fecha de vencimiento, que es el
dato del que depende todo. Lo reescribí con los campos reales del JSON y
mantuve del ejemplo lo que sí correspondía: el borrado lógico y el
`soft_delete()`.

También evité duplicar la lista de categorías. La IA la proponía escrita
a mano en el `choices`, pero esa lista ya existe en `UMBRALES` dentro de
`solucion.py`; tenerla en dos lugares significa que algún día van a
quedar distintas. Quedó así:

```python
CATEGORIA_CHOICES = [(c, c) for c in UMBRALES]
```

### 3. Las vistas con `request.POST` crudo no validaban nada

El código propuesto leía los campos directo del `request.POST` y
convertía la cantidad con un `int()` dentro de un `try`. Funciona, pero
la validación queda repartida dentro de la vista y hay que repetirla
igual en crear y en editar.

Lo cambié por un `ModelForm` (`core/forms.py`). Con eso la validación
está en un solo lugar, las dos vistas la reutilizan, y pude agregar una
regla de negocio que el `try/except` no cubría: **no se recibe en bodega
un lote que ya está vencido**, usando la misma clasificación en vez de
volver a comparar fechas.

### 4. Permisos sólo en la plantilla

La primera propuesta escondía los botones con `{% if %}` y lo daba por
resuelto. Eso no es seguridad: la dirección se puede escribir a mano. Lo
corregí poniendo el decorador `@requiere_rol(...)` en cada vista y dejé
el `{% if %}` sólo como comodidad visual.

Lo comprobé levantando el servidor y entrando con cada usuario a las
direcciones directas, sin usar los botones:

```
lector      /lotes/crear/ -> BLOQUEADO   /lotes/1/editar/ -> BLOQUEADO
bodeguero   /lotes/crear/ -> permitido   /lotes/1/editar/ -> BLOQUEADO
jefe        /lotes/crear/ -> permitido   /lotes/1/editar/ -> permitido
sin sesión  /lotes/crear/ -> /login/?next=/lotes/crear/
```

Además lo dejé como prueba automática, incluyendo el caso del POST
directo: `PermisosTest.test_normal_no_puede_eliminar_por_post_directo`.
Ese caso importa porque bloquear sólo el GET deja la puerta abierta.

### 5. El código de ejemplo no compilaba

Esto no es culpa de la IA sino del material que copié, pero vale
anotarlo porque me costó un rato: el guion trae `if request.method =
"POST"` con un solo `=`, `def _str_` en vez de `__str__`, `name _in` en
vez de `name__in` y `makemigrations -check` con un guion. Lo copié tal
cual y no corría. Son erratas de formato del PDF, pero el que las copia
sin leer pierde media hora.

## Lo que encontré yo al probar

**La migración de datos rechazó 2 de 8 registros.** Al correr
`cargar_datos` pasó esto:

```
Rechazado 'Harina sin cernir' (H-0104): categoria: Valor 'Abarrotes' no es una opción válida.
Rechazado 'Tomate triturado' (TM-8834A): categoria: Valor 'Conservas y salsas' no es una opción válida.
Cargados: 6
```

No lo había previsto y al principio pensé que el script estaba malo.
Revisándolo, es correcto: esos dos registros eran justamente los que en
el JSON quedaban guardados como `INVALIDO`, porque el archivo dejaba
entrar cualquier cosa. La base, con `choices`, los frena en la puerta.
Decidí que el comando los **informe y los salte** en vez de cargarlos
mal, y lo dejé documentado en el README, porque es una diferencia real
entre un JSON y una base de datos y no un error que haya que esconder.

**Un test mío estaba mal escrito.** `test_eliminar_es_logico` fallaba
buscando que el número de lote no apareciera en la página. Fallaba
siempre, aunque el borrado funcionara bien: el mensaje de éxito dice
«Lote L-1180 dado de baja», así que el texto aparecía igual. Lo corregí
para revisar la lista del contexto en vez del HTML completo. El código
nunca estuvo malo; la prueba sí.

**El `User` de Django ya cifra las contraseñas.** Lo verifiqué en vez de
asumirlo:
`SesionTest.test_la_contrasena_no_se_guarda_en_texto_plano` comprueba que
el campo empieza con `pbkdf2_`. Por eso no hay ningún modelo propio de
usuarios, y las contraseñas de los usuarios de prueba salen del `.env`:
si estuvieran escritas en `crear_roles.py`, cualquiera que clone el
repositorio entraría como administrador.

## Resultado

```
python manage.py check                              -> sin issues
python manage.py makemigrations --check --dry-run   -> No changes detected
python manage.py test                               -> Ran 29 tests ... OK
```

---

# Parte 2 · ES1 (antecedente)

## Qué herramienta usé y para qué

Usé Claude. La consulté para ordenar el `plan.md` y revisar la estructura
del proyecto Django antes de armarlo. Cada archivo lo revisé línea por
línea y hay partes que reescribí porque no calzaban con la evaluación.

## Qué corregí entonces

1. **Me propuso base de datos.** La Unidad 1 era sin base de datos. Dejé
   los modelos en Won't y la vista leía `datos.json` directo. *(En la Eva
   2 esto se revirtió: ahora sí hay base de datos, y el plan.md quedó
   actualizado.)*

2. **Me dejaba sólo 3 resultados.** Faltaba el caso del dato inválido.
   Lo agregué y lo puse **primero** en el `if`, porque una fecha mal
   escrita no se puede restar contra la fecha de hoy.

3. **Repetía la regla de decisión dentro de la vista.** Lo cambié para
   que `views.py` importara `clasificar_insumo` desde `solucion.py`. Esa
   decisión sigue vigente: en la Eva 2 el que importa la regla es el
   modelo, y sigue sin estar copiada en ninguna parte.

4. **Por qué recalcular si el estado ya está guardado.** Lo entendí
   probando: si sólo mostrara lo guardado, un lote registrado como verde
   seguiría verde para siempre. Es la base de la decisión de diseño de la
   Eva 2.

## Errores que encontré probando (ES1)

1. **Categoría sensible a mayúsculas:** «carnes» se marcaba inválida.
   Corregido normalizando con `.strip().capitalize()`.
2. **Fecha con espacios se marcaba inválida.** Corregido con `.strip()`
   antes de convertir.
3. **La tabla de consola mostraba el estado guardado, no el actual.**
   Corregido para que `mostrar_tabla` vuelva a clasificar cada fila.

## Tercera revisión (ES1), contra el PDF actualizado

1. **Ubicación de archivos:** moví `solucion.py` y `datos.json` junto a
   `manage.py` y saqué el parche de `sys.path.append`.
2. **Archivo `.env`:** saqué la `SECRET_KEY` de `settings.py` con
   `python-decouple` y agregué `.env`, `.env.example` y `.gitignore`.
   *(En la Eva 2 esto se amplió: ahora también la conexión a la base de
   datos y las contraseñas de los usuarios de prueba salen del `.env`.)*
