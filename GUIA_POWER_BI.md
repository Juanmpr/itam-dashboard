# Guía paso a paso: Dashboard de Inventario de Tecnología (ITAM) en Power BI

## 0. El caso de negocio (la historia que vas a contar)

**Empresa ficticia:** *Grupo Andino Retail*, 650 empleados en 5 sedes (Madrid, Barcelona, Ciudad de México, Bogotá, Lima).
**Quién pide el dashboard:** el CIO, que tiene que preparar el presupuesto de IT de 2027.
**Fecha de corte de los datos:** 31-10-2026.

**Preguntas de negocio que responde el dashboard:**

1. ¿Cuántos equipos tenemos, dónde están, cuánto valen hoy y en qué estado están?
2. ¿Cuántos equipos hay que renovar y cuánto costará? ¿Qué departamentos tienen el parque más antiguo?
3. ¿Qué fabricantes o modelos fallan más? ¿Qué sede tarda más en resolver incidencias y cumple peor el SLA?
4. ¿Estamos pagando licencias de software que nadie usa? ¿Qué renovaciones vienen en los próximos 90 días?
5. ¿Qué riesgos tenemos? (equipos sin garantía, Windows 10 sin soporte, equipos aún asignados a empleados que se fueron).

> Para tu portfolio esto es clave: **no enseñes un dashboard, enseña un problema de negocio resuelto con datos.**

---

## 1. Los datos (carpeta `datos/`)

Generados con `generar_datos.ps1` (semilla fija, siempre salen iguales). Todo es ficticio, también los fabricantes.

| Tabla | Filas | Tipo | Contenido |
|---|---|---|---|
| `Activos` | 2.600 | Hechos + dimensión | Cada equipo: tipo, fabricante, gama, compra, coste, garantía, estado, SO… |
| `Incidencias` | 5.687 | Hechos | Tickets de soporte por activo: fechas, categoría, prioridad, horas, coste |
| `Licencias` | 18 | Hechos | Software: compradas, asignadas, usuarios activos 30 días, coste, renovación |
| `Empleados` | 650 | Dimensión | Empleado, puesto, alta/baja |
| `Departamentos` | 8 | Dimensión | Departamento y centro de coste |
| `Ubicaciones` | 5 | Dimensión | Sede, ciudad, país, lat/long (para el mapa) |
| `Proveedores` | 4 | Dimensión | Proveedor y tipo |
| `SLA` | 4 | Dimensión | Horas objetivo por prioridad |

Los textos van sin tildes a propósito (`Portatil`, `Critica`…): arreglarlos en Power Query es un buen paso de limpieza que mostrar (ver 2.3).

---

## 2. Power Query (ETL)

### 2.1 Importar
`Inicio > Obtener datos > Texto/CSV` → selecciona cada CSV → **Origen del archivo: 65001: Unicode (UTF-8)** → **Transformar datos** (no "Cargar" directamente).

> Truco pro: guarda los CSV en una carpeta y usa `Obtener datos > Carpeta` + un parámetro `RutaDatos`. Así quien descargue tu repo solo cambia el parámetro.

### 2.2 Tipos de datos (revísalos uno a uno)
- IDs (`ActivoID`, `EmpleadoID`, `LicenciaID`…): **Texto**. `DeptoID`, `UbicacionID`, `ProveedorID`: **Número entero**.
- Fechas (`FechaCompra`, `FinGarantia`, `FechaApertura`, `FechaCierre`, `FechaAlta`, `FechaBaja`, `FechaRenovacion`): **Fecha**.
- Importes y horas: **Número entero**.
- `Latitud` / `Longitud`: clic derecho en la columna > **Cambiar tipo > Usar configuración regional… > Número decimal / Inglés (Estados Unidos)**. Si tu Power BI está en español y no haces esto, `40.4168` se convierte en `404168`.

### 2.3 Limpieza que vale la pena enseñar
- **Reemplazar valores** para recuperar tildes: `Portatil→Portátil`, `Movil→Móvil`, `Critica→Crítica`, `Bateria→Batería`, `Basica→Básica`, `Estandar→Estándar`, `En reparacion→En reparación`, `Direccion→Dirección`, `Atencion al Cliente→Atención al Cliente`, `Espana→España`, `Mexico→México`, `Peru→Perú`, `Bogota→Bogotá`.
  ⚠️ Si cambias `Critica` en `Incidencias`, cámbialo también en `SLA` (y lo mismo en las fórmulas DAX de esta guía, que usan los valores sin tilde).
