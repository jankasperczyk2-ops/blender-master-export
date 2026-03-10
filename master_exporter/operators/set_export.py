import bpy
from bpy.types import Operator

from ..utils.hierarchy import setup_asset_hierarchy, move_selected_meshes_to_geometry


class MASTEREXPORT_OT_SetExport(Operator):
    bl_idname = "master_export.set_export"
    bl_label = "Set Export"
    bl_description = "Create export hierarchy for selected meshes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        props = context.scene.master_export
        asset_name = props.asset_name

        if not asset_name:
            self.report({'ERROR'}, "Asset name cannot be empty")
            return {'CANCELLED'}

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            self.report({'ERROR'}, "No meshes selected")
            return {'CANCELLED'}

        from mathutils import Vector
        center = Vector((0, 0, 0))
        for obj in selected_meshes:
            center += obj.matrix_world.translation
        center /= len(selected_meshes)

        asset_col, parent_col, geo_col, collider_col, root_empty = setup_asset_hierarchy(
            context, asset_name, location=center
        )

        moved = move_selected_meshes_to_geometry(context, geo_col, root_empty)

        bpy.ops.object.select_all(action='DESELECT')
        root_empty.select_set(True)
        context.view_layer.objects.active = root_empty

        self.report({'INFO'}, f"Export setup complete: {len(moved)} meshes organized under {root_empty.name}")
        return {'FINISHED'}
