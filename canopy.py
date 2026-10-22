import bpy
import math

# ==============================================================================
# 1. DAFTAR OBJEK BARU (Untuk mencegah duplikasi)
# ==============================================================================
# Semua objek yang dibuat skrip ini dicatat di sini
NEW_PARTS = [
    "Addon_Canopy_Roof",
    "Addon_Lifting_Eye",
    "Addon_Pillar_FL", "Addon_Pillar_FR", 
    "Addon_Pillar_BL", "Addon_Pillar_BR"
]

def clean_new_parts():
    """Hanya menghapus objek baru dari skrip ini jika sudah ada di scene."""
    for part_name in NEW_PARTS:
        obj = bpy.data.objects.get(part_name)
        if obj:
            # Hapus objek dari memori Blender tanpa menyentuh objek lain
            bpy.data.objects.remove(obj, do_unlink=True)

# ==============================================================================
# 2. HELPER FUNCTIONS UNTUK PEMODELAN
# ==============================================================================
def get_existing_material(mat_name, fallback_color=(0.12, 0.12, 0.12, 1.0)):
    """Mencari material yang sudah ada (dari skrip sebelumnya), atau membuat baru jika tidak ada."""
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = fallback_color
            bsdf.inputs['Metallic'].default_value = 0.6
            bsdf.inputs['Roughness'].default_value = 0.45
    return mat

def create_cube(name, loc, scale, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    
    # Tambahkan Bevel modifier agar ujungnya tidak terlalu tajam (realistis)
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.01
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'
    return obj

def create_torus(name, loc, rot, major_radius, minor_radius, mat):
    bpy.ops.mesh.primitive_torus_add(location=loc, rotation=rot, major_radius=major_radius, minor_radius=minor_radius)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return obj

# ==============================================================================
# 3. PROSES PEMBUATAN KOMPONEN TAMBAHAN
# ==============================================================================
def build_canopy_addon():
    # Ambil material dari skrip sebelumnya, prioritaskan material yang sudah di-upgrade
    mat_frame = bpy.data.materials.get("Mat_HQ_Frame") or get_existing_material("Mat_Frame")
    mat_metal = bpy.data.materials.get("Mat_HQ_Bolt") or get_existing_material("Mat_Metal", (0.8, 0.8, 0.8, 1.0))

    # 1. Atap Pelindung (Canopy Roof)
    # Diposisikan di atas generator (Z = 1.7)
    create_cube(NEW_PARTS[0], loc=(0, 0, 1.7), scale=(1.45, 0.55, 0.03), mat=mat_frame)

    # 2. Kait Pengangkat (Lifting Eye) untuk Crane
    # Detail krusial untuk genset kelas industri
    create_torus(NEW_PARTS[1], loc=(0, 0, 1.75), rot=(math.radians(90), 0, 0), major_radius=0.08, minor_radius=0.02, mat=mat_metal)

    # 3. Tiang Penyangga (Pillars)
    # 4 tiang yang menghubungkan rangka bawah (Z=0.05) ke atap (Z=1.7)
    # Z location tiang = (1.7 - 0.05) / 2 + 0.05 = 0.875
    # Tinggi tiang = (1.7 - 0.05) / 2 = 0.825 (karena scale cube adalah radius/setengah tinggi)
    
    pillar_z_loc = 0.875
    pillar_z_scale = 0.825
    
    pillar_positions = [
        (NEW_PARTS[2], -1.35, 0.45),  # Front Left
        (NEW_PARTS[3], 1.35, 0.45),   # Front Right
        (NEW_PARTS[4], -1.35, -0.45), # Back Left
        (NEW_PARTS[5], 1.35, -0.45),  # Back Right
    ]

    for name, x, y in pillar_positions:
        create_cube(name, loc=(x, y, pillar_z_loc), scale=(0.04, 0.04, pillar_z_scale), mat=mat_frame)

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print("\n--- MENAMBAHKAN CANOPY & LIFTING EYE ---")
    
    # 1. Bersihkan versi lama dari komponen baru (jika ada) untuk mencegah duplikasi
    clean_new_parts()
    
    # 2. Bangun komponen tambahan
    build_canopy_addon()
    
    # Memastikan objek aktif tidak mengganggu navigasi user
    bpy.ops.object.select_all(action='DESELECT')
    
    print("✅ Penambahan Canopy dan Tiang berhasil diselesaikan tanpa mengganggu objek lama!")