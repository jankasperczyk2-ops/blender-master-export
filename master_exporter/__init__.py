bl_info = {
    "name": "Master Export",
    "author": "Master Exporter Team",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Master Export",
    "description": "Professional asset export management for Unreal Engine and Unity",
    "category": "Import-Export",
}

import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup

from .operators.set_export import MASTEREXPORT_OT_SetExport
from .operators.generate_colliders import MASTEREXPORT_OT_GenerateColliders
from .operators.export_asset import MASTEREXPORT_OT_ExportAsset
from .ui.panel import (
    MASTEREXPORT_PT_MainPanel,
    MASTEREXPORT_PT_SetExportPanel,
    MASTEREXPORT_PT_ColliderPanel,
    MASTEREXPORT_PT_ExportPanel,
)


class MasterExportProperties(PropertyGroup):
    export_target: EnumProperty(
        name="Export Target",
        description="Target game engine for export",
        items=[
            ('UNREAL', "Unreal Engine", "Export configured for Unreal Engine"),
            ('UNITY', "Unity", "Export configured for Unity"),
        ],
        default='UNREAL',
    )

    collision_mode: EnumProperty(
        name="Collision Mode",
        description="Collision generation method",
        items=[
            ('SIMPLE', "Simple Bounding Box", "Single bounding box from all geometry"),
            ('MULTI', "Multi Box Approximation", "Multiple boxes based on proportions"),
            ('CONVEX', "Convex Lite", "Decimated convex decomposition"),
        ],
        default='SIMPLE',
    )

    unreal_collision_prefix: EnumProperty(
        name="Collision Prefix",
        description="Unreal Engine collision prefix type",
        items=[
            ('UCX', "UCX (Convex)", "Convex collision"),
            ('UBX', "UBX (Box)", "Box collision"),
            ('USP', "USP (Sphere)", "Sphere collision"),
            ('UCP', "UCP (Capsule)", "Capsule collision"),
        ],
        default='UCX',
    )

    export_path: StringProperty(
        name="Export Path",
        description="Directory for exported FBX files",
        subtype='DIR_PATH',
        default="//exports/",
    )

    asset_name: StringProperty(
        name="Asset Name",
        description="Name for the export asset",
        default="AssetName_01",
    )


classes = (
    MasterExportProperties,
    MASTEREXPORT_OT_SetExport,
    MASTEREXPORT_OT_GenerateColliders,
    MASTEREXPORT_OT_ExportAsset,
    MASTEREXPORT_PT_MainPanel,
    MASTEREXPORT_PT_SetExportPanel,
    MASTEREXPORT_PT_ColliderPanel,
    MASTEREXPORT_PT_ExportPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.master_export = PointerProperty(type=MasterExportProperties)


def unregister():
    del bpy.types.Scene.master_export
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
