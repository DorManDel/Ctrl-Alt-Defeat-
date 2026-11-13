' Preferred one-click entry: requests UAC and opens just the elevated PowerShell window.
' Uses local checked-in launcher.ps1; never downloads arbitrary scripts.
Option Explicit
Dim shell, fso, root, arguments
Set shell = CreateObject("Shell.Application")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
arguments = "-NoProfile -ExecutionPolicy Bypass -File """ & root & "\launcher.ps1"""
shell.ShellExecute "powershell.exe", arguments, root, "runas", 1
