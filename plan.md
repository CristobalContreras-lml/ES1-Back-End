# plan.md · Monitoreo de vencimiento de insumos

**Asignatura:** TI3V41 · Programación Back End · Unidad 1 · ES1
**Estudiante:** Cristóbal Contreras
**Docente:** Juan Pablo Díaz S.

---

## 1. Apartado de negocio

### Problema

En la bodega de una cocina central (banquetería / cadena de restaurantes chicos) se manejan
cientos de insumos con vidas útiles distintas. Cada semana se botan cajas de productos caros
—quesos, carnes, salsas preparadas— porque quedaron al fondo del estante o debajo de lotes más
nuevos y nadie vio que se estaban venciendo. Se rompe la regla básica de rotación FIFO
(*First In, First Out*). A quien le molesta: al jefe de cocina, que descubre la pérdida cuando ya
no hay nada que hacer, y al dueño, que paga esa merma. Hoy el control se lleva en un cuaderno o
en la memoria de quien recibe la mercadería.

### Solución

El programa recibe los datos de un lote que entra a bodega y responde de inmediato con un
semáforo: rojo si está vencido, amarillo si vence dentro del plazo de alerta de su categoría,
verde si está vigente, y un cuarto resultado cuando el dato ingresado no tiene sentido. Todos los
lotes quedan guardados y se muestran en una pantalla web ordenados por fecha de vencimiento, de
modo que lo primero que se ve es lo que hay que usar primero.

### Alcance

**Entra:** ingreso de lotes por consola, cálculo de los días que faltan para el vencimiento,
clasificación en los 4 resultados, guardado en `datos.json`, resumen en tabla con `tabulate` y una
sola pantalla web en Django que lee ese JSON.

**No entra:** base de datos, modelos ni migraciones (eso es Unidad 2), cuentas de usuario, API,
formulario web para ingresar datos, lectura de códigos de barra.

### Priorización MoSCoW

**Must · imprescindible (esto es el MVP y es lo único que programé)**

1. Pedir por consola los datos del lote: nombre, categoría, número de lote, cantidad y fecha de vencimiento.
2. Calcular de forma dinámica cuántos días faltan para el vencimiento, comparando contra la fecha de hoy.
3. Clasificar el lote en los 4 resultados, cada uno con un mensaje que explica el motivo.
4. Guardar cada decisión en `datos.json`.
5. Mostrar el inventario ordenado por fecha de vencimiento: tabla con `tabulate` en consola y panel semáforo en la pantalla web.

**Should · importante (queda escrito, no programado)**

- Filtro en la pantalla para ver solo los lotes críticos (rojos y amarillos).
- Búsqueda por nombre de insumo o por número de lote.
- Corregir o dar de baja un lote mal ingresado sin editar el JSON a mano.

**Could · deseable**

- Exportar el listado de vencidos a CSV o PDF.
- Aviso por correo cuando un lote pasa a rojo.
- Historial de mermas para medir cuánta plata se perdió en el mes.

**Won't · fuera por ahora**

- Modelos `Categoria` e `Insumo` con base de datos SQL. La idea original del proyecto los incluía,
  pero esta evaluación es sin base de datos: se dejan para la Unidad 2.
- Login y roles de usuario.
- Escaneo de códigos de barra con la cámara.
- Pronósticos automáticos de compra o integración con proveedores.

---

## 2. Apartado técnico

### Datos de entrada

| Dato | Tipo | Ejemplo | Cómo se pide |
|---|---|---|---|
| Nombre del insumo | texto (`str`) | Queso mantecoso | `input()` |
| Categoría | texto (`str`) | Lacteos | `input()`, debe estar en la lista de categorías |
| Número de lote | texto (`str`) | L-1180 | `input()` |
| Cantidad | número entero (`int`) | 12 | `input()` convertido con `int()` |
| Fecha de vencimiento | texto con formato AAAA-MM-DD (`str`) | 2026-08-22 | `input()`, se transforma a fecha con `datetime` |

Dato calculado: **días restantes** = fecha de vencimiento − fecha de hoy.

Cada categoría tiene su propio plazo de alerta, porque no es lo mismo una lechuga que una caja de
bolsas: Verduras 3 días, Carnes 5, Lácteos 7, Salsas 10, Empaques 30.

### Regla de decisión · 4 resultados

La decisión depende de tres datos: la categoría, la cantidad y los días que faltan.

| # | Resultado | Cuándo ocurre | Mensaje |
|---|---|---|---|
| 1 | **INVÁLIDO** | La fecha no se puede leer **o** la cantidad es 0 o negativa **o** la categoría no está en la lista | Dato inválido: explica qué se esperaba |
| 2 | **ROJO** (rechazo 1) | Los días restantes son 0 o menos | Rechazado: vencido, se registra como merma |
| 3 | **AMARILLO** (rechazo 2) | Los días restantes son menores o iguales al plazo de alerta de su categoría **y** la cantidad es válida | Rechazado para bodega: sacar de inmediato a producción por FIFO |
| 4 | **VERDE** (aceptación) | Los días restantes superan el plazo de alerta de su categoría | Aceptado: se guarda detrás de los lotes más antiguos |

El caso inválido va **primero** en el `if`. Si quedara al final nunca se alcanzaría a revisar,
porque una fecha ilegible no se puede comparar con nada.

### Paquete externo

`tabulate`, instalado con `pip install tabulate`. Se usa para imprimir el resumen del inventario
como una tabla con bordes, ordenada por fecha de vencimiento, en vez de un `print()` por línea.
Queda anotado en `requirements.txt`.

### Pantalla web

- **Dirección:** `/` (la raíz del sitio), servida por la vista `resumen` de la app `core`.
- **Qué muestra:** cuatro contadores del semáforo (vencidos, por vencer, vigentes, con dato
  inválido), un aviso con las unidades vencidas que siguen en bodega, y la lista de lotes ordenada
  por fecha de vencimiento. Cada lote muestra en grande los días que le quedan y el motivo.
- **De dónde saca los datos:** la vista abre `datos.json` y vuelve a clasificar cada lote con la
  fecha de hoy, importando la misma función de `solucion.py`. Así el semáforo cambia solo con el
  paso de los días, sin tocar el archivo.
