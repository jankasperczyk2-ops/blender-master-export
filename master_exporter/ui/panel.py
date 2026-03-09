import bpy
from bpy.types import Panel

from ..utils.hierarchy import find_asset_from_object


class MASTEREXPORT_PT_MainPanel(Panel):
    bl_label = "Master Export"
    bl_idname = "MASTEREXPORT_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master Export"

    def draw(self, context):
        layout = self.layout
        props = context.scene.master_export

        header = layout.box()
        row = header.row()
        row.scale_y = 1.3
        row.label(text="Master Export", icon='EXPORT')

        col = header.column(align=True)
        col.prop(props, "asset_name", icon='OBJECT_DATA')
        col.prop(props, "export_target", icon='SCENE')


class MASTEREXPORT_PT_SetExportPanel(Panel):
    bl_label = "Set Export"
    bl_idname = "MASTEREXPORT_PT_SetExportPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master Export"
    bl_parent_id = "MASTEREXPORT_PT_MainPanel"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Select meshes, then click Set Export", icon='INFO')
        row = box.row()
        row.scale_y = 1.4
        row.operator("master_export.set_export", icon='COLLECTION_NEW')


class MASTEREXPORT_PT_ColliderPanel(Panel):
    bl_label = "Collision Generation"
    bl_idname = "MASTEREXPORT_PT_ColliderPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master Export"
    bl_parent_id = "MASTEREXPORT_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        props = context.scene.master_export

        box = layout.box()
        col = box.column(align=True)

        col.label(text="Mode:", icon='MOD_PHYSICS')
        col.prop(props, "collision_mode", text="")

        if props.export_target == 'UNREAL':
            col.separator()
            col.label(text="Unreal Prefix:", icon='MOD_BUILD')
            col.prop(props, "unreal_collision_prefix", text="")

        if props.collision_mode == 'SMART':
            col.separator()
            col.label(text="Voxel Detail:", icon='MOD_REMESH')
            col.prop(props, "smart_voxel_size", text="Voxel Size")

        mode_descriptions = {
            'SIMPLE': "One tight-fitting oriented box around all geometry",
            'SMART': "Voxel remesh + convex hull for precise collision",
        }
        desc_box = box.box()
        desc_box.scale_y = 0.7
        desc_box.label(text=mode_descriptions.get(props.collision_mode, ""), icon='INFO')

        row = layout.row()
        row.scale_y = 1.4
        row.operator("master_export.generate_colliders", icon='MESH_CUBE')


class MASTEREXPORT_PT_ExportCheckPanel(Panel):
    bl_label = "Export Check"
    bl_idname = "MASTEREXPORT_PT_ExportCheckPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master Export"
    bl_parent_id = "MASTEREXPORT_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        props = context.scene.master_export

        active = context.active_object
        asset_info = find_asset_from_object(active)
        has_asset = asset_info is not None

        if not has_asset:
            info_box = layout.box()
            info_box.label(text="Select an asset object to see stats", icon='INFO')

            fix_box = layout.box()
            fix_box.label(text="Fix Tools", icon='TOOL_SETTINGS')
            col = fix_box.column(align=True)
            col.enabled = False
            col.operator("master_export.fix_doubles", icon='VERTEXSEL')
            col.operator("master_export.fix_normals", icon='NORMALS_FACE')
            col.operator("master_export.fix_transforms", icon='OBJECT_ORIGIN')
            col.separator()
            col.operator("master_export.fix_all", icon='FILE_REFRESH')
            return

        if props.check_asset_name == "":
            info_box = layout.box()
            info_box.label(text="Checking...", icon='INFO')
            return

        summary = layout.box()
        summary_row = summary.row()
        summary_row.label(text=f"Asset: {props.check_asset_name}", icon='OUTLINER_DATA_MESH')

        col = summary.column(align=True)
        col.label(text=f"Total Triangles: {props.check_total_tris:,}", icon='MESH_DATA')

        if props.check_issues_found == 0:
            row = col.row()
            row.label(text="All clean - ready to export", icon='CHECKMARK')
        else:
            row = col.row()
            row.alert = True
            row.label(text=f"{props.check_issues_found} issue(s) found", icon='ERROR')

        if not props.check_has_colliders:
            warn_box = layout.box()
            warn_row = warn_box.row()
            warn_row.alert = True
            warn_row.label(text="No colliders found!", icon='ERROR')
            warn_box.label(text="Generate colliders before export", icon='INFO')

        if len(props.check_results) > 0:
            mesh_box = layout.box()
            mesh_box.label(text="Mesh Details", icon='OUTLINER_OB_MESH')

            for result in props.check_results:
                item_box = mesh_box.box()

                header_row = item_box.row()
                has_issues = (result.has_doubles or result.has_flipped or
                              result.bad_scale or result.bad_rotation)
                if has_issues:
                    header_row.alert = True
                header_row.label(text=result.obj_name, icon='OBJECT_DATA')
                header_row.label(text=f"{result.tri_count:,} tris")

                if result.has_doubles:
                    row = item_box.row(align=True)
                    row.alert = True
                    row.label(text=f"Double verts: {result.doubles_count}", icon='ERROR')
                    op = row.operator("master_export.fix_doubles", text="Fix", icon='TOOL_SETTINGS')
                    op.obj_name = result.obj_name

                if result.has_flipped:
                    row = item_box.row(align=True)
                    row.alert = True
                    row.label(text=f"Flipped faces: {result.flipped_count}", icon='ERROR')
                    op = row.operator("master_export.fix_normals", text="Fix", icon='TOOL_SETTINGS')
                    op.obj_name = result.obj_name

                if result.bad_scale:
                    row = item_box.row(align=True)
                    row.alert = True
                    row.label(text=f"Scale: ({result.scale_values})", icon='ERROR')
                    op = row.operator("master_export.fix_transforms", text="Fix", icon='TOOL_SETTINGS')
                    op.obj_name = result.obj_name

                if result.bad_rotation:
                    row = item_box.row(align=True)
                    row.alert = True
                    row.label(text=f"Rotation: ({result.rotation_values})", icon='ERROR')
                    op = row.operator("master_export.fix_transforms", text="Fix", icon='TOOL_SETTINGS')
                    op.obj_name = result.obj_name

                if not has_issues:
                    row = item_box.row()
                    row.label(text="Clean", icon='CHECKMARK')

        if props.check_issues_found > 0:
            layout.separator()
            row = layout.row()
            row.scale_y = 1.3
            row.alert = True
            row.operator("master_export.fix_all", icon='FILE_REFRESH', text="Fix All Issues")


class MASTEREXPORT_PT_ExportPanel(Panel):
    bl_label = "Export"
    bl_idname = "MASTEREXPORT_PT_ExportPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master Export"
    bl_parent_id = "MASTEREXPORT_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        props = context.scene.master_export

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Export Path:", icon='FILE_FOLDER')
        col.prop(props, "export_path", text="")

        col.label(text=f"Target: {props.export_target.title()}", icon='SCENE')

        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        row.operator("master_export.export_asset", icon='EXPORT', text="Export Asset")
