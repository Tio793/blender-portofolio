import bpy
import math
from mathutils import Vector

# ==============================================================================
# 1. KONFIGURASI NAMA OBJEK (Untuk Idempotensi/Mencegah Duplikat)
# ==============================================================================
ADDON_PREFIX = "Addon_FuelTank_"
NEW_PARTS = [
    f"{ADDON_PREFIX}FillerNeck",
    f"{ADDON_PREFIX}Cap",
    f"{ADDON_PREFIX}GaugeBase",
    f"{ADDON_PREFIX}GaugeGlass",
    f"{ADDON_PREFIX}BreatherPipe"
]

def clean_existing_addon_parts():
    """Hanya menghapus bagian tangki bahan bakar jika sebelumnya sudah di-generate."""
    for part_name in NEW_PARTS:
        obj = bpy.data.objects.get(part_name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

# ==============================================================================
# 2. HELPER FUNCTIONS UNTUK PEMODELAN DAN MATERIAL
# ==============================================================================
def get_existing_material(mat_name, fallback_color=(0.05, 0.05, 0.05, 1.0), metallic=0.5, roughness=0.5):
    """Mengambil material yang sudah ada, atau membuat baru jika belum ada."""
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if 'Base Color' in bsdf.inputs:
                bsdf.inputs['Base Color'].default_value = fallback_color
            if 'Metallic' in bsdf.inputs:
                bsdf.inputs['Metallic'].default_value = metallic
            if 'Roughness' in bsdf.inputs:
                bsdf.inputs['Roughness'].default_value = roughness
    return mat

def create_cylinder(name, loc, radius, depth, rot=(0,0,0), mat=None):
    """Fungsi helper membuat silinder dengan ujung di-smooth."""
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    
    # Bevel untuk ujung membulat yang lebih realistis
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.005
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(35)
    return obj

def get_top_z_from_bbox(obj):
    """Membaca koordinat Z tertinggi dari Bounding Box sebuah objek di World Space."""
    world_bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    max_z = max(v.z for v in world_bbox)
    return max_z

# ==============================================================================
# 3. PROSES PEMBUATAN DETAIL TANGKI
# ==============================================================================
def build_fuel_tank_details():
    # 1. Cari objek referensi (Base / Rangka)
    base_obj = bpy.data.objects.get("Base_FuelTank") or bpy.data.objects.get("Frame_Bottom")
    
    # 2. Tentukan koordinat dasar
    if base_obj:
        base_z = get_top_z_from_bbox(base_obj)
        print(f"[*] Basis tangki ditemukan. Z atas berada di: {base_z:.3f}")
    else:
        # Fallback jika nama sebelumnya sudah diganti manual oleh user
        base_z = 0.2
        print("[!] Peringatan: Objek base/frame tidak ditemukan. Menggunakan Z default (0.2).")

    # Siapkan material
    mat_metal = get_existing_material("Mat_HQ_Exhaust", (0.35, 0.32, 0.28, 1.0), 0.9, 0.45)
    mat_cap = get_existing_material("Mat_HQ_FuelCap", (0.01, 0.01, 0.01, 1.0), 0.1, 0.8) # Hitam kasar
    mat_glass = get_existing_material("Mat_HQ_GaugeGlass", (0.8, 0.9, 0.9, 0.3), 0.1, 0.1) # Transparan semu

    # Posisi peletakan (Di belakang alternator, dekat sudut kanan belakang rangka)
    # Area ini diasumsikan aman dari mesin (mesin di X=-0.3, alternator di X=0.6)
    pos_x = 1.15
    pos_y = 0.35

    # A. Leher Pengisian Bahan Bakar (Filler Neck)
    neck_height = 0.08
    neck_z = base_z + (neck_height / 2)
    create_cylinder(NEW_PARTS[0], loc=(pos_x, pos_y, neck_z), radius=0.035, depth=neck_height, mat=mat_metal)

    # B. Tutup Tangki (Fuel Cap)
    cap_height = 0.02
    cap_z = base_z + neck_height + (cap_height / 2)
    cap = create_cylinder(NEW_PARTS[1], loc=(pos_x, pos_y, cap_z), radius=0.045, depth=cap_height, mat=mat_cap)
    
    # C. Fuel Level Gauge (Indikator Level Mekanis)
    # Ditempatkan sedikit di sebelah tutup tangki
    gauge_x = pos_x - 0.12
    gauge_y = pos_y
    gauge_base_height = 0.015
    gauge_glass_height = 0.04
    
    create_cylinder(NEW_PARTS[2], loc=(gauge_x, gauge_y, base_z + (gauge_base_height/2)), 
                    radius=0.03, depth=gauge_base_height, mat=mat_metal)
                    
    create_cylinder(NEW_PARTS[3], loc=(gauge_x, gauge_y, base_z + gauge_base_height + (gauge_glass_height/2)), 
                    radius=0.02, depth=gauge_glass_height, mat=mat_glass)

    # D. Breather Pipe (Pipa Udara Tangki) - Penting untuk tangki industri
    breather_x = pos_x + 0.05
    breather_y = pos_y - 0.15
    breather_height = 0.06
    pipe = create_cylinder(NEW_PARTS[4], loc=(breather_x, breather_y, base_z + (breather_height/2)), 
                           radius=0.01, depth=breather_height, mat=mat_metal)
    
    # Sedikit memiringkan pipa breather ke arah luar
    pipe.rotation_euler = (math.radians(-15), math.radians(15), 0)

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print("\n--- MENAMBAHKAN DETAIL TANGKI BAHAN BAKAR (BELLY TANK) ---")
    
    # 1. Hapus versi lama (jika ada) agar tidak terjadi penumpukan
    clean_existing_addon_parts()
    
    # 2. Bangun detail tangki di atas rangka dasar yang sudah ada
    build_fuel_tank_details()
    
    # 3. Bersihkan seleksi objek agar pandangan di viewport rapi
    bpy.ops.object.select_all(action='DESELECT')
    
    print("✅ Penambahan fitur Tangki Bahan Bakar selesai dengan aman!")