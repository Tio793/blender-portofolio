import bpy

def get_or_create_material(mat_name, base_color, metallic, roughness, emission_color=None):
    """
    Fungsi helper untuk membuat material baru atau memperbarui material yang sudah ada
    agar tidak terjadi penumpukan material ganda (duplikat).
    """
    # Cari material jika sudah ada, jika belum buat baru
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
    
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    
    # Cari node Principled BSDF
    bsdf = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break
            
    # Jika tidak ada (sangat jarang), buat baru
    if not bsdf:
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    # Set parameter material agar realistis
    # (Kompatibel dengan arsitektur node Principled BSDF Blender 4.0 hingga 5.2.x LTS)
    if 'Base Color' in bsdf.inputs:
        bsdf.inputs['Base Color'].default_value = base_color
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = metallic
    if 'Roughness' in bsdf.inputs:
        bsdf.inputs['Roughness'].default_value = roughness
        
    # Set emisi untuk layar kontrol
    if emission_color:
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emission_color
        elif 'Emission' in bsdf.inputs: # Fallback untuk versi Blender tertentu
            bsdf.inputs['Emission'].default_value = emission_color
            
        if 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Strength'].default_value = 2.5

    return mat

def apply_advanced_materials():
    print("\n--- MEMULAI PROSES UPGRADE MATERIAL ---")
    
    # 1. Definisikan palet material industri yang realistis
    # Format Base Color: (R, G, B, Alpha)
    adv_materials = {
        "Frame": get_or_create_material("Mat_HQ_Frame", (0.12, 0.12, 0.12, 1.0), 0.6, 0.45),
        "Engine": get_or_create_material("Mat_HQ_EngineGreen", (0.1, 0.22, 0.12, 1.0), 0.2, 0.5), # Hijau Industri
        "EngineMetal": get_or_create_material("Mat_HQ_EngineMetal", (0.25, 0.25, 0.25, 1.0), 0.8, 0.35),
        "Alternator": get_or_create_material("Mat_HQ_Alternator", (0.08, 0.08, 0.08, 1.0), 0.7, 0.5),
        "Radiator": get_or_create_material("Mat_HQ_Radiator", (0.03, 0.03, 0.03, 1.0), 0.8, 0.6),
        "Exhaust": get_or_create_material("Mat_HQ_Exhaust", (0.35, 0.32, 0.28, 1.0), 0.9, 0.45), # Logam baja agak kusam
        "FuelTank": get_or_create_material("Mat_HQ_FuelTank", (0.05, 0.05, 0.05, 1.0), 0.5, 0.55),
        "PanelBox": get_or_create_material("Mat_HQ_Panel", (0.04, 0.04, 0.04, 1.0), 0.3, 0.3),
        "Screen": get_or_create_material("Mat_HQ_Screen", (0.0, 0.0, 0.0, 1.0), 0.0, 0.2, emission_color=(0.1, 0.8, 0.2, 1.0)),
        "Button": get_or_create_material("Mat_HQ_Button", (0.7, 0.02, 0.02, 1.0), 0.0, 0.3),
        "Rubber": get_or_create_material("Mat_HQ_Rubber", (0.01, 0.01, 0.01, 1.0), 0.0, 0.85),
        "Bolt": get_or_create_material("Mat_HQ_Bolt", (0.8, 0.8, 0.8, 1.0), 0.95, 0.2), # Logam mengilap
        "Floor": get_or_create_material("Mat_HQ_Floor", (0.2, 0.2, 0.2, 1.0), 0.0, 0.95) # Abu-abu netral matte
    }

    # 2. Peta pencocokan kata kunci (keywords) nama objek ke material
    # Menggunakan huruf kecil (lowercase) untuk pencocokan yang fleksibel
    keyword_mapping = {
        "frame": "Frame",
        "base_fueltank": "FuelTank",
        "rubber": "Rubber",
        "enginemount": "Rubber",
        "engine_block": "Engine",
        "cylinder_head": "EngineMetal",
        "alternator_vent": "EngineMetal",
        "alternator": "Alternator",
        "radiator": "Radiator",
        "fan_hub": "Alternator",
        "fan_blade": "PanelBox", # Plastik keras/logam cat hitam
        "exhaust": "Exhaust",
        "muffler": "Exhaust",
        "control_panel": "PanelBox",
        "panel_screen": "Screen",
        "button": "Button",
        "bolt": "Bolt",
        "floor": "Floor"
    }

    # Untuk melacak komponen apa saja yang berhasil ditemukan
    found_keywords = set()

    # 3. Iterasi semua objek mesh di scene dan terapkan material
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj_name_lower = obj.name.lower()
            
            # Cocokkan nama objek dengan mapping (mengutamakan kecocokan pertama)
            for keyword, mat_key in keyword_mapping.items():
                if keyword in obj_name_lower:
                    material_to_apply = adv_materials[mat_key]
                    
                    # Terapkan material ke objek
                    if len(obj.data.materials) > 0:
                        obj.data.materials[0] = material_to_apply
                    else:
                        obj.data.materials.append(material_to_apply)
                        
                    found_keywords.add(keyword)
                    # Break agar tidak terjadi double-assign jika ada nama gabungan
                    break 

    # 4. Validasi & Peringatan untuk komponen yang hilang
    print("\n[STATUS MATERIAL]")
    for keyword in keyword_mapping.keys():
        if keyword not in found_keywords:
            print(f"⚠️ Peringatan: Objek dengan elemen nama '{keyword}' tidak ditemukan. Material dilewati.")
    
    print("✅ Upgrade material selesai dengan aman!")

if __name__ == "__main__":
    apply_advanced_materials()