import bpy

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def set_bsdf_value(bsdf, input_name, value):
    """Fungsi aman untuk mengubah nilai input Principled BSDF lintas versi Blender."""
    if input_name in bsdf.inputs:
        bsdf.inputs[input_name].default_value = value
    # Fallback untuk penamaan lama/baru di Blender 4.0 - 5.2.x
    elif input_name == 'Emission Color' and 'Emission' in bsdf.inputs:
        bsdf.inputs['Emission'].default_value = value

def add_cast_iron_bump(mat, bsdf, scale=100.0, strength=0.15):
    """
    Menambahkan tekstur prosedural (Noise) ke Normal/Bump.
    Memberikan ilusi permukaan besi cor (cast metal) yang kasar tanpa menambah poligon.
    """
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 1. Bersihkan node bump/noise lama jika skrip dijalankan ulang (Idempoten)
    for n in list(nodes):
        if n.name in ["Gen_Noise_Tex", "Gen_Bump_Map"]:
            nodes.remove(n)
            
    # 2. Buat Node Noise Texture
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.name = "Gen_Noise_Tex"
    noise.location = (-600, -200)
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 5.0
    
    # 3. Buat Node Bump
    bump = nodes.new(type="ShaderNodeBump")
    bump.name = "Gen_Bump_Map"
    bump.location = (-300, -200)
    bump.inputs['Strength'].default_value = strength
    
    # 4. Hubungkan Node: Noise(Fac) -> Bump(Height) -> Principled BSDF(Normal)
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

# ==============================================================================
# MAIN MATERIAL POLISHING LOGIC
# ==============================================================================
def polish_all_materials():
    print("\n[*] MEMULAI PROSES FINISHING MATERIAL...")
    
    # Iterasi seluruh material yang ada di dalam scene Blender
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
            
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if not bsdf:
            continue
            
        mat_name = mat.name.lower()
        
        # Cegah warna terlalu gelap (pure black) agar detail shading/bayangan tetap terlihat
        if 'Base Color' in bsdf.inputs:
            current_color = list(bsdf.inputs['Base Color'].default_value)
            # Jika R, G, dan B di bawah 0.04, naikkan sedikit (menjadi abu-abu arang)
            if current_color[0] < 0.04 and current_color[1] < 0.04 and current_color[2] < 0.04:
                current_color[0] = current_color[1] = current_color[2] = 0.05
                bsdf.inputs['Base Color'].default_value = current_color

        # -------------------------------------------------------------
        # 1. MATERIAL RANGKA, KANOPI, PANEL, & TANGKI (Painted Metal)
        # -------------------------------------------------------------
        if any(kw in mat_name for kw in ["frame", "panel", "tank", "canopy", "base"]):
            set_bsdf_value(bsdf, 'Metallic', 0.6)
            set_bsdf_value(bsdf, 'Roughness', 0.5) # Semi-matte powder coat
            
        # -------------------------------------------------------------
        # 2. MATERIAL MESIN & ALTERNATOR (Cast Iron / Logam Cor)
        # -------------------------------------------------------------
        elif any(kw in mat_name for kw in ["engine", "alternator"]):
            set_bsdf_value(bsdf, 'Metallic', 0.75)
            set_bsdf_value(bsdf, 'Roughness', 0.55)
            # Berikan tekstur kasar besi cor (skala padat)
            add_cast_iron_bump(mat, bsdf, scale=250.0, strength=0.12)
            
        # -------------------------------------------------------------
        # 3. KNALPOT & MUFFLER (Heated / Rough Metal)
        # -------------------------------------------------------------
        elif any(kw in mat_name for kw in ["exhaust", "muffler"]):
            set_bsdf_value(bsdf, 'Metallic', 0.8)
            set_bsdf_value(bsdf, 'Roughness', 0.7) # Kusam karena panas
            # Tekstur kasar yang lebih besar (logam memuai/berkarat halus)
            add_cast_iron_bump(mat, bsdf, scale=80.0, strength=0.25)
            
        # -------------------------------------------------------------
        # 4. RADIATOR (Dark Matte Metal)
        # -------------------------------------------------------------
        elif "radiator" in mat_name:
            set_bsdf_value(bsdf, 'Metallic', 0.3)
            set_bsdf_value(bsdf, 'Roughness', 0.8)
            
        # -------------------------------------------------------------
        # 5. KABEL, SELANG, KARET (Rubber / Plastic)
        # -------------------------------------------------------------
        elif any(kw in mat_name for kw in ["cable", "hose", "rubber"]):
            set_bsdf_value(bsdf, 'Metallic', 0.0)
            set_bsdf_value(bsdf, 'Roughness', 0.75)
            
        # -------------------------------------------------------------
        # 6. BAUT & KONEKTOR LOGAM (Shiny Metal / Chrome)
        # -------------------------------------------------------------
        elif any(kw in mat_name for kw in ["bolt", "metal", "connector"]):
            set_bsdf_value(bsdf, 'Metallic', 1.0)
            set_bsdf_value(bsdf, 'Roughness', 0.25) # Sangat memantulkan cahaya
            
        # -------------------------------------------------------------
        # 7. LAYAR & LAMPU INDIKATOR (Emissive / Kaca)
        # -------------------------------------------------------------
        elif any(kw in mat_name for kw in ["lcd", "screen", "ind", "glass"]):
            set_bsdf_value(bsdf, 'Metallic', 0.0)
            set_bsdf_value(bsdf, 'Roughness', 0.15) # Mengilap seperti kaca
            # Jika ini material layar/indikator, pastikan menyala
            if "glass" not in mat_name: 
                set_bsdf_value(bsdf, 'Emission Strength', 3.5)

    print("✅ Tahap Finishing Material selesai. Objek kini menggunakan parameter PBR (Physically Based Rendering) yang akurat.")

# ==============================================================================
# EKSEKUSI SKRIP
# ==============================================================================
if __name__ == "__main__":
    polish_all_materials()