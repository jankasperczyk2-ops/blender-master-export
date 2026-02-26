import bpy
from bpy.types import Panel


class MASTEREXPORT_PT_MainPanel(Panel):
    bl_label = "Master Export"
    bl_idname = "MASTEREXPORT_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master Export"

    def draw(self, context):
        layout = self.layout
        props = context.scene.master_export

        layout.prop(props, "asset_name")
        layout.prop(props, "export_target")


class MASTEREXPORT_PT_SetExportPanel(Panel):
    bl_label = "Set Export"
    bl_idname = "MASTEREXPORT_PT_SetExportPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Master Export"
    bl_parent_id = "MASTEREXPORT_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        layout.operator("master_export.set_export", icon='COLLECTION_NEW')


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

        layout.prop(props, "collision_mode")

        if props.export_target == 'UNREAL':
            layout.prop(props, "unreal_collision_prefix")

        layout.operator("master_export.generate_colliders", icon='MESH_CUBE')


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

        layout.prop(props, "export_path")
        layout.operator("master_export.export_asset", icon='EXPORT')
