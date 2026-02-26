import bpy
from bpy.types import Operator

from ..utils.hierarchy import get_root_empty_for_asset, select_hierarchy
from ..utils.fbx import export_fbx_unreal, export_fbx_unity, get_export_filepath


class MASTEREXPORT_OT_ExportAsset(Operator):
    bl_idname = "master_export.export_asset"
    bl_label = "Export Selected Asset"
    bl_description = "Export asset as FBX for the selected target engine"
    bl_options = {'REGISTER'}

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

        root_empty = get_root_empty_for_asset(asset_name)
        if root_empty is None:
            self.report({'ERROR'}, "No export setup found. Run Set Export first.")
            return {'CANCELLED'}

        filepath = get_export_filepath(context, asset_name)

        select_hierarchy(root_empty)

        try:
            if export_target == 'UNREAL':
                export_fbx_unreal(filepath, root_empty)
            else:
                export_fbx_unity(filepath, root_empty)
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Exported to: {filepath}")
        return {'FINISHED'}
