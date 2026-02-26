# Master Export - Blender Addon

## Overview
Professional Blender addon for exporting assets to Unreal Engine and Unity. This is a Blender 4.x addon using only `bpy` — it is NOT a web application.

## Project Structure
```
master_exporter/
├── __init__.py              # Addon entry point (bl_info, register/unregister)
├── operators/
│   ├── set_export.py        # Set Export operator - creates collection hierarchy
│   ├── generate_colliders.py # Collision mesh generation operator
│   └── export_asset.py      # FBX export operator
├── ui/
│   └── panel.py             # 3D Viewport sidebar panel (Master Export tab)
└── utils/
    ├── naming.py            # Naming conventions for Unreal/Unity
    ├── hierarchy.py         # Collection and object hierarchy management
    ├── collision.py         # Collision generation algorithms (Simple/Multi/Convex)
    └── fbx.py               # FBX export settings per engine
```

## Features
- **Set Export**: Organizes selected meshes into a structured collection hierarchy with a root Empty for pivot control
- **Export Targets**: Unreal Engine and Unity with engine-specific FBX settings and naming
- **Collision Generation**: Three modes — Simple Bounding Box, Multi Box Approximation, Convex Lite
- **FBX Export**: One-click export with correct settings per target engine
- **Re-export**: Move the root Empty to adjust pivot, then re-export (overwrites previous file)

## Installation
1. Zip the `master_exporter/` folder
2. In Blender: Edit → Preferences → Add-ons → Install
3. Select the zip file
4. Enable "Master Export" in the addon list

## Dependencies
- Blender 4.x
- No external Python packages (bpy only)
