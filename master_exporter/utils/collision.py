import bpy
import bmesh
from mathutils import Vector, Matrix
from math import atan2, cos, sin

from .naming import get_collision_name

COLLIDER_COLOR = (0.0, 1.0, 0.0, 1.0)


def _get_world_verts(obj):
    mesh = obj.data
    matrix = obj.matrix_world
    return [matrix @ v.co for v in mesh.vertices]


def _get_all_world_verts(objects):
    verts = []
    for obj in objects:
        if obj.type == 'MESH':
            verts.extend(_get_world_verts(obj))
    return verts


def _compute_covariance(verts):
    n = len(verts)
    if n == 0:
        return Vector((0, 0, 0)), [[0.0] * 3 for _ in range(3)]

    mean = Vector((0, 0, 0))
    for v in verts:
        mean += v
    mean /= n

    cov = [[0.0] * 3 for _ in range(3)]
    for v in verts:
        d = v - mean
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]

    for i in range(3):
        for j in range(3):
            cov[i][j] /= n

    return mean, cov


def _jacobi_eigen_3x3(cov):
    a = [row[:] for row in cov]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]

    for _ in range(50):
        off_diag = abs(a[0][1]) + abs(a[0][2]) + abs(a[1][2])
        if off_diag < 1e-12:
            break

        for p in range(3):
            for q in range(p + 1, 3):
                if abs(a[p][q]) < 1e-14:
                    continue

                theta = 0.5 * atan2(2.0 * a[p][q], a[q][q] - a[p][p])
                c = cos(theta)
                s = sin(theta)

                app = c * c * a[p][p] - 2 * s * c * a[p][q] + s * s * a[q][q]
                aqq = s * s * a[p][p] + 2 * s * c * a[p][q] + c * c * a[q][q]
                a[p][q] = 0.0
                a[q][p] = 0.0
                a[p][p] = app
                a[q][q] = aqq

                for r in range(3):
                    if r == p or r == q:
                        continue
                    arp = c * a[r][p] - s * a[r][q]
                    arq = s * a[r][p] + c * a[r][q]
                    a[r][p] = arp
                    a[p][r] = arp
                    a[r][q] = arq
                    a[q][r] = arq

                for r in range(3):
                    vrp = c * v[r][p] - s * v[r][q]
                    vrq = s * v[r][p] + c * v[r][q]
                    v[r][p] = vrp
                    v[r][q] = vrq

    eigenvalues = [a[i][i] for i in range(3)]
    eigenvectors = [Vector((v[0][i], v[1][i], v[2][i])).normalized() for i in range(3)]

    paired = sorted(zip(eigenvalues, eigenvectors), key=lambda x: -x[0])
    eigenvalues = [p[0] for p in paired]
    eigenvectors = [p[1] for p in paired]

    e0 = eigenvectors[0]
    e1 = eigenvectors[1]
    e2 = e0.cross(e1).normalized()
    e1 = e2.cross(e0).normalized()
    eigenvectors = [e0, e1, e2]

    return eigenvalues, eigenvectors


def _compute_obb(verts):
    if len(verts) < 3:
        if len(verts) == 0:
            return None
        center = verts[0] if len(verts) == 1 else (verts[0] + verts[1]) / 2
        return {
            'center': center,
            'axes': [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))],
            'half_extents': Vector((0.01, 0.01, 0.01)),
        }

    mean, cov = _compute_covariance(verts)
    eigenvalues, axes = _jacobi_eigen_3x3(cov)

    proj_min = [float('inf')] * 3
    proj_max = [float('-inf')] * 3

    for v in verts:
        d = v - mean
        for i in range(3):
            p = d.dot(axes[i])
            if p < proj_min[i]:
                proj_min[i] = p
            if p > proj_max[i]:
                proj_max[i] = p

    center = Vector(mean)
    for i in range(3):
        mid = (proj_min[i] + proj_max[i]) / 2
        center += axes[i] * mid

    half_extents = Vector((
        max((proj_max[i] - proj_min[i]) / 2, 0.001) for i in range(3)
    ))

    return {
        'center': center,
        'axes': axes,
        'half_extents': half_extents,
    }


