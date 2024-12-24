[Setup]
; ----- Basic Installer Info -----
AppName=MiniAnnotator
AppVersion=1.0.1
AppPublisher=RaccoonDev
DefaultDirName={pf}\MiniAnnotator

; Output (the final installer) will be "AnnotatorSetup.exe"
OutputBaseFilename=MiniAnnotatorSetup

; ----- Optional Settings -----
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DefaultGroupName=MiniAnnotator

[Files]
; Copy the main EXE
Source: "annotator.exe"; DestDir: "{app}"; Flags: ignoreversion

; Recursively copy everything in "_internal" into the same folder
Source: "_internal\*"; DestDir: "{app}\_internal"; Flags: recursesubdirs ignoreversion

[Icons]
; Create a Start Menu shortcut
Name: "{group}\MiniAnnotator"; Filename: "{app}\annotator.exe"

; Optionally, you can create a desktop shortcut as well
Name: "{commondesktop}\MiniAnnotator"; Filename: "{app}\annotator.exe"; Tasks: desktopicon

[Tasks]
; This allows user to choose whether to create a desktop shortcut
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
