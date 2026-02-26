import bpy
import bmesh
from mathutils import Vector

from .naming import get_collision_name, get_root_empty_name


def get_combined_bounds(objects):
    all_coords = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        all_coords.extend(bbox)

    if not all_coords:
        return None, None

    min_co = Vector((
        min(v.x for v in all_coords),
        min(v.y for v in all_coords),
        min(v.z for v in all_coords),
    ))
    max_co = Vector((
        max(v.x for v in all_coords),
        max(v.y for v in all_coords),
        max(v.z for v in all_coords),
    ))
    return min_co, max_co


def create_box_mesh(name, min_co, max_co):
    center = (min_co + max_co) / 2
    size = max_co - min_co

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)

    for v in bm.verts:
        v.co.x = v.co.x * size.x + center.x
        v.co.y = v.co.y * size.y + center.y
        v.co.z = v.co.z * size.z + center.z

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    return obj


def _link_collider(col_obj, collider_col, root_empty):
    collider_col.objects.link(col_obj)
    col_obj.display_type = 'WIRE'
    col_obj.parent = root_empty
    col_obj.matrix_parent_inverse = root_empty.matrix_world.inverted()


def _merge_geometry_copies(context, geo_objects):
    bpy.ops.object.select_all(action='DESELECT')

    temp_objects = []
    for obj in geo_objects:
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        context.scene.collection.objects.link(new_obj)
        new_obj.select_set(True)
        temp_objects.append(new_obj)

    if not temp_objects:
        return None

    context.view_layer.objects.active = temp_objects[0]

    if len(temp_objects) > 1:
        bpy.ops.object.join()

    return context.active_object


def generate_simple_bounding_box(context, geo_objects, asset_name, export_target, collider_col, root_empty):
    clear_colliders(collider_col)

    min_co, max_co = get_combined_bounds(geo_objects)
    if min_co is None:
        return []

    prefix = 'UCX' if export_target == 'UNREAL' else 'COL'
    col_name = get_collision_name(asset_name, 1, export_target, prefix)
    col_obj = create_box_mesh(col_name, min_co, max_co)
    _link_collider(col_obj, collider_col, root_empty)

    return [col_obj]


def generate_multi_box(context, geo_objects, asset_name, export_target, collider_col, root_empty):
    clear_colliders(collider_col)

    merged = _merge_geometry_copies(context, geo_objects)
    if merged is None:
        return []

    bbox = [merged.matrix_world @ Vector(corner) for corner in merged.bound_box]
    min_co = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
    max_co = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))

    mesh_data = merged.data
    bpy.data.objects.remove(merged, do_unlink=True)
    if mesh_data and mesh_data.users == 0:
        bpy.data.meshes.remove(mesh_data)

    size = max_co - min_co
    sizes = [size.x, size.y, size.z]

    max_axis_idx = sizes.index(max(sizes))
    min_axis_val = min(s for s in sizes if s > 0) if any(s > 0 for s in sizes) else 0.001

    if min_axis_val == 0:
        min_axis_val = 0.001

    ratio = sizes[max_axis_idx] / min_axis_val

    if ratio > 1.5:
        num_splits = max(3, min(int(ratio + 0.5), 6))
    else:
        num_splits = 3

    axis_idx = max_axis_idx
    axis_min = min_co[axis_idx]
    axis_max = max_co[axis_idx]
    step = (axis_max - axis_min) / num_splits

    prefix = 'UBX' if export_target == 'UNREAL' else 'COL'
    colliders = []
    for i in range(num_splits):
        seg_min = Vector(min_co)
        seg_max = Vector(max_co)
        seg_min[axis_idx] = axis_min + step * i
        seg_max[axis_idx] = axis_min + step * (i + 1)

        col_name = get_collision_name(asset_name, i + 1, export_target, prefix)
        col_obj = create_box_mesh(col_name, seg_min, seg_max)
        _link_collider(col_obj, collider_col, root_empty)
        colliders.append(col_obj)

    return colliders


def generate_convex_lite(context, geo_objects, asset_name, export_target, collider_col, root_empty):
    clear_colliders(collider_col)

    if not geo_objects:
        return []

    merged = _merge_geometry_copies(context, geo_objects)
    if merged is None:
        return []

    decimate = merged.modifiers.new(name="Decimate", type='DECIMATE')
    decimate.ratio = 0.15

    bpy.ops.object.select_all(action='DESELECT')
    merged.select_set(True)
    context.view_layer.objects.active = merged
    bpy.ops.object.modifier_apply(modifier=decimate.name)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')

    parts = list(context.selected_objects)

    if not parts:
        parts = [merged]

    prefix = 'UCX' if export_target == 'UNREAL' else 'COL'
    colliders = []
    for i, part in enumerate(parts):
        if part.type != 'MESH':
            mesh_data = part.data if hasattr(part, 'data') else None
            bpy.data.objects.remove(part, do_unlink=True)
            if mesh_data and hasattr(mesh_data, 'users') and mesh_data.users == 0:
                bpy.data.meshes.remove(mesh_data)
            continue

        col_name = get_collision_name(asset_name, i + 1, export_target, prefix)
        part.name = col_name
        part.data.name = col_name

        for col in list(part.users_collection):
            col.objects.unlink(part)
        collider_col.objects.link(part)

        part.display_type = 'WIRE'
        part.parent = root_empty
        part.matrix_parent_inverse = root_empty.matrix_world.inverted()
        colliders.append(part)

    return colliders


def clear_colliders(collider_col):
    for obj in list(collider_col.objects):
        mesh_data = obj.data if obj.type == 'MESH' else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh_data and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)
