; ═══════════════════════════════════════════════════════════════════════════════
;  DendroLen_installer.iss — Inno Setup script
;  Instalador profesional para DendroLen v2.1
;
;  Requisitos:
;    1. Inno Setup 6.x instalado (https://jrsoftware.org/isinfo.php)
;    2. Haber construido DendroLen con PyInstaller (carpeta dist\DendroLen\)
;    3. Tener DendroLen.ico en la carpeta del proyecto
;
;  Uso:
;    - Abrir este archivo con Inno Setup Compiler
;    - Clic en "Compile" (Ctrl+F9)
;    - El instalador se genera en la carpeta Output\
; ═══════════════════════════════════════════════════════════════════════════════

#define MyAppName "DendroLen"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "MoiCedrus — Moisés E. Rojas Badilla"
#define MyAppURL "https://github.com/MoiCedrus/DendroLen"
#define MyAppExeName "DendroLen.exe"
#define MyAppDescription "Medición de anillos de árboles con carro de medición serial"

[Setup]
; ── Identificación ────────────────────────────────────────────────────────────
AppId={{A1B2C3D4-5678-90AB-CDEF-DENDROLEN20}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppContact=moisese.rojasbadilla@gmail.com
AppCopyright=© 2026 Moisés E. Rojas Badilla

; ── Licencia (muestra el texto de GPL antes de instalar)
LicenseFile=LICENSE.txt

; ── Directorios ───────────────────────────────────────────────────────────────
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName=MoiCedrus\{#MyAppName}
AllowNoIcons=yes
DisableProgramGroupPage=yes

; ── Salida ────────────────────────────────────────────────────────────────────
OutputDir=Output
OutputBaseFilename=DendroLen_v{#MyAppVersion}_Setup_Win64
SetupIconFile=DendroLen.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}

; ── Compresión ────────────────────────────────────────────────────────────────
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4

; ── Apariencia del instalador ─────────────────────────────────────────────────
WizardStyle=modern
WizardSizePercent=110,110
; Si tienes una imagen de banner (164x314 px), descomenta la siguiente línea:
; WizardSmallImageFile=banner_small.bmp
; Si tienes una imagen lateral (164x314 px):
; WizardImageFile=banner_lateral.bmp

; ── Privilegios ───────────────────────────────────────────────────────────────
; "lowest" permite instalar sin admin (en carpeta del usuario)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; ── Versión mínima de Windows ─────────────────────────────────────────────────
MinVersion=10.0

; ── Arquitectura ──────────────────────────────────────────────────────────────
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
spanish.LaunchApp=Iniciar {#MyAppName} después de la instalación
english.LaunchApp=Launch {#MyAppName} after installation
spanish.CreateDesktopIcon=Crear acceso directo en el escritorio
english.CreateDesktopIcon=Create desktop shortcut
spanish.AssociateRwl=Asociar archivos .rwl con {#MyAppName}
english.AssociateRwl=Associate .rwl files with {#MyAppName}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "Opciones adicionales:"
Name: "rwlassoc"; Description: "{cm:AssociateRwl}"; GroupDescription: "Opciones adicionales:"; Flags: unchecked

[Files]
; Copiar todo el contenido de dist\DendroLen\ al directorio de instalación
Source: "dist\DendroLen\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentación
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.md"

[Icons]
; Menú Inicio
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    Comment: "{#MyAppDescription}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"

; Escritorio (si el usuario lo eligió)
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon; Comment: "{#MyAppDescription}"

[Registry]
; Asociar .rwl con DendroLen (si el usuario lo eligió)
Root: HKCU; Subkey: "Software\Classes\.rwl"; ValueType: string; \
    ValueName: ""; ValueData: "DendroLen.rwl"; Flags: uninsdeletevalue; Tasks: rwlassoc
Root: HKCU; Subkey: "Software\Classes\DendroLen.rwl"; ValueType: string; \
    ValueName: ""; ValueData: "Archivo Tucson (.rwl)"; Flags: uninsdeletekey; Tasks: rwlassoc
Root: HKCU; Subkey: "Software\Classes\DendroLen.rwl\DefaultIcon"; ValueType: string; \
    ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: rwlassoc
Root: HKCU; Subkey: "Software\Classes\DendroLen.rwl\shell\open\command"; ValueType: string; \
    ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: rwlassoc

[Run]
; Ofrecer iniciar la app después de instalar
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchApp}"; \
    Flags: nowait postinstall skipifsilent

[Code]
// ── Verificar si ya hay una versión instalada ────────────────────────────────
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  UninstPath: String;
begin
  Result := True;
  // Si existe una instalación previa, ofrecer desinstalar primero
  if RegQueryStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A1B2C3D4-5678-90AB-CDEF-DENDROLEN20}_is1',
     'UninstallString', UninstPath) then
  begin
    if MsgBox('Se detectó una versión anterior de DendroLen.' + #13#10 +
              '¿Desea desinstalarla antes de continuar?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec(RemoveQuotes(UninstPath), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
