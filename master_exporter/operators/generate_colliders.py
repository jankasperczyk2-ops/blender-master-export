import bpy
from bpy.types import Operator

from ..utils.hierarchy import get_geometry_objects, get_root_empty_for_asset
from ..utils.collision import (
    generate_simple_bounding_box,
    generate_smart_collider,
)
from ..utils.naming import get_collection_name


class MASTEREXPORT_OT_GenerateColliders(Operator):
    bl_idname = "master_export.generate_colliders"
    bl_label = "Generate Colliders"
    bl_description = "Generate collision meshes for the asset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.master_export
        asset_name = props.asset_name
        root_empty = get_root_empty_for_asset(asset_name)
        return root_empty is not None

    def execute(self, context):
        props = context.scene.master_export
        asset_name = props.asset_name
        export_target = props.export_target
        collision_mode = props.collision_mode

        root_empty = get_root_empty_for_asset(asset_name)
        if root_empty is None:
            self.report({'ERROR'}, "No export setup found. Run Set Export first.")
            return {'CANCELLED'}

        asset_col_name = get_collection_name(asset_name)
        asset_col = bpy.data.collections.get(asset_col_name)
        if asset_col is None:
            self.report({'ERROR'}, "Asset collection not found")
            return {'CANCELLED'}

        geo_col = None
        collider_col = None
        for child in asset_col.children:
            if child.name == "Geometry":
                geo_col = child
            elif child.name == "Colliders":
                collider_col = child

        if geo_col is None or collider_col is None:
            self.report({'ERROR'}, "Geometry or Colliders collection not found")
            return {'CANCELLED'}

        geo_objects = get_geometry_objects(geo_col)
        if not geo_objects:
            self.report({'ERROR'}, "No geometry found in Geometry collection")
            return {'CANCELLED'}

        if collision_mode == 'SIMPLE':
            colliders = generate_simple_bounding_box(
                context, geo_objects, asset_name, export_target, collider_col, root_empty
            )
        elif collision_mode == 'SMART':
            colliders = generate_smart_collider(
                context, geo_objects, asset_name, export_target,
                collider_col, root_empty, voxel_size=props.smart_voxel_size
            )
        else:
            self.report({'ERROR'}, f"Unknown collision mode: {collision_mode}")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        root_empty.select_set(True)
        context.view_layer.objects.active = root_empty

        self.report({'INFO'}, f"Generated {len(colliders)} collider(s) using {collision_mode} mode")
        return {'FINISHED'}
