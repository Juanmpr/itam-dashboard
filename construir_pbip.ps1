# ================================================================
#  Construye el proyecto Power BI (PBIP) en .\ITAM_PowerBI
#  - Ajusta la ruta de datos del modelo (parametro RutaDatos)
#  - Convierte la sangria de los .tmdl a tabuladores
#  - Genera el informe en formato PBIR (paginas y visuales)
#  Uso: powershell -ExecutionPolicy Bypass -File .\construir_pbip.ps1
# ================================================================
$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot 'ITAM_PowerBI'
$sm = Join-Path $root 'ITAM.SemanticModel'
$rp = Join-Path $root 'ITAM.Report'
$utf8 = New-Object System.Text.UTF8Encoding $false

function WriteText($path, $text) {
    New-Item -ItemType Directory -Force (Split-Path $path) | Out-Null
    [IO.File]::WriteAllText($path, ($text -replace "`r?`n", "`r`n"), $utf8)
}
function WriteJson($path, $obj) { WriteText $path ($obj | ConvertTo-Json -Depth 60) }

# ---------- 1. Archivos raiz ----------
WriteJson (Join-Path $root 'ITAM.pbip') ([ordered]@{
    '$schema' = 'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json'
    version = '1.0'
    artifacts = @(@{ report = @{ path = 'ITAM.Report' } })
    settings = @{ enableAutoRecovery = $true }
})
WriteJson (Join-Path $sm 'definition.pbism') ([ordered]@{
    '$schema' = 'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json'
    version = '4.0'
    settings = @{}
})
WriteJson (Join-Path $rp 'definition.pbir') ([ordered]@{
    '$schema' = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json'
    version = '4.0'
    datasetReference = @{ byPath = @{ path = '../ITAM.SemanticModel' } }
})
WriteText (Join-Path $root '.gitignore') "**/.pbi/localSettings.json`n**/.pbi/cache.abf`n"

# ---------- 2. Modelo: ruta de datos + tabuladores ----------
$ruta = (Join-Path $PSScriptRoot 'datos') + '\'
Get-ChildItem (Join-Path $sm 'definition') -Recurse -Filter *.tmdl | ForEach-Object {
    $t = [IO.File]::ReadAllText($_.FullName)
    $t = [regex]::Replace($t, '(?m)^(expression RutaDatos = )"[^"]*"', { param($mt) $mt.Groups[1].Value + '"' + $ruta + '"' })
    $lines = $t -split "`r?`n" | ForEach-Object {
        if ($_ -match '^( +)(.*)$') { ("`t" * [math]::Floor($matches[1].Length / 4)) + (' ' * ($matches[1].Length % 4)) + $matches[2] } else { $_ }
    }
    WriteText $_.FullName ($lines -join "`n")
}

# ---------- 3. Informe (PBIR) ----------
$def = Join-Path $rp 'definition'
if (Test-Path (Join-Path $def 'pages')) { Remove-Item (Join-Path $def 'pages') -Recurse -Force }
$S_VIS  = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json'
$S_PAGE = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.4.0/schema.json'

WriteJson (Join-Path $def 'version.json') ([ordered]@{
    '$schema' = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json'
    version = '2.0.0'
})
WriteJson (Join-Path $def 'report.json') ([ordered]@{
    '$schema' = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/2.0.0/schema.json'
    themeCollection = @{}
})