def _create_obb_mesh(name, obb):
    center = obb['center']
    axes = obb['axes']
    he = obb['half_extents']

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)

    rot = Matrix((
        (axes[0].x, axes[1].x, axes[2].x),
        (axes[0].y, axes[1].y, axes[2].y),
        (axes[0].z, axes[1].z, axes[2].z),
    ))

    for v in bm.verts:
        local = Vector((v.co.x * he.x * 2, v.co.y * he.y * 2, v.co.z * he.z * 2))
        world = rot @ local + center
        v.co = world

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    return obj


def _setup_collider_material():
    mat_name = "MasterExport_Collider"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(mat_name)
    mat.diffuse_color = COLLIDER_COLOR
    mat.roughness = 1.0
    mat.use_nodes = False
    return mat


def _link_collider(col_obj, collider_col, root_empty):
    collider_col.objects.link(col_obj)

    col_obj.display_type = 'WIRE'
    col_obj.color = COLLIDER_COLOR
    col_obj.show_wire = True
    col_obj.show_in_front = True

    mat = _setup_collider_material()
    col_obj.data.materials.clear()
    col_obj.data.materials.append(mat)

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


def _remove_temp_object(obj):
    mesh_data = obj.data if obj.type == 'MESH' else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh_data and mesh_data.users == 0:
        bpy.data.meshes.remove(mesh_data)


def generate_simple_bounding_box(context, geo_objects, asset_name, export_target, collider_col, root_empty):
    clear_colliders(collider_col)

    verts = _get_all_world_verts(geo_objects)
    if not verts:
        return []

    obb = _compute_obb(verts)
    if obb is None:
        return []

    prefix = 'UCX' if export_target == 'UNREAL' else 'COL'
    col_name = get_collision_name(asset_name, 1, export_target, prefix)
    col_obj = _create_obb_mesh(col_name, obb)
    _link_collider(col_obj, collider_col, root_empty)

    return [col_obj]


def _compute_merge_distance(geo_objects):
    all_verts = _get_all_world_verts(geo_objects)
    if not all_verts:
        return 0.1

    min_co = Vector((float('inf'), float('inf'), float('inf')))
    max_co = Vector((float('-inf'), float('-inf'), float('-inf')))
    for v in all_verts:
        for i in range(3):
            if v[i] < min_co[i]:
                min_co[i] = v[i]
            if v[i] > max_co[i]:
                max_co[i] = v[i]

    dims = max_co - min_co
    max_dim = max(dims.x, dims.y, dims.z)
    merge_dist = max_dim * 0.05
    return max(merge_dist, 0.001)


def generate_smart_collider(context, geo_objects, asset_name, export_target,
                            collider_col, root_empty, voxel_size=0.1):
    clear_colliders(collider_col)

    if not geo_objects:
        return []

    merge_dist = _compute_merge_distance(geo_objects)

    merged = _merge_geometry_copies(context, geo_objects)
    if merged is None:
        return []

    bpy.ops.object.select_all(action='DESELECT')
    merged.select_set(True)
    context.view_layer.objects.active = merged

    remesh_mod = merged.modifiers.new(name="VoxelRemesh", type='REMESH')
    remesh_mod.mode = 'VOXEL'
    remesh_mod.voxel_size = voxel_size
    bpy.ops.object.modifier_apply(modifier=remesh_mod.name)

    bm = bmesh.new()
    bm.from_mesh(merged.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_dist)
    bm.to_mesh(merged.data)
    bm.free()
    merged.data.update()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')

    parts = [obj for obj in context.selected_objects if obj.type == 'MESH']
    if not parts:
        parts = [merged]

    convex_parts = []
    for part in parts:
        bpy.ops.object.select_all(action='DESELECT')
        part.select_set(True)
        context.view_layer.objects.active = part

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.convex_hull()
        bpy.ops.object.mode_set(mode='OBJECT')

        convex_parts.append(part)

    prefix = 'UCX' if export_target == 'UNREAL' else 'COL'
    colliders = []

    for i, part in enumerate(convex_parts):
        if part.type != 'MESH':
            _remove_temp_object(part)
            continue

        col_name = get_collision_name(asset_name, i + 1, export_target, prefix)
        part.name = col_name
        part.data.name = col_name

        for col in list(part.users_collection):
            col.objects.unlink(part)

        _link_collider(part, collider_col, root_empty)
        colliders.append(part)

    return colliders


def clear_colliders(collider_col):
    for obj in list(collider_col.objects):
        mesh_data = obj.data if obj.type == 'MESH' else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh_data and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)