- Renombra las consultas con nombres limpios y **desactiva la carga** de cualquier consulta auxiliar.

---

## 3. Modelo de datos (estrella)

### 3.1 Tabla calendario (`Modelado > Nueva tabla`)

```DAX
Calendario =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2018, 1, 1 ), DATE ( 2026, 12, 31 ) ),
    "Año", YEAR ( [Date] ),
    "MesNum", MONTH ( [Date] ),
    "Mes", FORMAT ( [Date], "mmm" ),
    "AñoMes", FORMAT ( [Date], "yyyy-mm" ),
    "Trimestre", "T" & QUARTER ( [Date] )
)
```
- Márcala como **tabla de fechas** (`Herramientas de tabla > Marcar como tabla de fechas` → columna `Date`).
- Ordena `Mes` por `MesNum` (`Herramientas de columna > Ordenar por columna`).

### 3.2 Relaciones (vista Modelo)

| Desde (muchos) | Hacia (uno) | Activa |
|---|---|---|
| `Incidencias[ActivoID]` | `Activos[ActivoID]` | ✅ |
| `Incidencias[Prioridad]` | `SLA[Prioridad]` | ✅ |
| `Incidencias[FechaApertura]` | `Calendario[Date]` | ✅ |
| `Activos[FechaCompra]` | `Calendario[Date]` | ❌ **inactiva** |
| `Activos[EmpleadoID]` | `Empleados[EmpleadoID]` | ✅ |
| `Activos[DeptoID]` | `Departamentos[DeptoID]` | ✅ |
| `Activos[UbicacionID]` | `Ubicaciones[UbicacionID]` | ✅ |
| `Activos[ProveedorID]` | `Proveedores[ProveedorID]` | ✅ |
| `Licencias[DeptoID]` | `Departamentos[DeptoID]` | ✅ |

Todas 1:* con filtro en una sola dirección.

**¿Por qué la de `FechaCompra` es inactiva?** Porque si no, el calendario llegaría a `Incidencias` por dos caminos (directo y a través de `Activos`) y el modelo sería ambiguo. La activamos solo cuando la necesitamos con `USERELATIONSHIP`. **Esto es exactamente lo que un entrevistador te preguntará — tenlo claro.**

Extra: oculta en la vista de informe todas las columnas ID y claves foráneas (clic derecho > Ocultar). Un modelo limpio en la captura del README suma puntos.

### 3.3 Tabla de medidas
`Inicio > Escribir datos` → crea una tabla vacía llamada `_Medidas`. Mete ahí todas las medidas y organízalas en **carpetas de visualización** (Inventario, Ciclo de vida, Soporte, Licencias).

---

## 4. Columnas calculadas

### En `Activos`
```DAX
Edad (años) = DATEDIFF ( Activos[FechaCompra], DATE ( 2026, 10, 31 ), DAY ) / 365.25

Fin Vida Útil = EDATE ( Activos[FechaCompra], 12 * Activos[VidaUtilAnios] )

Es Operativo = NOT ( Activos[Estado] IN { "Retirado", "Extraviado" } )

Requiere Renovación = Activos[Es Operativo] && Activos[Fin Vida Útil] <= DATE ( 2026, 10, 31 )

Situación Garantía =
IF ( Activos[FinGarantia] >= DATE ( 2026, 10, 31 ), "En garantía", "Fuera de garantía" )

Valor Contable =
Activos[CosteCompra] * MAX ( 0, 1 - Activos[Edad (años)] / Activos[VidaUtilAnios] )

Rango Edad =
SWITCH (
    TRUE (),
    Activos[Edad (años)] < 1, "0-1 años",
    Activos[Edad (años)] < 3, "1-3 años",
    Activos[Edad (años)] < 5, "3-5 años",
    "5+ años"
)
```
(Ordena `Rango Edad` con una columna auxiliar `Orden Rango` 1-4 si el orden alfabético no te encaja).

