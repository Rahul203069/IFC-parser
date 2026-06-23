# IFC Parser

A PySide6 desktop app for batch parsing IFC files with IfcOpenShell and exporting them to GLB or STEP.

## Features

- Drag-and-drop or browse to queue multiple `.ifc` files
- Parse IFC metadata and geometry with IfcOpenShell
- Export files as GLB for 3D/web viewers
- Export STEP copies for downstream CAD workflows
- Track batch progress, success/failure counts, and conversion logs
- Build a Windows executable with PyInstaller

## Requirements

- Python 3.10+
- PySide6
- IfcOpenShell
- PyInstaller, only needed for packaging

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install PySide6 ifcopenshell pyinstaller
```

## Run

```powershell
python main.py
```

## Build

The project includes a PyInstaller spec file for building the desktop executable:

```powershell
pyinstaller --clean --noconfirm .\IFCBatchConverterDemo.spec
```

The generated executable is written under `dist/`.

## Repository Description

PySide6 desktop IFC batch parser and converter powered by IfcOpenShell, with GLB and STEP export support.
