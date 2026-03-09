bl_info = {
    "name": "Master Export",
    "author": "Master Exporter Team",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Master Export",
    "description": "Professional asset export management for Unreal Engine and Unity",
    "category": "Import-Export",
}

import bpy
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)
from bpy.types import PropertyGroup

from .operators.set_export import MASTEREXPORT_OT_SetExport
from .operators.generate_colliders import MASTEREXPORT_OT_GenerateColliders
from .operators.export_asset import MASTEREXPORT_OT_ExportAsset
from .operators.pre_export_check import (
    MASTEREXPORT_OT_RunCheck,
    MASTEREXPORT_OT_FixDoubles,
    MASTEREXPORT_OT_FixNormals,
    MASTEREXPORT_OT_FixTransforms,
    MASTEREXPORT_OT_FixAll,
)
from .ui.panel import (
    MASTEREXPORT_PT_MainPanel,
    MASTEREXPORT_PT_SetExportPanel,
    MASTEREXPORT_PT_ColliderPanel,
    MASTEREXPORT_PT_ExportCheckPanel,
    MASTEREXPORT_PT_ExportPanel,
)


class MeshCheckResult(PropertyGroup):
    obj_name: StringProperty(name="Object Name")
    tri_count: IntProperty(name="Triangles")
    has_doubles: BoolProperty(name="Has Doubles")
    doubles_count: IntProperty(name="Double Verts")
    has_flipped: BoolProperty(name="Flipped Faces")
    flipped_count: IntProperty(name="Flipped Count")
    bad_scale: BoolProperty(name="Bad Scale")
    bad_rotation: BoolProperty(name="Bad Rotation")
    scale_values: StringProperty(name="Scale")
    rotation_values: StringProperty(name="Rotation")


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
            ('SIMPLE', "Simple Bounding Box", "Single oriented bounding box"),
            ('MULTI', "Multi Box", "Multiple oriented boxes per loose part"),
            ('CONVEX', "Convex Lite", "Decimated convex decomposition"),
            ('SMART', "Smart Collider", "Voxel remesh + convex hull decomposition"),
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

    smart_voxel_size: FloatProperty(
        name="Voxel Size",
        description="Voxel size for smart collider (smaller = more detail, more pieces)",
        default=0.1,
        min=0.01,
        max=2.0,
        step=1,
        precision=3,
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

    check_performed: BoolProperty(
        name="Check Performed",
        default=False,
    )

    check_results: CollectionProperty(type=MeshCheckResult)

    check_has_colliders: BoolProperty(
        name="Has Colliders",
        default=False,
    )

    check_total_tris: IntProperty(
        name="Total Triangles",
        default=0,
    )

    check_issues_found: IntProperty(
        name="Issues Found",
        default=0,
    )


classes = (
    MeshCheckResult,
    MasterExportProperties,
    MASTEREXPORT_OT_SetExport,
    MASTEREXPORT_OT_GenerateColliders,
    MASTEREXPORT_OT_ExportAsset,
    MASTEREXPORT_OT_RunCheck,
    MASTEREXPORT_OT_FixDoubles,
    MASTEREXPORT_OT_FixNormals,
    MASTEREXPORT_OT_FixTransforms,
    MASTEREXPORT_OT_FixAll,
    MASTEREXPORT_PT_MainPanel,
    MASTEREXPORT_PT_SetExportPanel,
    MASTEREXPORT_PT_ColliderPanel,
    MASTEREXPORT_PT_ExportCheckPanel,
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
