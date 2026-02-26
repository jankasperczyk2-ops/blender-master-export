def get_root_empty_name(asset_name):
    return f"SM_{asset_name}"


def get_collision_name(asset_name, index, export_target, collision_prefix='UCX'):
    root_name = get_root_empty_name(asset_name)
    if export_target == 'UNREAL':
        return f"{collision_prefix}_{root_name}_{index:02d}"
    else:
        return f"COL_{root_name}_{index:02d}"


def get_collection_name(asset_name):
    return asset_name


def get_parent_collection_name(asset_name):
    return "Parent"


def get_geometry_collection_name(asset_name):
    return "Geometry"


def get_colliders_collection_name(asset_name):
    return "Colliders"