# --- helpers ---
function Lit($v) { @{ expr = @{ Literal = @{ Value = $v } } } }
function Str($s) { Lit ("'" + $s.Replace("'", "''") + "'") }
function Color($hex) { @{ solid = @{ color = (Str $hex) } } }
function Col($t, $c) { [ordered]@{ field = @{ Column = [ordered]@{ Expression = @{ SourceRef = @{ Entity = $t } }; Property = $c } }; queryRef = "$t.$c"; nativeQueryRef = $c } }
function Mea($m) { [ordered]@{ field = @{ Measure = [ordered]@{ Expression = @{ SourceRef = @{ Entity = '_Medidas' } }; Property = $m } }; queryRef = "_Medidas.$m"; nativeQueryRef = $m } }
function CatFilter($t, $c, $valueLiteral) {
    [ordered]@{
        name = ('f_' + ($c -replace '\W', ''))
        field = @{ Column = [ordered]@{ Expression = @{ SourceRef = @{ Entity = $t } }; Property = $c } }
        type = 'Categorical'
        filter = [ordered]@{
            Version = 2
            From = @(@{ Name = 'a'; Entity = $t; Type = 0 })
            Where = @(@{ Condition = @{ In = [ordered]@{
                Expressions = @(@{ Column = [ordered]@{ Expression = @{ SourceRef = @{ Source = 'a' } }; Property = $c } })
                Values = @(, @(@{ Literal = @{ Value = $valueLiteral } }))
            } } })
        }
    }
}

$script:z = 1000
function NewVisual($page, $name, $type, $x, $y, $w, $h, $roles, $title, $extra) {
    $script:z += 10
    $visual = [ordered]@{ visualType = $type }
    if ($roles) {
        $qs = [ordered]@{}
        foreach ($k in $roles.Keys) { $qs[$k] = @{ projections = @($roles[$k]) } }
        $visual.query = [ordered]@{ queryState = $qs }
        if ($extra -and $extra.sortBy) {
            $visual.query.sortDefinition = @{ sort = @(@{ field = $extra.sortBy.field; direction = $extra.sortDir }) }
        }
    }
    if ($extra -and $extra.objects) { $visual.objects = $extra.objects }
    $vco = [ordered]@{}
    if ($title) { $vco.title = @(@{ properties = [ordered]@{ show = (Lit 'true'); text = (Str $title) } }) }
    if ($extra -and $extra.vco) { foreach ($k in $extra.vco.Keys) { $vco[$k] = $extra.vco[$k] } }
    if ($vco.Count) { $visual.visualContainerObjects = $vco }
    $visual.drillFilterOtherVisuals = $true
    $v = [ordered]@{
        '$schema' = $S_VIS
        name = $name
        position = [ordered]@{ x = $x; y = $y; z = $script:z; height = $h; width = $w; tabOrder = $script:z }
        visual = $visual
    }
    if ($extra -and $extra.filters) { $v.filterConfig = @{ filters = @($extra.filters) } }
    WriteJson (Join-Path $def "pages\$page\visuals\$name\visual.json") $v
}

function TextBox($page, $name, $x, $y, $w, $h, $runs) {
    $paras = @($runs | ForEach-Object { @{ textRuns = @(@{ value = $_[0]; textStyle = [ordered]@{ fontSize = $_[1]; fontWeight = $_[2]; color = $_[3] } }) } })
    NewVisual $page $name 'textbox' $x $y $w $h $null $null @{ objects = @{ general = @(@{ properties = @{ paragraphs = $paras } }) } }
}

$pages = [ordered]@{
    resumen   = 'Resumen ejecutivo'
    ciclo     = 'Ciclo de vida'
    soporte   = 'Soporte'
    licencias = 'Licencias'
    acerca    = 'Acerca de'
}

function NavBar($page) {
    NewVisual $page 'nav_fondo' 'shape' 0 0 150 720 $null $null @{ objects = [ordered]@{
        shape = @(@{ properties = @{ tileShape = (Str 'rectangle') } })
        fill = @(@{ properties = [ordered]@{ show = (Lit 'true'); fillColor = (Color '#0F172A') } })
        outline = @(@{ properties = @{ show = (Lit 'false') } })
    } }
    TextBox $page 'nav_logo' 10 18 130 60 @(@('ITAM', '20pt', 'bold', '#FFFFFF'), @('Grupo Andino Retail', '9pt', 'normal', '#94A3B8'))
    $i = 0
    foreach ($p in $pages.Keys) {
        $activo = ($p -eq $page)
        $fill = if ($activo) { '#2563EB' } else { '#1E293B' }
        NewVisual $page ("nav_$p") 'actionButton' 10 (100 + $i * 50) 130 40 $null $null @{
            objects = [ordered]@{
                icon = @(@{ properties = @{ shapeType = (Str 'blank') }; selector = @{ id = 'default' } })
                text = @(@{ properties = [ordered]@{ show = (Lit 'true'); text = (Str $pages[$p]); fontColor = (Color '#FFFFFF'); fontSize = (Lit '11D') }; selector = @{ id = 'default' } })
                fill = @(@{ properties = [ordered]@{ show = (Lit 'true'); fillColor = (Color $fill); transparency = (Lit '0D') }; selector = @{ id = 'default' } })
                outline = @(@{ properties = @{ show = (Lit 'false') }; selector = @{ id = 'default' } })
            }
            vco = @{ visualLink = @(@{ properties = [ordered]@{ show = (Lit 'true'); type = (Str 'PageNavigation'); navigationSection = (Str $p) } }) }
        }
        $i++
    }
}

