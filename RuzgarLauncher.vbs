' PowerShell bitene kadar bekle (yarim kalan baslatma olmasin); pencere stili 0 = gizli
Option Explicit
Dim shell, fso, root, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File """ & root & "\Ruzgar.ps1"""
Set shell = CreateObject("WScript.Shell")
' 0 = gizli; True = PowerShell bitene kadar bekle (Electron ayri process olarak acilir)
shell.Run cmd, 0, True