### En `Incidencias`
```DAX
Cumple SLA =
IF (
    NOT ISBLANK ( Incidencias[HorasResolucion] ),
    IF ( Incidencias[HorasResolucion] <= RELATED ( SLA[HorasSLA] ), 1, 0 )
)

Cobertura =
IF ( Incidencias[FechaApertura] <= RELATED ( Activos[FinGarantia] ), "Con garantía", "Sin garantía" )
```
Truco: `Cumple SLA` devuelve 1/0/BLANK, así que el % de cumplimiento es simplemente un `AVERAGE` (las abiertas no cuentan).

---

## 5. Medidas DAX

```DAX
-- ===== Parámetro =====
Fecha Corte = DATE ( 2026, 10, 31 )

-- ===== Inventario =====
Activos Totales = COUNTROWS ( Activos )

Activos Operativos = CALCULATE ( [Activos Totales], Activos[Es Operativo] = TRUE () )

Valor Compra Parque = CALCULATE ( SUM ( Activos[CosteCompra] ), Activos[Es Operativo] = TRUE () )

Valor Contable Parque = CALCULATE ( SUM ( Activos[Valor Contable] ), Activos[Es Operativo] = TRUE () )

% Depreciado = 1 - DIVIDE ( [Valor Contable Parque], [Valor Compra Parque] )

Tasa de Uso =
DIVIDE (
    CALCULATE ( [Activos Totales], Activos[Estado] = "Asignado" ),
    CALCULATE ( [Activos Totales], Activos[Estado] IN { "Asignado", "En stock" } )
)

-- ===== Ciclo de vida y riesgo =====
% Fuera de Garantía =
VAR corte = [Fecha Corte]
RETURN
    DIVIDE (
        CALCULATE ( [Activos Operativos], Activos[FinGarantia] < corte ),
        [Activos Operativos]
    )

Activos a Renovar = CALCULATE ( [Activos Totales], Activos[Requiere Renovación] = TRUE () )

% a Renovar = DIVIDE ( [Activos a Renovar], [Activos Operativos] )

Coste Reposición Estimado =
CALCULATE ( SUM ( Activos[CosteCompra] ), Activos[Requiere Renovación] = TRUE () )

Equipos Windows 10 = CALCULATE ( [Activos Operativos], Activos[SistemaOperativo] = "Windows 10" )

Activos de Empleados de Baja = CALCULATE ( [Activos Operativos], Empleados[EstadoEmpleado] = "Baja" )

-- ===== Compras (relación inactiva) =====
Inversión en Compras =
CALCULATE (
    SUM ( Activos[CosteCompra] ),
    USERELATIONSHIP ( Calendario[Date], Activos[FechaCompra] )
)

Inversión YTD = CALCULATE ( [Inversión en Compras], DATESYTD ( Calendario[Date] ) )

-- ===== Soporte =====
Incidencias = COUNTROWS ( Incidencias )

Incidencias Abiertas = CALCULATE ( [Incidencias], ISBLANK ( Incidencias[FechaCierre] ) )

MTTR (h) = AVERAGE ( Incidencias[HorasResolucion] )

% Cumplimiento SLA = AVERAGE ( Incidencias[Cumple SLA] )

Coste Reparaciones = SUM ( Incidencias[CosteReparacion] )

Incidencias por 100 Activos = DIVIDE ( [Incidencias], [Activos Totales] ) * 100

Incidencias Año Anterior = CALCULATE ( [Incidencias], SAMEPERIODLASTYEAR ( Calendario[Date] ) )

% Var Incidencias =
DIVIDE ( [Incidencias] - [Incidencias Año Anterior], [Incidencias Año Anterior] )

-- ===== Licencias =====
Licencias Compradas = SUM ( Licencias[LicenciasCompradas] )

Usuarios Activos 30d = SUM ( Licencias[UsuariosActivos30d] )

% Uso Real Licencias = DIVIDE ( [Usuarios Activos 30d], [Licencias Compradas] )

Coste Anual Licencias =
SUMX ( Licencias, Licencias[LicenciasCompradas] * Licencias[CosteUnitarioAnual] )

Ahorro Potencial Licencias =
-- Dejamos un 10 % de margen sobre los usuarios activos
SUMX (
    Licencias,
    MAX ( 0, Licencias[LicenciasCompradas] - ROUNDUP ( Licencias[UsuariosActivos30d] * 1.1, 0 ) )
        * Licencias[CosteUnitarioAnual]
)

Renovaciones Próx. 90 días =
VAR corte = [Fecha Corte]
RETURN
    CALCULATE (
        COUNTROWS ( Licencias ),
        Licencias[FechaRenovacion] > corte,
        Licencias[FechaRenovacion] <= corte + 90
    )

-- ===== Títulos dinámicos (detalle pro) =====
Título Soporte =
"Soporte · " & FORMAT ( [Incidencias], "#,0" ) & " incidencias · SLA "
    & FORMAT ( [% Cumplimiento SLA], "0%" )
```

