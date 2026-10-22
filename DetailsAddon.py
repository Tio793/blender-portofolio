import bpy
import math
from mathutils import Vector

# ==============================================================================
# 1. KONFIGURASI AWAL & IDEMPOTENSI
# ==============================================================================
ADDON_PREFIX = "Addon_Details_"

def clean_existing_details():
    """Hanya menghapus objek detail yang dibuat oleh skrip ini sebelumnya."""
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith(ADDON_PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)

# ==============================================================================
# 2. HELPER FUNCTIONS UNTUK PEMODELAN MATERIAL & OBJEK
# ==============================================================================
def get_or_create_mat(mat_name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if 'Base Color' in bsdf.inputs: bsdf.inputs['Base Color'].default_value = color
            if 'Metallic' in bsdf.inputs: bsdf.inputs['Metallic'].default_value = metallic
            if 'Roughness' in bsdf.inputs: bsdf.inputs['Roughness'].default_value = roughness
    return mat

def get_bounding_box_limits(obj):
    """Membaca batas terluar objek di World Space."""
    world_bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    max_z = max(v.z for v in world_bbox)
    min_y = min(v.y for v in world_bbox)
    return max_z, min_y

def create_hex_bolt(name, loc, size):
    """Membuat baut kepala segi enam (hexagonal bolt)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=size, depth=size, location=loc)
    obj = bpy.context.active_object
    obj.name = f"{ADDON_PREFIX}{name}"
    
    # Gunakan material baut yang sudah ada atau buat fallback
    mat = bpy.data.materials.get("Mat_HQ_Bolt") or get_or_create_mat("Mat_Details_Bolt", (0.8, 0.8, 0.8, 1), 0.9, 0.3)
    obj.data.materials.append(mat)
    
    # Bevel sedikit agar tidak terlalu tajam
    bpy.ops.object.shade_smooth()
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = size * 0.1
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'
    return obj

def create_placard(name, text, loc, rot, scale, base_color, text_color):
    """Membuat pelat timbul dengan teks 3D (misal: pelat merek atau peringatan)."""
    # 1. Base Plate (Latar belakang)
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    base = bpy.context.active_object
    base.name = f"{ADDON_PREFIX}{name}_Plate"
    base.scale = scale
    
    mat_base = get_or_create_mat(f"Mat_Details_Plate_{name}", base_color, metallic=0.2, roughness=0.6)
    base.data.materials.append(mat_base)
    
    # 2. Text (Tulisan)
    # Majukan posisi teks sedikit dari base plate agar tidak bertumpuk (Z-fighting)
    # rotasi mengikuti rotasi base, digeser sepanjang sumbu lokal Z
    text_offset_loc = base.matrix_world @ Vector((0, 0, scale[2] + 0.005))
    
    bpy.ops.object.text_add(location=text_offset_loc, rotation=rot)
    txt = bpy.context.active_object
    txt.name = f"{ADDON_PREFIX}{name}_Text"
    txt.data.body = text
    txt.data.align_x = 'CENTER'
    txt.data.align_y = 'CENTER'
    txt.data.extrude = 0.002 # Ketebalan teks
    
    # Sesuaikan ukuran font terhadap ukuran base plate
    txt_scale = scale[0] * 1.5 
    txt.scale = (txt_scale, txt_scale, txt_scale)
    
    mat_text = get_or_create_mat(f"Mat_Details_Text_{name}", text_color, metallic=0.0, roughness=0.8)
    txt.data.materials.append(mat_text)

# ==============================================================================
# 3. PROSES PEMBANGUNAN DETAIL
# ==============================================================================
def apply_mechanical_details():
    print("[*] Menganalisis geometri untuk penempatan detail...")
    
    # ---------------------------------------------------------
    # DETAIL 1: BAUT TIANG PENYANGGA (PILLAR BOLTS)
    # ---------------------------------------------------------
    # Kita akan membaut dasar tiang penyangga ke rangka bawah
    frame = bpy.data.objects.get("Frame_Bottom")
    frame_top_z = get_bounding_box_limits(frame)[0] if frame else 0.1
    
    pillars = ["Addon_Pillar_FL", "Addon_Pillar_FR", "Addon_Pillar_BL", "Addon_Pillar_BR"]
    bolt_offset = 0.045 # Jarak baut dari tengah tiang
    
    for p_name in pillars:
        pillar = bpy.data.objects.get(p_name)
        if pillar:
            p_x, p_y = pillar.location.x, pillar.location.y
            # Buat 4 baut mengelilingi pangkal setiap tiang
            create_hex_bolt(f"Bolt_{p_name}_1", (p_x + bolt_offset, p_y + bolt_offset, frame_top_z + 0.01), 0.008)
            create_hex_bolt(f"Bolt_{p_name}_2", (p_x - bolt_offset, p_y + bolt_offset, frame_top_z + 0.01), 0.008)
            create_hex_bolt(f"Bolt_{p_name}_3", (p_x + bolt_offset, p_y - bolt_offset, frame_top_z + 0.01), 0.008)
            create_hex_bolt(f"Bolt_{p_name}_4", (p_x - bolt_offset, p_y - bolt_offset, frame_top_z + 0.01), 0.008)

    # ---------------------------------------------------------
    # DETAIL 2: LABEL PERINGATAN PANAS KNALPOT (HOT EXHAUST)
    # ---------------------------------------------------------
    # Cari atap kanopi untuk menempelkan stiker peringatan di tepi terluarnya
    roof = bpy.data.objects.get("Addon_Canopy_Roof")
    exhaust = bpy.data.objects.get("Exhaust_Pipe") or bpy.data.objects.get("Muffler")
    
    if roof and exhaust:
        # Tempatkan di atap bagian depan (-Y), sejajar dengan sumbu X dari knalpot
        roof_z, roof_min_y = get_bounding_box_limits(roof)
        exhaust_x = exhaust.location.x
        
        # Dimensi plate: (X, Y, Ketebalan Z) -> Ingat di rotasi 90 derajat!
        plate_scale = (0.08, 0.04, 0.001)
        create_placard("Warning_Hot", "HOT\nSURFACE", 
                       loc=(exhaust_x, roof_min_y - 0.001, roof_z - 0.015), 
                       rot=(math.radians(90), 0, 0), # Menghadap -Y
                       scale=plate_scale, 
                       base_color=(0.9, 0.8, 0.0, 1.0), # Kuning Industri
                       text_color=(0.0, 0.0, 0.0, 1.0)) # Hitam
    
    # ---------------------------------------------------------
    # DETAIL 3: IDENTITAS PRODUK (MANUFACTURER ID PLATE)
    # ---------------------------------------------------------
    if frame:
        _, frame_min_y = get_bounding_box_limits(frame)
        plate_scale = (0.12, 0.06, 0.002)
        create_placard("ID_Plate", "HEAVY DUTY\nDIESEL GEN-SET", 
                       loc=(0.0, frame_min_y - 0.001, frame_top_z - 0.02), 
                       rot=(math.radians(90), 0, 0), 
                       scale=plate_scale, 
                       base_color=(0.02, 0.02, 0.02, 1.0), # Hitam/Logam Gelap
                       text_color=(0.8, 0.8, 0.8, 1.0))    # Teks Putih/Perak

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print("\n--- MENAMBAHKAN DETAIL MEKANIS & LABELING ---")
    
    clean_existing_details()
    apply_mechanical_details()
    
    bpy.ops.object.select_all(action='DESELECT')
    print("✅ Penambahan Baut Struktural dan Label Identitas Selesai!")