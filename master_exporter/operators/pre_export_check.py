import bpy
import bmesh
from bpy.types import Operator
from mathutils import Vector

from ..utils.hierarchy import MASTER_COLLECTION_NAME, find_asset_from_object


def _get_master_collection():
    return bpy.data.collections.get(MASTER_COLLECTION_NAME)


def _get_all_mesh_objects(collection):
    meshes = []
    for obj in collection.objects:
        if obj.type == 'MESH':
            meshes.append(obj)
    for child_col in collection.children:
        meshes.extend(_get_all_mesh_objects(child_col))
    return meshes


def _count_triangles(obj):
    mesh = obj.data
    tri_count = 0
    for poly in mesh.polygons:
        verts = len(poly.vertices)
        if verts >= 3:
            tri_count += verts - 2
    return tri_count


def _count_doubles(obj, threshold=0.0001):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    from mathutils import kdtree
    kd = kdtree.KDTree(len(bm.verts))
    for i, v in enumerate(bm.verts):
        kd.insert(obj.matrix_world @ v.co, i)
    kd.balance()

    double_count = 0
    visited = set()
    for i, v in enumerate(bm.verts):
        if i in visited:
            continue
        co = obj.matrix_world @ v.co
        results = kd.find_range(co, threshold)
        if len(results) > 1:
            double_count += len(results) - 1
            for _, idx, _ in results:
                visited.add(idx)

    bm.free()
    return double_count


def _count_flipped_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()

    flipped = 0
    center = Vector((0, 0, 0))
    for v in bm.verts:
        center += v.co
    if bm.verts:
        center /= len(bm.verts)

    for face in bm.faces:
        face_center = face.calc_center_median()
        outward = (face_center - center).normalized()
        if face.normal.dot(outward) < 0:
            flipped += 1

    bm.free()
    return flipped


def _check_scale(obj):
    s = obj.scale
    return not (abs(s.x - 1.0) < 0.001 and abs(s.y - 1.0) < 0.001 and abs(s.z - 1.0) < 0.001)


def _check_rotation(obj):
    r = obj.rotation_euler
    return not (abs(r.x) < 0.001 and abs(r.y) < 0.001 and abs(r.z) < 0.001)


def _is_collider_name(name):
    return (
        name.startswith("UCX_") or name.startswith("UBX_") or
        name.startswith("USP_") or name.startswith("UCP_") or
        name.startswith("COL_")
    )


def run_auto_check(context):
    props = context.scene.master_export
    props.check_results.clear()
    props.check_total_tris = 0
    props.check_issues_found = 0
    props.check_has_colliders = False

    active = context.active_object
    asset_info = find_asset_from_object(active)
    if asset_info is None:
        return

    geo_col = asset_info.get('geo_col')
    collider_col = asset_info.get('collider_col')

    if geo_col is None:
        return

    geometry_meshes = [obj for obj in geo_col.objects if obj.type == 'MESH']

    total_tris = 0
    issues = 0

    for obj in geometry_meshes:
        result = props.check_results.add()
        result.obj_name = obj.name

        tri_count = _count_triangles(obj)
        result.tri_count = tri_count
        total_tris += tri_count

        doubles = _count_doubles(obj)
        result.has_doubles = doubles > 0
        result.doubles_count = doubles
        if doubles > 0:
            issues += 1

        flipped = _count_flipped_normals(obj)
        result.has_flipped = flipped > 0
        result.flipped_count = flipped
        if flipped > 0:
            issues += 1

        bad_scale = _check_scale(obj)
        result.bad_scale = bad_scale
        result.scale_values = f"{obj.scale.x:.3f}, {obj.scale.y:.3f}, {obj.scale.z:.3f}"
        if bad_scale:
            issues += 1

        bad_rot = _check_rotation(obj)
        result.bad_rotation = bad_rot
        result.rotation_values = f"{obj.rotation_euler.x:.3f}, {obj.rotation_euler.y:.3f}, {obj.rotation_euler.z:.3f}"
        if bad_rot:
            issues += 1

    has_colliders = collider_col is not None and len(collider_col.objects) > 0
    props.check_has_colliders = has_colliders
    if not has_colliders:
        issues += 1

    props.check_total_tris = total_tris
    props.check_issues_found = issues


