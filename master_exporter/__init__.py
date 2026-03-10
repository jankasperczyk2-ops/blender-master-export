bl_info = {
    "name": "Master Export",
    "author": "Master Exporter Team",
    "version": (1, 4, 0),
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
from .operators.pre_export_check import run_auto_check
from .ui.panel import (
    MASTEREXPORT_PT_MainPanel,
    MASTEREXPORT_PT_SetExportPanel,
    MASTEREXPORT_PT_ColliderPanel,
    MASTEREXPORT_PT_ExportCheckPanel,
    MASTEREXPORT_PT_ExportPanel,
)
from .utils.hierarchy import find_asset_from_object


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
            ('SMART', "Smart Collider", "Analyzes shape and auto-decomposes"),
            ('SIMPLE', "Simple Bounding Box", "Single oriented bounding box"),
        ],
        default='SMART',
    )

    unreal_collision_prefix: EnumProperty(
        name="Collision Prefix",
        description="Unreal Engine collision prefix type",
        items=[
            ('UCX', "UCX (Convex)", "Convex collision"),
            ('UBX', "UBX (Box)", "Box collision"),
        ],
        default='UCX',
    )

    smart_voxel_size: FloatProperty(
        name="Voxel Size",
        description="Voxel size for smart collider (smaller = more detail, more pieces)",
        default=1.0,
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

    check_results: CollectionProperty(type=MeshCheckResult)

    check_asset_name: StringProperty(
        name="Check Asset Name",
        default="",
    )

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


_last_active_object_name = ""


def _on_depsgraph_update(scene, depsgraph):
    global _last_active_object_name

    active = bpy.context.view_layer.objects.active
    current_name = active.name if active else ""

    if current_name == _last_active_object_name:
        return

    _last_active_object_name = current_name

    asset_info = find_asset_from_object(active)
    props = scene.master_export

    if asset_info is None:
        props.check_results.clear()
        props.check_asset_name = ""
        props.check_total_tris = 0
        props.check_issues_found = 0
        props.check_has_colliders = False
        return

    run_auto_check(bpy.context)


classes = (
    MeshCheckResult,
    MasterExportProperties,
    MASTEREXPORT_OT_SetExport,
    MASTEREXPORT_OT_GenerateColliders,
    MASTEREXPORT_OT_ExportAsset,
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
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)


def unregister():
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    del bpy.types.Scene.master_export
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
