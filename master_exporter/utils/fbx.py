import bpy
import os


def apply_transforms_on_children(root_empty):
    bpy.ops.object.select_all(action='DESELECT')

    mesh_children = [child for child in root_empty.children_recursive if child.type == 'MESH']

    for child in mesh_children:
        child.select_set(True)

    if mesh_children:
        bpy.context.view_layer.objects.active = mesh_children[0]
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    bpy.ops.object.select_all(action='DESELECT')


def _select_hierarchy(root_empty):
    bpy.ops.object.select_all(action='DESELECT')
    root_empty.select_set(True)
    for child in root_empty.children_recursive:
        child.select_set(True)
    bpy.context.view_layer.objects.active = root_empty


def export_fbx_unreal(filepath, root_empty):
    _select_hierarchy(root_empty)
    apply_transforms_on_children(root_empty)
    _select_hierarchy(root_empty)

    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=True,
        apply_unit_scale=True,
        bake_space_transform=True,
        add_leaf_bones=False,
        mesh_smooth_type='FACE',
        axis_forward='-Z',
        axis_up='Y',
        object_types={'EMPTY', 'MESH'},
        use_mesh_modifiers=True,
    )


def export_fbx_unity(filepath, root_empty):
    _select_hierarchy(root_empty)
    apply_transforms_on_children(root_empty)
    _select_hierarchy(root_empty)

    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=True,
        apply_scale_options='FBX_SCALE_ALL',
        apply_unit_scale=True,
        axis_forward='-Z',
        axis_up='Y',
        object_types={'EMPTY', 'MESH'},
        use_mesh_modifiers=True,
    )


def get_export_filepath(context, asset_name):
    props = context.scene.master_export
    export_dir = bpy.path.abspath(props.export_path)

    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    filename = f"SM_{asset_name}.fbx"
    return os.path.join(export_dir, filename)