def _get_geometry_targets(context, obj_name=""):
    active = context.active_object
    asset_info = find_asset_from_object(active)

    if asset_info is None:
        master_col = _get_master_collection()
        if master_col is None:
            return []
        all_meshes = _get_all_mesh_objects(master_col)
        targets = [obj for obj in all_meshes if not _is_collider_name(obj.name)]
    else:
        geo_col = asset_info.get('geo_col')
        if geo_col is None:
            return []
        targets = [obj for obj in geo_col.objects if obj.type == 'MESH']

    if obj_name:
        targets = [obj for obj in targets if obj.name == obj_name]

    return targets


def _poll_asset_selected(context):
    active = context.active_object
    return find_asset_from_object(active) is not None


class MASTEREXPORT_OT_FixDoubles(Operator):
    bl_idname = "master_export.fix_doubles"
    bl_label = "Fix Double Vertices"
    bl_description = "Merge vertices by distance"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return _poll_asset_selected(context)

    def execute(self, context):
        targets = _get_geometry_targets(context, self.obj_name)
        if not targets:
            self.report({'WARNING'}, "No geometry meshes found")
            return {'CANCELLED'}

        fixed = 0
        for obj in targets:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
            fixed += 1

        run_auto_check(context)
        self.report({'INFO'}, f"Fixed doubles on {fixed} mesh(es)")
        return {'FINISHED'}


class MASTEREXPORT_OT_FixNormals(Operator):
    bl_idname = "master_export.fix_normals"
    bl_label = "Fix Normals"
    bl_description = "Recalculate normals outside"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return _poll_asset_selected(context)

    def execute(self, context):
        targets = _get_geometry_targets(context, self.obj_name)
        if not targets:
            self.report({'WARNING'}, "No geometry meshes found")
            return {'CANCELLED'}

        fixed = 0
        for obj in targets:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
            fixed += 1

        run_auto_check(context)
        self.report({'INFO'}, f"Fixed normals on {fixed} mesh(es)")
        return {'FINISHED'}


class MASTEREXPORT_OT_FixTransforms(Operator):
    bl_idname = "master_export.fix_transforms"
    bl_label = "Apply Transforms"
    bl_description = "Apply rotation and scale"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty(default="")

    @classmethod
    def poll(cls, context):
        return _poll_asset_selected(context)

    def execute(self, context):
        targets = _get_geometry_targets(context, self.obj_name)
        if not targets:
            self.report({'WARNING'}, "No geometry meshes found")
            return {'CANCELLED'}

        prev_active = context.active_object
        bpy.ops.object.select_all(action='DESELECT')
        for obj in targets:
            obj.select_set(True)

        if targets:
            context.view_layer.objects.active = targets[0]
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        bpy.ops.object.select_all(action='DESELECT')
        if prev_active:
            prev_active.select_set(True)
            context.view_layer.objects.active = prev_active

        run_auto_check(context)
        self.report({'INFO'}, f"Applied transforms on {len(targets)} mesh(es)")
        return {'FINISHED'}


class MASTEREXPORT_OT_FixAll(Operator):
    bl_idname = "master_export.fix_all"
    bl_label = "Fix All Issues"
    bl_description = "Fix all detected issues at once"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_asset_selected(context)

    def execute(self, context):
        bpy.ops.master_export.fix_doubles()
        bpy.ops.master_export.fix_normals()
        bpy.ops.master_export.fix_transforms()

        self.report({'INFO'}, "All fixes applied")
        return {'FINISHED'}
