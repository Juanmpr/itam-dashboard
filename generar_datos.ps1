# ================================================================
#  Generador de datos ficticios - Inventario de Tecnologia (ITAM)
#  Empresa ficticia: "Grupo Andino Retail"  |  Fecha de corte: 2026-10-31
#  Uso:  powershell -ExecutionPolicy Bypass -File .\generar_datos.ps1
#  Salida: carpeta .\datos con 8 CSV (UTF-8, separador coma)
# ================================================================
$ErrorActionPreference = 'Stop'
$script:rnd = New-Object System.Random 42          # semilla fija = datos reproducibles
$corte = [datetime]'2026-10-31'
$out = Join-Path $PSScriptRoot 'datos'
New-Item -ItemType Directory -Force $out | Out-Null

function RInt([int]$a, [int]$b) { $script:rnd.Next($a, $b + 1) }
function P([double]$p) { $script:rnd.NextDouble() -lt $p }
function Pick($arr) { $arr[$script:rnd.Next(0, $arr.Count)] }
function PickW($items, $weights) {
    $tot = ($weights | Measure-Object -Sum).Sum
    $x = $script:rnd.NextDouble() * $tot; $acc = 0
    for ($i = 0; $i -lt $items.Count; $i++) { $acc += $weights[$i]; if ($x -lt $acc) { return $items[$i] } }
    return $items[-1]
}
function RandDate([datetime]$from, [datetime]$to) {
    $days = [int]($to - $from).TotalDays
    if ($days -le 0) { return $from }
    $from.AddDays($script:rnd.Next(0, $days + 1))
}
function D($d) { if ($null -eq $d) { '' } else { $d.ToString('yyyy-MM-dd') } }
function Save($name, $header, $rows) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine($header)
    foreach ($r in $rows) { [void]$sb.AppendLine($r) }
    [System.IO.File]::WriteAllText((Join-Path $out $name), $sb.ToString(), (New-Object System.Text.UTF8Encoding $true))
    Write-Host ("{0,-20} {1,6} filas" -f $name, $rows.Count)
}

# ---------------- Dimensiones fijas ----------------
$deptos = @(
    @{Id=1; N='Sistemas';            CC='CC-100'; W=6 },
    @{Id=2; N='Ventas';              CC='CC-200'; W=22},
    @{Id=3; N='Marketing';           CC='CC-300'; W=9 },
    @{Id=4; N='Finanzas';            CC='CC-400'; W=8 },
    @{Id=5; N='Recursos Humanos';    CC='CC-500'; W=5 },
    @{Id=6; N='Operaciones';         CC='CC-600'; W=25},
    @{Id=7; N='Atencion al Cliente'; CC='CC-700'; W=20},
    @{Id=8; N='Direccion';           CC='CC-800'; W=5 }
)
$sedes = @(
    @{Id=1; Sede='Oficina Central'; Ciudad='Madrid';           Pais='Espana';   Lat=40.4168;  Lon=-3.7038;  W=30},
    @{Id=2; Sede='Hub Barcelona';   Ciudad='Barcelona';        Pais='Espana';   Lat=41.3874;  Lon=2.1686;   W=18},
    @{Id=3; Sede='Oficina Mexico';  Ciudad='Ciudad de Mexico'; Pais='Mexico';   Lat=19.4326;  Lon=-99.1332; W=22},
    @{Id=4; Sede='Oficina Bogota';  Ciudad='Bogota';           Pais='Colombia'; Lat=4.7110;   Lon=-74.0721; W=17},
    @{Id=5; Sede='Oficina Lima';    Ciudad='Lima';             Pais='Peru';     Lat=-12.0464; Lon=-77.0428; W=13}
)
$proveedores = @(
    @{Id=1; N='TecnoSuministros SL';  Tipo='Mayorista'},
    @{Id=2; N='Iberdata Soluciones';  Tipo='Integrador'},
    @{Id=3; N='LatamTech Distribucion'; Tipo='Mayorista'},
    @{Id=4; N='RentaIT Leasing';      Tipo='Leasing'}
)
$sla = @(
    @{P='Critica'; H=8;   O=1},
    @{P='Alta';    H=24;  O=2},
    @{P='Media';   H=72;  O=3},
    @{P='Baja';    H=120; O=4}
)

