import bpy
import bmesh
from bpy.types import Operator
from mathutils import Vector

from ..utils.hierarchy import MASTER_COLLECTION_NAME


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


def _has_colliders_in_collection(collection):
    for child_col in collection.children:
        if child_col.name == "Colliders":
            if len(child_col.objects) > 0:
                return True
        if _has_colliders_in_collection(child_col):
            return True
    return False


class MASTEREXPORT_OT_RunCheck(Operator):
    bl_idname = "master_export.run_check"
    bl_label = "Run Export Check"
    bl_description = "Analyze all meshes in MasterExport for issues"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.master_export

        master_col = _get_master_collection()
        if master_col is None:
            self.report({'ERROR'}, "MasterExport collection not found. Run Set Export first.")
            return {'CANCELLED'}

        props.check_results.clear()

        mesh_objects = _get_all_mesh_objects(master_col)

        is_collider_name = lambda n: (
            n.startswith("UCX_") or n.startswith("UBX_") or
            n.startswith("USP_") or n.startswith("UCP_") or
            n.startswith("COL_")
        )
        geometry_meshes = [obj for obj in mesh_objects if not is_collider_name(obj.name)]

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

        props.check_has_colliders = _has_colliders_in_collection(master_col)
        if not props.check_has_colliders:
            issues += 1

        props.check_total_tris = total_tris
        props.check_issues_found = issues
        props.check_performed = True

        self.report({'INFO'}, f"Check complete: {len(geometry_meshes)} meshes, {total_tris} tris, {issues} issue(s)")
        return {'FINISHED'}


class MASTEREXPORT_OT_FixDoubles(Operator):
    bl_idname = "master_export.fix_doubles"
    bl_label = "Fix Double Vertices"
    bl_description = "Merge vertices by distance on all geometry meshes"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        master_col = _get_master_collection()
        if master_col is None:
            return {'CANCELLED'}

        if self.obj_name:
            targets = [bpy.data.objects.get(self.obj_name)]
            targets = [t for t in targets if t and t.type == 'MESH']
        else:
            targets = _get_all_mesh_objects(master_col)
            targets = [obj for obj in targets if obj.type == 'MESH']

        fixed = 0
        for obj in targets:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            result = bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
            removed = len(result.get('verts', []))
            if removed is None:
                removed = 0
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
            fixed += 1

        self.report({'INFO'}, f"Fixed doubles on {fixed} mesh(es)")
        return {'FINISHED'}


class MASTEREXPORT_OT_FixNormals(Operator):
    bl_idname = "master_export.fix_normals"
    bl_label = "Fix Normals"
    bl_description = "Recalculate normals outside on all geometry meshes"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        master_col = _get_master_collection()
        if master_col is None:
            return {'CANCELLED'}

        if self.obj_name:
            targets = [bpy.data.objects.get(self.obj_name)]
            targets = [t for t in targets if t and t.type == 'MESH']
        else:
            targets = _get_all_mesh_objects(master_col)
            targets = [obj for obj in targets if obj.type == 'MESH']

        fixed = 0
        for obj in targets:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()
            fixed += 1

        self.report({'INFO'}, f"Fixed normals on {fixed} mesh(es)")
        return {'FINISHED'}


class MASTEREXPORT_OT_FixTransforms(Operator):
    bl_idname = "master_export.fix_transforms"
    bl_label = "Apply Transforms"
    bl_description = "Apply rotation and scale on all geometry meshes"
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        master_col = _get_master_collection()
        if master_col is None:
            return {'CANCELLED'}

        if self.obj_name:
            targets = [bpy.data.objects.get(self.obj_name)]
            targets = [t for t in targets if t and t.type == 'MESH']
        else:
            targets = _get_all_mesh_objects(master_col)
            targets = [obj for obj in targets if obj.type == 'MESH']

        bpy.ops.object.select_all(action='DESELECT')
        for obj in targets:
            obj.select_set(True)

        if targets:
            context.view_layer.objects.active = targets[0]
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        bpy.ops.object.select_all(action='DESELECT')

        self.report({'INFO'}, f"Applied transforms on {len(targets)} mesh(es)")
        return {'FINISHED'}


class MASTEREXPORT_OT_FixAll(Operator):
    bl_idname = "master_export.fix_all"
    bl_label = "Fix All Issues"
    bl_description = "Fix all detected issues at once"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.master_export.fix_doubles()
        bpy.ops.master_export.fix_normals()
        bpy.ops.master_export.fix_transforms()
        bpy.ops.master_export.run_check()

        self.report({'INFO'}, "All fixes applied and re-checked")
        return {'FINISHED'}