function Header($page, $titulo, $sub) {
    TextBox $page 'titulo' 165 8 600 60 @(@($titulo, '18pt', 'bold', '#0F172A'), @($sub, '10pt', 'normal', '#64748B'))
    NewVisual $page 'seg_sede' 'slicer' 785 12 155 56 ([ordered]@{ Values = @(Col 'Ubicaciones' 'Sede') }) $null @{ objects = @{ data = @(@{ properties = @{ mode = (Str 'Dropdown') } }) } }
    NewVisual $page 'seg_depto' 'slicer' 948 12 155 56 ([ordered]@{ Values = @(Col 'Departamentos' 'Departamento') }) $null @{ objects = @{ data = @(@{ properties = @{ mode = (Str 'Dropdown') } }) } }
    NewVisual $page 'seg_tipo' 'slicer' 1111 12 155 56 ([ordered]@{ Values = @(Col 'Activos' 'TipoActivo') }) $null @{ objects = @{ data = @(@{ properties = @{ mode = (Str 'Dropdown') } }) } }
}

function KpiRow($page, $measures) {
    $n = $measures.Count; $gap = 10; $w = [math]::Floor((1100 - $gap * ($n - 1)) / $n); $i = 0
    foreach ($m in $measures) {
        NewVisual $page ("kpi_$i") 'card' (165 + $i * ($w + $gap)) 78 $w 92 ([ordered]@{ Values = @(Mea $m) }) $null $null
        $i++
    }
}

function WritePage($p) {
    WriteJson (Join-Path $def "pages\$p\page.json") ([ordered]@{
        '$schema' = $S_PAGE; name = $p; displayName = $pages[$p]; displayOption = 'FitToPage'; height = 720; width = 1280
    })
}

# ===== Pagina 1: Resumen ejecutivo =====
$p = 'resumen'; WritePage $p; NavBar $p
Header $p 'Inventario de tecnología · Resumen ejecutivo' 'Foto del parque a 31/10/2026 · los filtros de fecha solo afectan a incidencias e inversión'
KpiRow $p @('Activos Operativos', 'Valor Contable Parque', '% Fuera de Garantía', 'Activos a Renovar', '% Cumplimiento SLA', 'Ahorro Potencial Licencias')
$m = Mea 'Activos Operativos'
NewVisual $p 'activos_sede' 'clusteredBarChart' 165 180 545 265 ([ordered]@{ Category = @(Col 'Ubicaciones' 'Sede'); Y = @($m) }) 'Madrid concentra el 30 % del parque' @{ sortBy = $m; sortDir = 'Descending' }
NewVisual $p 'activos_tipo' 'barChart' 720 180 545 265 ([ordered]@{ Category = @(Col 'Activos' 'TipoActivo'); Y = @((Mea 'Activos en Uso'), (Mea 'Activos en Stock'), (Mea 'Activos en Reparación')) }) 'Portátiles y monitores son el 61 % del parque' @{ sortBy = (Mea 'Activos en Uso'); sortDir = 'Descending' }
NewVisual $p 'inversion_anual' 'clusteredColumnChart' 165 455 545 255 ([ordered]@{ Category = @(Col 'Calendario' 'Año'); Y = @(Mea 'Inversión en Compras') }) 'Inversión en compras estable, unos 400 k€ al año' $null
NewVisual $p 'riesgos' 'multiRowCard' 720 455 545 255 ([ordered]@{ Values = @((Mea 'Equipos Windows 10'), (Mea 'Activos de Empleados de Baja'), (Mea 'Activos Extraviados'), (Mea 'Incidencias Abiertas')) }) 'Riesgos a vigilar' $null