Save 'Departamentos.csv' 'DeptoID,Departamento,CentroCoste' ($deptos | ForEach-Object { "$($_.Id),$($_.N),$($_.CC)" })
Save 'Ubicaciones.csv' 'UbicacionID,Sede,Ciudad,Pais,Latitud,Longitud' ($sedes | ForEach-Object {
    "$($_.Id),$($_.Sede),$($_.Ciudad),$($_.Pais),$($_.Lat.ToString([Globalization.CultureInfo]::InvariantCulture)),$($_.Lon.ToString([Globalization.CultureInfo]::InvariantCulture))" })
Save 'Proveedores.csv' 'ProveedorID,Proveedor,TipoProveedor' ($proveedores | ForEach-Object { "$($_.Id),$($_.N),$($_.Tipo)" })
Save 'SLA.csv' 'Prioridad,HorasSLA,OrdenPrioridad' ($sla | ForEach-Object { "$($_.P),$($_.H),$($_.O)" })

# ---------------- Empleados ----------------
$nombres = 'Ana','Luis','Maria','Carlos','Lucia','Javier','Sofia','Diego','Valentina','Andres','Camila','Jorge','Paula','Miguel','Elena','Raul','Daniela','Pablo','Laura','Sergio','Isabel','Fernando','Carmen','Ricardo','Natalia','Alejandro','Gabriela','Hugo','Marta','Tomas'
$apellidos = 'Garcia','Rodriguez','Lopez','Martinez','Gonzalez','Perez','Sanchez','Ramirez','Torres','Flores','Rivera','Gomez','Diaz','Vargas','Castro','Ruiz','Morales','Ortiz','Herrera','Medina','Rojas','Navarro','Silva','Mendoza','Cruz','Romero','Suarez','Vega','Molina','Delgado'
$puestos = @{1='Tecnico IT','Administrador de Sistemas','Analista IT'; 2='Comercial','Key Account Manager','Jefe de Ventas';
             3='Especialista Marketing','Disenador','Analista Digital'; 4='Contable','Analista Financiero','Controller';
             5='Tecnico RR.HH.','Responsable de Seleccion'; 6='Operario Logistica','Jefe de Almacen','Coordinador Operaciones';
             7='Agente de Soporte','Supervisor de Turno'; 8='Director de Area','Asistente de Direccion'}
$empleados = @()
$empRows = @()
for ($e = 1; $e -le 650; $e++) {
    $dep = PickW $deptos ($deptos | ForEach-Object { $_.W })
    $sed = PickW $sedes ($sedes | ForEach-Object { $_.W })
    $alta = RandDate ([datetime]'2014-01-01') ([datetime]'2026-09-30')
    $baja = $null; $estado = 'Activo'
    if (P 0.09) { $baja = RandDate $alta.AddDays(90) $corte; if ($baja -gt $corte) { $baja = $corte }; $estado = 'Baja' }
    $nom = "$(Pick $nombres) $(Pick $apellidos)"
    $id = 'E{0:D4}' -f $e
    $empleados += @{Id=$id; Dep=$dep.Id; Sede=$sed.Id; Estado=$estado}
    $empRows += "$id,$nom,$(Pick $puestos[$dep.Id]),$(D $alta),$estado,$(D $baja)"
}
Save 'Empleados.csv' 'EmpleadoID,Empleado,Puesto,FechaAlta,EstadoEmpleado,FechaBaja' $empRows