Formatos: importes en € sin decimales, porcentajes con 0–1 decimal, `MTTR (h)` con 1 decimal.

> Nota: como la relación de `FechaCompra` está inactiva, el filtro de fechas **no** afecta a las medidas de inventario (son una "foto" a la fecha de corte), pero sí a las de incidencias e inversión. Explícalo en un tooltip o en la página de "Acerca de".

---

## 6. Diseño de páginas

Importa el tema: `Vista > Temas > Examinar temas` → `tema_itam.json`. Lienzo 16:9 (1280×720).

Estructura común a todas las páginas: **barra izquierda** (logo/título + navegación con botones) · **franja superior de KPIs** · **2–3 visuales principales** · segmentadores (Sede, Departamento, Tipo de activo) en un **panel desplegable con marcadores**.

### Página 1 · Resumen ejecutivo
```
┌──────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│      │ Activos   │ Valor     │ % Fuera   │ Activos a │ % SLA     │ Ahorro    │
│ NAV  │ operativ. │ contable  │ garantía  │ renovar   │           │ licencias │
│      ├───────────┴───────────┴───────┬───┴───────────┴───────────┴───────────┤
│      │ Mapa: activos por sede         │ Barras: activos por tipo y estado    │
│      │ (burbuja = Activos Operativos) │ (apiladas)                           │
│      ├────────────────────────────────┼──────────────────────────────────────┤
│      │ Columnas: inversión en compras │ Tarjetas de riesgo: Windows 10 ·     │
│      │ por año                        │ asignados a ex-empleados · extraviados│
└──────┴────────────────────────────────┴──────────────────────────────────────┘
```

### Página 2 · Ciclo de vida y renovación
- **Matriz con formato condicional (mapa de calor):** Departamento × Rango Edad → `% a Renovar`.
- **Barras:** `Coste Reposición Estimado` por departamento (este es el número para el presupuesto 2027).
- **Anillo:** Situación de garantía.
- **Tabla de detalle:** activos a renovar (ID, tipo, modelo, empleado, edad, SO) con formato condicional en Windows 10.

### Página 3 · Soporte e incidencias
- **Líneas:** incidencias por `AñoMes` + línea de año anterior.
- **Barras horizontales:** `Incidencias por 100 Activos` por Modelo (filtra TipoActivo = Portátil). Añade una **línea de promedio** desde el panel Análisis.
- **Columnas + línea:** `MTTR (h)` y `% Cumplimiento SLA` por sede.
- **Matriz:** Prioridad × Sede con `% Cumplimiento SLA` en formato semáforo.
- **Tarjeta:** `Coste Reparaciones` con desglose por `Cobertura`.

### Página 4 · Licencias de software
- **Barras agrupadas:** compradas vs usuarios activos 30d por software (ordenado por ahorro).
- **Medidor:** `% Uso Real Licencias` con objetivo 85 %.
- **Tabla:** renovaciones próximas (software, fecha, coste anual, % uso) con barra de datos en el ahorro.

### Página 5 · Ficha de activo (drillthrough)
Página oculta con campo de obtención de detalles `Activos[ActivoID]`: datos del equipo, historial de incidencias (tabla), coste acumulado. Desde cualquier tabla: clic derecho > Obtener detalles.

### Extras que diferencian un portfolio
- **Tooltip personalizado** (página de tamaño "Información sobre herramientas") en el mapa: MTTR, SLA e incidencias abiertas de la sede.
- **Parámetro de campo** (`Modelado > Nuevo parámetro > Campos`) para cambiar el eje entre Sede / Departamento / Fabricante.
- **Página "Acerca de"**: objetivo, fuentes, fecha de corte, definiciones de KPI.
- Textos con **conclusión, no descripción**: en vez de "Incidencias por sede", pon "Lima tarda casi el doble en resolver incidencias".