# ===== Pagina 2: Ciclo de vida =====
$p = 'ciclo'; WritePage $p; NavBar $p
Header $p 'Ciclo de vida y renovación' 'Qué equipos hay que renovar en 2027 y cuánto costará'
KpiRow $p @('Activos a Renovar', '% a Renovar', 'Coste Reposición Estimado', 'Edad Media (años)', 'Equipos Windows 10', '% Fuera de Garantía')
NewVisual $p 'matriz_edad' 'pivotTable' 165 180 545 265 ([ordered]@{ Rows = @(Col 'Departamentos' 'Departamento'); Columns = @(Col 'Activos' 'Rango Edad'); Values = @(Mea 'Activos Operativos') }) 'Antigüedad del parque por departamento' $null
$m = Mea 'Coste Reposición Estimado'
NewVisual $p 'reposicion_depto' 'clusteredBarChart' 720 180 545 265 ([ordered]@{ Category = @(Col 'Departamentos' 'Departamento'); Y = @($m) }) 'Operaciones necesita la mayor inversión en renovación' @{ sortBy = $m; sortDir = 'Descending' }
NewVisual $p 'garantia' 'donutChart' 165 455 300 255 ([ordered]@{ Category = @(Col 'Activos' 'Situación Garantía'); Y = @(Mea 'Activos Operativos') }) '7 de cada 10 equipos sin garantía' $null
NewVisual $p 'tabla_renovar' 'tableEx' 475 455 790 255 ([ordered]@{ Values = @((Col 'Activos' 'ActivoID'), (Col 'Activos' 'Modelo'), (Col 'Departamentos' 'Departamento'), (Col 'Empleados' 'Empleado'), (Col 'Activos' 'SistemaOperativo'), (Col 'Activos' 'Edad (años)'), (Col 'Activos' 'CosteCompra')) }) 'Equipos a renovar' @{ filters = @(CatFilter 'Activos' 'Requiere Renovación' 'true') }

# ===== Pagina 3: Soporte =====
$p = 'soporte'; WritePage $p; NavBar $p
Header $p 'Soporte e incidencias' 'Qué falla, dónde y cuánto tardamos en resolverlo'
KpiRow $p @('Total Incidencias', 'Incidencias Abiertas', 'MTTR (h)', '% Cumplimiento SLA', 'Coste Reparaciones', '% Var Incidencias')
NewVisual $p 'tendencia' 'lineChart' 165 180 545 265 ([ordered]@{ Category = @(Col 'Calendario' 'AñoMes'); Y = @(Mea 'Total Incidencias') }) 'Evolución mensual de incidencias' $null
$m = Mea 'Incidencias por 100 Activos'
NewVisual $p 'fallos_modelo' 'clusteredBarChart' 720 180 545 265 ([ordered]@{ Category = @(Col 'Activos' 'Modelo'); Y = @($m) }) 'Los portátiles Valtek Básica fallan casi 3 veces más' @{ sortBy = $m; sortDir = 'Descending'; filters = @(CatFilter 'Activos' 'TipoActivo' "'Portátil'") }
NewVisual $p 'mttr_sede' 'lineClusteredColumnComboChart' 165 455 545 255 ([ordered]@{ Category = @(Col 'Ubicaciones' 'Sede'); Y = @(Mea 'MTTR (h)'); Y2 = @(Mea '% Cumplimiento SLA') }) 'Lima tarda casi el doble en resolver incidencias' $null
NewVisual $p 'sla_matriz' 'pivotTable' 720 455 545 255 ([ordered]@{ Rows = @(Col 'SLA' 'Prioridad'); Columns = @(Col 'Ubicaciones' 'Sede'); Values = @(Mea '% Cumplimiento SLA') }) 'Cumplimiento del SLA por prioridad y sede' $null