# ---------------- Activos ----------------
# Tipo: peso, coste min-max (gama estandar), vida util (anios), asignable a persona, fabricantes ficticios
$tipos = @(
    @{T='Portatil';   W=32; Min=850;  Max=1600;  Vida=4; Asig=$true;  Fab='Valtek','Nexora','Orbis','Kairo'},
    @{T='Monitor';    W=24; Min=150;  Max=380;   Vida=6; Asig=$true;  Fab='Lumen','Nexora','Valtek'},
    @{T='Movil';      W=15; Min=280;  Max=900;   Vida=3; Asig=$true;  Fab='Orbis','Kairo','Zentro'},
    @{T='Sobremesa';  W=9;  Min=650;  Max=1200;  Vida=5; Asig=$true;  Fab='Valtek','Nexora','Kairo'},
    @{T='Tablet';     W=6;  Min=320;  Max=850;   Vida=3; Asig=$true;  Fab='Orbis','Zentro'},
    @{T='Impresora';  W=5;  Min=280;  Max=1400;  Vida=5; Asig=$false; Fab='Printa','Nexora'},
    @{T='Switch';     W=5;  Min=600;  Max=3200;  Vida=7; Asig=$false; Fab='Stratos Networks','Helix Net'},
    @{T='Servidor';   W=4;  Min=4500; Max=12000; Vida=5; Asig=$false; Fab='Nexora','Stratos Networks','Kairo'}
)
$tasaInc = @{Portatil=0.55; Monitor=0.07; Movil=0.45; Sobremesa=0.28; Tablet=0.38; Impresora=1.1; Switch=0.25; Servidor=0.8}
$gamas = 'Basica','Estandar','Pro'
$gamaMult = @{Basica=0.75; Estandar=1.0; Pro=1.45}
$gamaGar = @{Basica=1; Estandar=2; Pro=3}
$catPorTipo = @{
    Portatil  = @(@('Hardware','Software','Bateria','Pantalla','Red','Perifericos'), @(25,30,18,12,10,5))
    Sobremesa = @(@('Hardware','Software','Red','Perifericos'), @(35,40,15,10))
    Monitor   = @(@('Hardware','Pantalla'), @(40,60))
    Movil     = @(@('Hardware','Software','Bateria','Pantalla'), @(20,30,25,25))
    Tablet    = @(@('Hardware','Software','Bateria','Pantalla'), @(20,35,25,20))
    Impresora = @(@('Hardware','Red','Perifericos'), @(50,20,30))
    Switch    = @(@('Hardware','Red'), @(30,70))
    Servidor  = @(@('Hardware','Software','Red'), @(40,40,20))
}
$costeRep = @{Portatil=@(90,420); Sobremesa=@(70,300); Monitor=@(60,180); Movil=@(60,260); Tablet=@(70,240); Impresora=@(40,350); Switch=@(150,900); Servidor=@(300,2500)}
$sedeLenta = @{1=1.0; 2=0.95; 3=1.15; 4=1.1; 5=1.75}   # Lima resuelve mas lento (insight)

