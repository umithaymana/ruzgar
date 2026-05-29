' RUZGAR — masaustu Electron (API 8779, Faz 98)
Option Explicit
Dim shell, fso, root, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & root & "\RuzgarMasaustuBaslat.ps1"""
Set shell = CreateObject("WScript.Shell")
shell.Run cmd, 0, True