---

## 7. Lo que deberías descubrir (comprueba que te cuadra)

Valores validados sobre los CSV generados. Si no te salen, revisa relaciones y filtros.

| # | Hallazgo | Cifra aprox. | Recomendación para el CIO |
|---|---|---|---|
| 1 | Parque operativo | 1.994 activos | — |
| 2 | Activos fuera de garantía | 72 % | Ampliar garantías en gama Pro / leasing |
| 3 | Activos al final de su vida útil | 635 | Plan de renovación escalonado 2027 |
| 4 | **Operaciones** tiene el parque más viejo | 50 % a renovar vs ~30 % resto | Priorizar Operaciones en el presupuesto |
| 5 | Portátiles **Valtek Básica** fallan mucho más | ~800 incidencias/100 equipos vs ~250–330 del resto | Dejar de comprar ese modelo |
| 6 | **Lima** resuelve más lento | MTTR ~118 h vs 63–75 h; SLA 24 % vs 50–63 % | Revisar dotación de soporte en Lima |
| 7 | Equipos con **Windows 10** (sin soporte desde oct-2025) | 130 | Riesgo de seguridad: migrar o renovar |
| 8 | Activos aún asignados a **empleados de baja** | 142 | Proceso de recuperación en el offboarding |
| 9 | Coste de reparaciones | ~472 k€, todo en equipos sin garantía | Refuerza el hallazgo 2 |
| 10 | Licencias: coste anual / ahorro potencial | ~986 k€ / ~148 k€ (≈15 %) | Ajustar Zoom, Adobe, VPN, Visio, AutoCAD… |
| 11 | Renovaciones de licencias en 90 días | 6 | Renegociar antes de renovar |

---

## 8. Atajo: abrir el proyecto ya generado (`ITAM_PowerBI/`)

La carpeta `ITAM_PowerBI` es un **proyecto de Power BI (.pbip)** con todo lo de los apartados 2–6 ya hecho: Power Query, modelo, relaciones, columnas, medidas y 5 páginas.

1. Power BI Desktop actualizado (2025 o posterior). Si al abrir te avisa de formatos en vista previa, actívalos en `Archivo > Opciones > Características en versión preliminar`: **Guardar como proyecto de Power BI (.pbip)** y **Almacenar informes con el formato PBIR**. Reinicia Desktop.
2. Doble clic en `ITAM_PowerBI/ITAM.pbip`.
3. Pulsa **Actualizar**. Si da error de ruta: `Transformar datos > Editar parámetros > RutaDatos` → la ruta de tu carpeta `datos`, terminada en `\`. (O mueve la carpeta y vuelve a ejecutar `construir_pbip.ps1`, que reescribe la ruta solo).
4. Importa el tema: `Vista > Temas > Examinar temas > tema_itam.json`.
5. Repasa cada página: ajusta tamaños, colores de las tarjetas (formato condicional rojo/verde), etiquetas de datos y añade las capturas al README.
6. `Archivo > Guardar como` → `.pbix` si también quieres el archivo clásico.

Si algún visual sale con error o vacío, bórralo y vuelve a crearlo arrastrando los mismos campos: el modelo y las medidas no se ven afectados. Para regenerar el informe desde cero: `powershell -ExecutionPolicy Bypass -File .\construir_pbip.ps1` (⚠️ sobrescribe las páginas, no los cambios del modelo).

---

## 9. Checklist antes de publicar

- [ ] Sin errores en Power Query y tipos correctos.
- [ ] Modelo en estrella, IDs ocultos, relación inactiva documentada.
- [ ] Medidas en `_Medidas` con carpetas y formato.
- [ ] Navegación con botones, interacciones entre visuales revisadas (`Formato > Editar interacciones`).
- [ ] Títulos con conclusiones y página "Acerca de".
- [ ] Probado con filtros extremos (una sola sede, un solo tipo) sin visuales rotos.
- [ ] Capturas de cada página + GIF corto navegando (ScreenToGif es gratis).
- [ ] Publicado: **Publicar en la web** desde Power BI Service (solo porque los datos son ficticios) o, si no tienes cuenta de trabajo, sube el `.pbix` y capturas a GitHub.
- [ ] README completado (plantilla en `README_portfolio.md`).
