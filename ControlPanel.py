import bpy
import math
from mathutils import Vector

# ==============================================================================
# 1. KONFIGURASI AWAL & IDEMPOTENSI
# ==============================================================================
ADDON_PREFIX = "Addon_ControlPanel_"

def clean_existing_panel():
    """Hanya menghapus objek dengan awalan Addon_ControlPanel_"""
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith(ADDON_PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)

# ==============================================================================
# 2. HELPER FUNCTIONS UNTUK PEMODELAN
# ==============================================================================
def get_or_create_mat(mat_name, color, emit=False, metallic=0.5, roughness=0.5):
    """Mencari material lama atau membuat material baru dengan nama konsisten."""
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if 'Base Color' in bsdf.inputs:
            bsdf.inputs['Base Color'].default_value = color
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = metallic
        if 'Roughness' in bsdf.inputs:
            bsdf.inputs['Roughness'].default_value = roughness
            
        if emit:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = color
            elif 'Emission' in bsdf.inputs:  # Fallback
                bsdf.inputs['Emission'].default_value = color
            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value = 3.0
    return mat

def create_cube(name, loc, scale, mat):
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
    bevel.limit_method = 'ANGLE'
    return obj

def create_cylinder(name, loc, radius, depth, rot=(0,0,0), mat=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = f"{ADDON_PREFIX}{name}"
    if mat:
        obj.data.materials.append(mat)
        
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.002
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'
    return obj

def get_canopy_y_boundary():
    """Mencari tepi terluar kanopi (-Y) agar panel tidak bertabrakan dengan komponen dalam."""
    roof = bpy.data.objects.get("Addon_Canopy_Roof")
    if roof:
        world_bbox = [roof.matrix_world @ Vector(corner) for corner in roof.bound_box]
        min_y = min(v.y for v in world_bbox)
        return min_y
    return -0.55 # Fallback default jika atap tidak ditemukan

# ==============================================================================
# 3. PROSES PEMBUATAN PANEL KONTROL
# ==============================================================================
def build_exterior_panel():
    # 1. Tentukan Titik Jangkar (Anchor Point)
    min_y = get_canopy_y_boundary()
    
    # Koordinat pusat kotak panel
    pos_x = 0.6            # Posisi di sisi alternator (menjauhi panas mesin di sisi negatif)
    pos_z = 1.15           # Tinggi ergonomis untuk operator
    panel_thickness = 0.04 # Setengah ketebalan panel sebenarnya
    
    # Letakkan persis di luar tepi kanopi
    pos_y = min_y - panel_thickness 
    
    # 2. Siapkan Material
    mat_casing = get_or_create_mat("Mat_HQ_PanelCasing", (0.02, 0.02, 0.02, 1.0), metallic=0.7, roughness=0.3)
    mat_screen = get_or_create_mat("Mat_HQ_LCD", (0.01, 0.2, 0.8, 1.0), emit=True, metallic=0.0, roughness=0.2)
    mat_btn_start = get_or_create_mat("Mat_HQ_BtnStart", (0.1, 0.8, 0.1, 1.0), metallic=0.1, roughness=0.4)
    mat_btn_stop = get_or_create_mat("Mat_HQ_BtnStop", (0.8, 0.05, 0.05, 1.0), metallic=0.1, roughness=0.4)
    mat_estop = get_or_create_mat("Mat_HQ_EStop", (0.9, 0.0, 0.0, 1.0), metallic=0.3, roughness=0.5)
    mat_ind_ok = get_or_create_mat("Mat_HQ_IndGreen", (0.2, 1.0, 0.2, 1.0), emit=True, metallic=0.2)
    mat_ind_warn = get_or_create_mat("Mat_HQ_IndYellow", (1.0, 0.8, 0.1, 1.0), emit=True, metallic=0.2)
    mat_bolt = get_or_create_mat("Mat_HQ_Bolt", (0.8, 0.8, 0.8, 1.0), metallic=0.9, roughness=0.2)

    # 3. Buat Casing Utama Panel
    # Scale: X (Lebar), Y (Ketebalan menonjol keluar), Z (Tinggi)
    casing = create_cube("MainCasing", (pos_x, pos_y, pos_z), (0.22, panel_thickness, 0.35), mat_casing)
    
    # Hitung permukaan depan panel agar tombol menempel pas di permukaannya
    front_y = pos_y - panel_thickness 
    
    # Putaran standar tombol: menghadap ke arah Y negatif (keluar ke arah operator)
    btn_rot = (math.radians(90), 0, 0)

    # 4. Layar Digital (Digital Controller Screen)
    create_cube("Screen_LCD", (pos_x, front_y - 0.002, pos_z + 0.15), (0.15, 0.005, 0.08), mat_screen)
    
    # Frame/Bingkai Layar (sedikit lebih besar dari layar, warna gelap)
    mat_frame = get_or_create_mat("Mat_HQ_ScreenFrame", (0.01, 0.01, 0.01, 1.0), metallic=0.3, roughness=0.8)
    create_cube("Screen_Frame", (pos_x, front_y + 0.001, pos_z + 0.15), (0.16, 0.002, 0.09), mat_frame)

    # 5. Tombol Start & Stop (Kiri Bawah)
    create_cylinder("Btn_Start", (pos_x - 0.12, front_y, pos_z - 0.05), radius=0.018, depth=0.01, rot=btn_rot, mat=mat_btn_start)
    create_cylinder("Btn_Stop", (pos_x - 0.05, front_y, pos_z - 0.05), radius=0.018, depth=0.01, rot=btn_rot, mat=mat_btn_stop)

    # 6. Emergency Stop (Tombol Jamur Besar di Kanan Bawah)
    # Base kuning (Standar industri untuk E-Stop)
    mat_estop_base = get_or_create_mat("Mat_HQ_EStopBase", (0.9, 0.8, 0.0, 1.0), metallic=0.1, roughness=0.4)
    create_cylinder("EStop_Base", (pos_x + 0.1, front_y, pos_z - 0.15), radius=0.035, depth=0.005, rot=btn_rot, mat=mat_estop_base)
    # Tombol merah menonjol
    create_cylinder("EStop_Button", (pos_x + 0.1, front_y - 0.015, pos_z - 0.15), radius=0.025, depth=0.02, rot=btn_rot, mat=mat_estop)

    # 7. Lampu Indikator (Status Lights di bawah layar)
    create_cylinder("Ind_Power", (pos_x - 0.08, front_y, pos_z + 0.04), radius=0.008, depth=0.005, rot=btn_rot, mat=mat_ind_ok)
    create_cylinder("Ind_Warning", (pos_x, front_y, pos_z + 0.04), radius=0.008, depth=0.005, rot=btn_rot, mat=mat_ind_warn)
    
    # 8. Baut Sudut Casing (4 Sudut)
    bolt_x = 0.19 # Jarak X dari titik tengah
    bolt_z = 0.31 # Jarak Z dari titik tengah
    for bx in [-bolt_x, bolt_x]:
        for bz in [-bolt_z, bolt_z]:
            create_cylinder(f"Bolt_{bx}_{bz}", (pos_x + bx, front_y + 0.001, pos_z + bz), radius=0.006, depth=0.003, rot=btn_rot, mat=mat_bolt)

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print("\n--- MEMASANG PANEL KONTROL EKSTERIOR ---")
    
    # 1. Bersihkan komponen panel dari run sebelumnya agar idempoten
    clean_existing_panel()
    
    # 2. Rancang dan letakkan panel baru
    build_exterior_panel()
    
    # 3. Rapikan state objek agar viewport tidak semrawut
    bpy.ops.object.select_all(action='DESELECT')
    
    print("✅ Pemasangan Panel Kontrol Eksterior Selesai! Cek sisi luar rangka.")