$actRows = @(); $incRows = @(); $incId = 0
for ($a = 1; $a -le 2600; $a++) {
    $t = PickW $tipos ($tipos | ForEach-Object { $_.W })
    $fab = Pick $t.Fab
    $gama = PickW $gamas @(35, 45, 20)
    if ($t.T -in 'Servidor','Switch') { $gama = PickW $gamas @(5, 45, 50) }

    # Ubicacion / departamento / empleado
    $emp = $null
    if ($t.Asig) {
        $emp = Pick $empleados
        $dep = $emp.Dep; $sede = $emp.Sede
    } else {
        $dep = 1; $sede = (PickW $sedes ($sedes | ForEach-Object { $_.W })).Id
    }

    # Fecha de compra: Operaciones tiene un parque mas antiguo (insight)
    if ($dep -eq 6 -and (P 0.6)) { $compra = RandDate ([datetime]'2018-01-01') ([datetime]'2022-06-30') }
    else { $compra = RandDate ([datetime]'2019-01-01') ([datetime]'2026-10-15') }

    $coste = [int]([math]::Round((RInt $t.Min $t.Max) * $gamaMult[$gama] / 5) * 5)
    $finGar = $compra.AddYears($gamaGar[$gama])
    $edad = ($corte - $compra).TotalDays / 365.25

    # Estado
    if ($edad -gt ($t.Vida + 0.5) -and (P 0.55)) { $estado = 'Retirado' }
    elseif (P 0.012) { $estado = 'Extraviado' }
    elseif (P 0.04) { $estado = 'En reparacion' }
    elseif (P 0.12) { $estado = 'En stock' }
    else { $estado = if ($t.Asig) { 'Asignado' } else { 'En servicio' } }
    $empId = ''
    if ($estado -in 'Asignado', 'Extraviado', 'En reparacion' -and $t.Asig) { $empId = $emp.Id }
    if ($estado -in 'En stock', 'Retirado' -or -not $t.Asig) { $empId = '' }

    # Sistema operativo (Windows 10 sin soporte desde oct-2025 = insight)
    switch ($t.T) {
        { $_ -in 'Portatil', 'Sobremesa' } {
            if ($compra -lt [datetime]'2022-01-01') { $so = PickW @('Windows 10', 'Windows 11') @(55, 45) }
            elseif ($compra -lt [datetime]'2023-06-01') { $so = PickW @('Windows 10', 'Windows 11') @(20, 80) }
            else { $so = 'Windows 11' }
            if ($fab -eq 'Orbis') { $so = 'macOS' }
        }
        { $_ -in 'Movil', 'Tablet' } { $so = if ($fab -eq 'Orbis') { 'iOS' } else { 'Android' } }
        'Servidor' { $so = PickW @('Linux', 'Windows Server') @(60, 40) }
        default { $so = 'Firmware' }
    }

    $prov = if ($t.T -eq 'Portatil' -and (P 0.25)) { 4 } elseif ($sede -ge 3) { PickW @(2, 3) @(30, 70) } else { PickW @(1, 2) @(65, 35) }
    $id = 'A{0:D5}' -f $a
    $serie = '{0}-{1}' -f $fab.Substring(0, 3).ToUpper(), $script:rnd.Next(100000, 999999)
    $modelo = "$fab $($t.T) $gama"
    $actRows += "$id,$($t.T),$fab,$modelo,$gama,$serie,$(D $compra),$coste,$($t.Vida),$(D $finGar),$estado,$empId,$dep,$sede,$prov,$so"

    # ---------------- Incidencias del activo ----------------
    $mult = 1.0
    if ($fab -eq 'Valtek' -and $gama -eq 'Basica') { $mult *= 2.4 }   # modelo problematico (insight)
    if ($edad -gt 4) { $mult *= 1.5 }
    $finVidaInc = if ($estado -eq 'Retirado') { $compra.AddYears($t.Vida) } else { $corte }
    if ($finVidaInc -gt $corte) { $finVidaInc = $corte }
    $anios = ($finVidaInc - $compra).TotalDays / 365.25
    $esperado = $tasaInc[$t.T] * $anios * $mult * (0.4 + $script:rnd.NextDouble() * 1.2)
    $n = [math]::Floor($esperado); if (P ($esperado - $n)) { $n++ }
    for ($k = 0; $k -lt $n; $k++) {
        $incId++
        $ap = RandDate $compra.AddDays(10) $finVidaInc
        $cat = PickW $catPorTipo[$t.T][0] $catPorTipo[$t.T][1]
        $prio = if ($t.T -in 'Servidor', 'Switch') { PickW @('Critica', 'Alta', 'Media', 'Baja') @(25, 40, 25, 10) } else { PickW @('Critica', 'Alta', 'Media', 'Baja') @(3, 20, 42, 35) }
        $h = switch ($prio) { 'Critica' { RInt 2 14 } 'Alta' { RInt 6 40 } 'Media' { RInt 20 100 } 'Baja' { RInt 40 170 } }
        $h = [int][math]::Round($h * $sedeLenta[$sede])
        $abierta = (($corte - $ap).TotalDays -lt 25) -and (P 0.55)
        if ($abierta) { $cierre = ''; $hs = '' } else { $cierre = D ($ap.AddHours($h)); $hs = $h }
        $cr = 0
        if ($cat -in 'Hardware', 'Bateria', 'Pantalla' -and $ap -gt $finGar) { $cr = (RInt $costeRep[$t.T][0] $costeRep[$t.T][1]) }
        $canal = PickW @('Portal', 'Email', 'Telefono', 'Chat') @(40, 25, 20, 15)
        $incRows += ('I{0:D6},{1},{2},{3},{4},{5},{6},{7},{8}' -f $incId, $id, (D $ap), $cierre, $cat, $prio, $hs, $cr, $canal)
    }
}
Save 'Activos.csv' 'ActivoID,TipoActivo,Fabricante,Modelo,Gama,NumSerie,FechaCompra,CosteCompra,VidaUtilAnios,FinGarantia,Estado,EmpleadoID,DeptoID,UbicacionID,ProveedorID,SistemaOperativo' $actRows
Save 'Incidencias.csv' 'IncidenciaID,ActivoID,FechaApertura,FechaCierre,Categoria,Prioridad,HorasResolucion,CosteReparacion,Canal' $incRows

