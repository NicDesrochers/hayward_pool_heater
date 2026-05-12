# Copyright (c) 2024 S. Leclerc (sle118@hotmail.com)
#
# This file is part of the Pool Heater Controller component project.
#
# @project Pool Heater Controller Component
# @developer S. Leclerc (sle118@hotmail.com)
# @license MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

param(
    [switch] $Local,
    [switch] $BindCache,
    [string] $Image = "ghcr.io/esphome/esphome:latest",
    [string[]] $Fixtures = @(
        "tests/components/hwp/test.esp32-idf.yaml",
        "tests/components/hwp/test.esp32-idf-pulse-debug.yaml"
    )
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$WorkDir = "/workspaces/hayward_pool_heater"
$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "hayward-esphome-tests"
$ConfigDir = Join-Path $TempRoot "config"
$BuildDir = Join-Path $TempRoot "build"
$PlatformioDir = Join-Path $TempRoot "platformio"
$CacheDir = Join-Path $TempRoot "cache"
$RootCacheDir = Join-Path $TempRoot "root-cache"

New-Item -ItemType Directory -Force -Path $ConfigDir, $BuildDir, $PlatformioDir, $CacheDir, $RootCacheDir | Out-Null

function Get-GitStatus {
    return ((git -C $RepoRoot status --short) -join "`n")
}

function Invoke-ESPHome {
    param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $ESPHomeArgs)

    if ($Local) {
        $previousBuildPath = $env:ESPHOME_BUILD_PATH
        try {
            $env:ESPHOME_BUILD_PATH = $BuildDir
            & esphome @ESPHomeArgs
        } finally {
            $env:ESPHOME_BUILD_PATH = $previousBuildPath
        }
        if ($LASTEXITCODE -ne 0) {
            throw "esphome $($ESPHomeArgs -join ' ') failed with exit code $LASTEXITCODE"
        }
        return
    }

    $cacheMounts = if ($BindCache) {
        @(
            "-v", "${BuildDir}:/build",
            "-v", "${PlatformioDir}:/root/.platformio",
            "-v", "${CacheDir}:/cache",
            "-v", "${RootCacheDir}:/root/.cache"
        )
    } else {
        @(
            "-v", "hayward-esphome-test-build:/build",
            "-v", "hayward-esphome-test-platformio:/root/.platformio",
            "-v", "hayward-esphome-test-cache:/cache",
            "-v", "hayward-esphome-test-root-cache:/root/.cache"
        )
    }

    $dockerArgs = @(
        "run", "--rm",
        "-v", "${RepoRoot}:${WorkDir}",
        "-v", "${ConfigDir}:/config"
    ) + $cacheMounts + @(
        "-e", "ESPHOME_BUILD_PATH=/build",
        "-w", $WorkDir,
        $Image
    ) + $ESPHomeArgs

    & docker @dockerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker esphome $($ESPHomeArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

$statusBefore = Get-GitStatus

Invoke-ESPHome version

foreach ($fixture in $Fixtures) {
    Write-Host "Validating $fixture"
    Invoke-ESPHome config $fixture
}

foreach ($fixture in $Fixtures) {
    Write-Host "Compiling $fixture"
    Invoke-ESPHome compile $fixture
}

$statusAfter = Get-GitStatus
if ($statusBefore -ne $statusAfter) {
    Write-Error @"
Git status changed during ESPHome tests.

Before:
$statusBefore

After:
$statusAfter
"@
}

Write-Host "ESPHome fixture tests completed without repo status changes."