# ===== Pagina 4: Licencias =====
$p = 'licencias'; WritePage $p; NavBar $p
Header $p 'Licencias de software' 'Cuánto pagamos por licencias que nadie usa'
KpiRow $p @('Coste Anual Licencias', 'Ahorro Potencial Licencias', '% Uso Real Licencias', 'Renovaciones Próx. 90 días')
$m = Mea 'Licencias Compradas'
NewVisual $p 'uso_software' 'clusteredBarChart' 165 180 700 530 ([ordered]@{ Category = @(Col 'Licencias' 'Software'); Y = @($m, (Mea 'Usuarios Activos 30d')) }) 'Licencias compradas frente a usuarios activos' @{ sortBy = (Mea 'Ahorro Potencial Licencias'); sortDir = 'Descending' }
NewVisual $p 'gauge_uso' 'gauge' 875 180 390 250 ([ordered]@{ Y = @(Mea '% Uso Real Licencias'); TargetValue = @(Mea 'Objetivo Uso Licencias') }) 'Uso real frente al objetivo del 85 %' $null
NewVisual $p 'tabla_renov' 'tableEx' 875 440 390 270 ([ordered]@{ Values = @((Col 'Licencias' 'Software'), (Col 'Licencias' 'FechaRenovacion'), (Mea '% Uso Real Licencias'), (Mea 'Ahorro Potencial Licencias')) }) 'Ahorro por software y renovación' @{ sortBy = (Mea 'Ahorro Potencial Licencias'); sortDir = 'Descending' }

# ===== Pagina 5: Acerca de =====
$p = 'acerca'; WritePage $p; NavBar $p
TextBox $p 'titulo' 165 8 900 60 @(@('Acerca de este dashboard', '18pt', 'bold', '#0F172A'), @('Proyecto de portfolio · datos 100 % ficticios', '10pt', 'normal', '#64748B'))
TextBox $p 'texto' 165 90 1100 610 @(
    @('Objetivo', '13pt', 'bold', '#0F172A'),
    @('Ayudar al responsable de IT a preparar el presupuesto 2027: qué equipos renovar, dónde falla el soporte y cuánto se puede ahorrar en licencias.', '11pt', 'normal', '#334155'),
    @(' ', '8pt', 'normal', '#334155'),
    @('Datos', '13pt', 'bold', '#0F172A'),
    @('2.600 activos, 5.687 incidencias, 18 licencias y 650 empleados en 5 sedes. Fecha de corte: 31/10/2026.', '11pt', 'normal', '#334155'),
    @(' ', '8pt', 'normal', '#334155'),
    @('Definiciones', '13pt', 'bold', '#0F172A'),
    @('Activo operativo: no está retirado ni extraviado.', '11pt', 'normal', '#334155'),
    @('Valor contable: coste de compra con depreciación lineal según la vida útil del tipo de activo.', '11pt', 'normal', '#334155'),
    @('A renovar: activo operativo que ya ha superado su vida útil.', '11pt', 'normal', '#334155'),
    @('MTTR: tiempo medio de resolución en horas (solo incidencias cerradas).', '11pt', 'normal', '#334155'),
    @('Cumplimiento SLA: incidencias resueltas dentro de las horas objetivo de su prioridad.', '11pt', 'normal', '#334155'),
    @('Ahorro potencial: licencias compradas por encima de los usuarios activos de los últimos 30 días + 10 % de margen.', '11pt', 'normal', '#334155'),
    @(' ', '8pt', 'normal', '#334155'),
    @('Nota técnica', '13pt', 'bold', '#0F172A'),
    @('La relación de la fecha de compra con el calendario está inactiva y se activa con USERELATIONSHIP en las medidas de inversión, para evitar ambigüedad en el modelo.', '11pt', 'normal', '#334155')
)

WriteJson (Join-Path $def 'pages\pages.json') ([ordered]@{
    '$schema' = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json'
    pageOrder = @($pages.Keys)
    activePageName = 'resumen'
})

Write-Host "Proyecto generado en: $root"
