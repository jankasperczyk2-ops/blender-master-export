import bpy

from .naming import (
    get_root_empty_name,
    get_collection_name,
    get_parent_collection_name,
    get_geometry_collection_name,
    get_colliders_collection_name,
)

MASTER_COLLECTION_NAME = "MasterExport"

COL_COLOR_MASTER = (0.15, 0.75, 0.15)
COL_COLOR_PARENT = (0.3, 0.5, 1.0)
COL_COLOR_GEOMETRY = (1.0, 0.75, 0.2)
COL_COLOR_COLLIDERS = (1.0, 0.3, 0.3)


def find_or_create_collection(parent_collection, name):
    for child in parent_collection.children:
        if child.name == name:
            return child
    new_col = bpy.data.collections.new(name)
    parent_collection.children.link(new_col)
    return new_col


def _set_collection_color(collection, color_tag):
    collection.color_tag = color_tag


def get_or_create_master_collection(context):
    scene_col = context.scene.collection
    master_col = find_or_create_collection(scene_col, MASTER_COLLECTION_NAME)
    _set_collection_color(master_col, 'COLOR_04')
    return master_col


def setup_asset_hierarchy(context, asset_name):
    master_col = get_or_create_master_collection(context)

    asset_col = find_or_create_collection(master_col, get_collection_name(asset_name))
    _set_collection_color(asset_col, 'COLOR_04')

    parent_col = find_or_create_collection(asset_col, get_parent_collection_name(asset_name))
    _set_collection_color(parent_col, 'COLOR_05')

    geo_col = find_or_create_collection(asset_col, get_geometry_collection_name(asset_name))
    _set_collection_color(geo_col, 'COLOR_06')

    collider_col = find_or_create_collection(asset_col, get_colliders_collection_name(asset_name))
    _set_collection_color(collider_col, 'COLOR_01')

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


def find_asset_from_object(obj):
    if obj is None:
        return None
    root = obj
    while root is not None:
        if root.type == 'EMPTY' and root.name.startswith("SM_"):
            break
        root = root.parent
    if root is None:
        return None
    asset_name = root.name[3:]
    master_col = bpy.data.collections.get(MASTER_COLLECTION_NAME)
    if master_col is None:
        return None
    asset_col = None
    for child in master_col.children:
        if child.name == asset_name:
            asset_col = child
            break
    if asset_col is None:
        return None
    geo_col = None
    collider_col = None
    for child in asset_col.children:
        if child.name == "Geometry":
            geo_col = child
        elif child.name == "Colliders":
            collider_col = child
    return {
        'asset_name': asset_name,
        'asset_col': asset_col,
        'geo_col': geo_col,
        'collider_col': collider_col,
        'root_empty': root,
    }
