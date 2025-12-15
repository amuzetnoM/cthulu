#!/usr/bin/env pwsh
# Shortcut to launch Herald setup wizard interactively
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)\..\
powershell -NoProfile -ExecutionPolicy Bypass -Command "python -m herald --wizard"
