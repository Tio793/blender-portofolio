import bpy
import mathutils

ADDON_PREFIX = "Addon_SidePanel_"

def clean_existing_panels():
    """Hanya menghapus panel penutup dari eksekusi sebelumnya jika ada."""
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith(ADDON_PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)

def get_or_create_mat(mat_name, color):
    """Gunakan material yang menyatu dengan warna rangka utama."""
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if 'Base Color' in bsdf.inputs: bsdf.inputs['Base Color'].default_value = color
            if 'Metallic' in bsdf.inputs: bsdf.inputs['Metallic'].default_value = 0.6
            if 'Roughness' in bsdf.inputs: bsdf.inputs['Roughness'].default_value = 0.5
    return mat

def create_panel(name, loc, scale, mat):
    """Membuat objek flat panel dengan sedikit bevel agar pinggirannya tidak tajam."""
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.active_object
    obj.name = f"{ADDON_PREFIX}{name}"
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.005
    bevel.segments = 3
    return obj

def build_and_animate_panels():
    clean_existing_panels()

    # Menggunakan warna abu-abu gelap industrial
    mat_panel = get_or_create_mat("Mat_HQ_SidePanel", (0.12, 0.12, 0.12, 1.0))

    # Kalkulasi ukuran agar pas di sela-sela pilar penyangga tanpa menabrak kontrol panel
    z_loc = 0.875
    z_scale = 0.81 # Diskalakan sedikit lebih kecil dari tinggi pilar untuk celah sirkulasi udara

    # 1. PEMBUATAN OBJEK PANEL
    # X_scale 1.31 agar pas di antara pilar kiri dan kanan
    p_front = create_panel("Front", (0, -0.45, z_loc), (1.31, 0.01, z_scale), mat_panel)
    p_back = create_panel("Back", (0, 0.45, z_loc), (1.31, 0.01, z_scale), mat_panel)
    
    # Y_scale 0.41 agar pas di antara pilar depan dan belakang
    p_left = create_panel("Left", (-1.35, 0, z_loc), (0.01, 0.41, z_scale), mat_panel)
    p_right = create_panel("Right", (1.35, 0, z_loc), (0.01, 0.41, z_scale), mat_panel)

    # 2. LOGIKA ANIMASI
    # Panel terlempar paling jauh (2.5 hingga 3.0 meter) karena berada di lapisan paling luar
    panels_direction = {
        p_front: mathutils.Vector((0, -2.5, 0)),
        p_back: mathutils.Vector((0, 2.5, 0)),
        p_left: mathutils.Vector((-3.0, 0, 0)),
        p_right: mathutils.Vector((3.0, 0, 0))
    }

    for obj, offset in panels_direction.items():
        orig_loc = obj.location.copy()
        exploded_loc = orig_loc + offset

        obj.animation_data_clear()

        # Frame 1 - 40: Panel mengambang jauh di luar
        obj.location = exploded_loc
        obj.keyframe_insert(data_path="location", frame=1)
        obj.keyframe_insert(data_path="location", frame=40)

        # Frame 180 - 240: Panel mengunci rapat ke rangka genset
        obj.location = orig_loc
        obj.keyframe_insert(data_path="location", frame=180)
        obj.keyframe_insert(data_path="location", frame=240)

if __name__ == "__main__":
    print("\nMenambahkan Papan Penutup (Silent Canopy)...")
    build_and_animate_panels()
    bpy.ops.object.select_all(action='DESELECT')
    print("Selesai! Silakan cek Timeline Anda.")