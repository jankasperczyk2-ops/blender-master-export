import bpy

from .naming import (
    get_root_empty_name,
    get_collection_name,
    get_parent_collection_name,
    get_geometry_collection_name,
    get_colliders_collection_name,
)


def find_or_create_collection(parent_collection, name):
    for child in parent_collection.children:
        if child.name == name:
            return child
    new_col = bpy.data.collections.new(name)
    parent_collection.children.link(new_col)
    return new_col


MASTER_COLLECTION_NAME = "MasterExport"


def get_or_create_master_collection(context):
    scene_col = context.scene.collection
    return find_or_create_collection(scene_col, MASTER_COLLECTION_NAME)


def setup_asset_hierarchy(context, asset_name):
    master_col = get_or_create_master_collection(context)

    asset_col = find_or_create_collection(master_col, get_collection_name(asset_name))
    parent_col = find_or_create_collection(asset_col, get_parent_collection_name(asset_name))
    geo_col = find_or_create_collection(asset_col, get_geometry_collection_name(asset_name))
    collider_col = find_or_create_collection(asset_col, get_colliders_collection_name(asset_name))

    root_empty_name = get_root_empty_name(asset_name)
    root_empty = bpy.data.objects.get(root_empty_name)
    if root_empty is None:
        root_empty = bpy.data.objects.new(root_empty_name, None)
        root_empty.empty_display_type = 'ARROWS'
        root_empty.empty_display_size = 0.5

    if root_empty.name not in parent_col.objects:
        parent_col.objects.link(root_empty)

    for col in root_empty.users_collection:
        if col != parent_col:
            col.objects.unlink(root_empty)

    return asset_col, parent_col, geo_col, collider_col, root_empty


def move_selected_meshes_to_geometry(context, geo_col, root_empty):
    moved = []
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
        if obj == root_empty:
            continue

        for col in obj.users_collection:
            col.objects.unlink(obj)
        geo_col.objects.link(obj)

        obj.parent = root_empty
        obj.matrix_parent_inverse = root_empty.matrix_world.inverted()
        moved.append(obj)
    return moved


def get_geometry_objects(geo_col):
    return [obj for obj in geo_col.objects if obj.type == 'MESH']


def get_collider_objects(collider_col):
    return [obj for obj in collider_col.objects if obj.type == 'MESH']


def get_root_empty_for_asset(asset_name):
    root_name = get_root_empty_name(asset_name)
    return bpy.data.objects.get(root_name)


def select_hierarchy(root_empty):
    bpy.ops.object.select_all(action='DESELECT')
    root_empty.select_set(True)
    for child in root_empty.children_recursive:
        child.select_set(True)
    bpy.context.view_layer.objects.active = root_empty