# ---------------- Licencias de software ----------------
# Software,Categoria,Modelo,Compradas,Asignadas,Activas30d,CosteUnitarioAnual,FechaRenovacion,DeptoID
$lic = @(
    'Microsoft 365 E3,Ofimatica,Suscripcion,620,598,571,380,2027-01-31,1',
    'Adobe Creative Cloud,Diseno,Suscripcion,45,41,19,780,2026-12-15,3',
    'Salesforce Sales Cloud,CRM,Suscripcion,160,152,131,1200,2027-03-31,2',
    'Zoom Business,Comunicacion,Suscripcion,250,231,64,180,2026-12-01,1',
    'Slack Pro,Comunicacion,Suscripcion,300,287,262,105,2027-05-31,1',
    'Tableau Creator,Analitica,Suscripcion,25,22,9,900,2027-02-28,4',
    'Power BI Pro,Analitica,Suscripcion,80,74,68,168,2027-01-31,4',
    'AutoCAD,Diseno,Suscripcion,12,10,3,2100,2027-04-30,6',
    'SAP Business One,ERP,Suscripcion,95,93,90,1450,2027-06-30,4',
    'Zendesk Suite,Soporte,Suscripcion,140,136,129,690,2027-01-15,7',
    'Atlassian Jira,Gestion de proyectos,Suscripcion,70,66,58,95,2027-08-31,1',
    'DocuSign,Firma digital,Suscripcion,40,38,14,300,2026-11-30,5',
    'Antivirus Endpoint,Seguridad,Suscripcion,1500,1412,1398,38,2027-02-15,1',
    'VPN Corporativa,Seguridad,Suscripcion,650,610,355,48,2027-03-15,1',
    'Windows Server Datacenter,Sistemas,Perpetua,20,18,18,0,,1',
    'Microsoft Visio,Ofimatica,Perpetua,60,52,11,0,,1',
    'Miro Business,Colaboracion,Suscripcion,90,84,30,120,2027-01-10,3',
    'LinkedIn Sales Navigator,CRM,Suscripcion,35,33,12,950,2026-12-20,2'
)
$licRows = @(); $i = 0
foreach ($l in $lic) { $i++; $licRows += ('L{0:D3},{1}' -f $i, $l) }
Save 'Licencias.csv' 'LicenciaID,Software,Categoria,TipoLicencia,LicenciasCompradas,LicenciasAsignadas,UsuariosActivos30d,CosteUnitarioAnual,FechaRenovacion,DeptoID' $licRows

Write-Host "`nListo. CSV generados en: $out"
