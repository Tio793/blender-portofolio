import bpy
import math
import mathutils

# ==============================================================================
# 1. PERSIAPAN SCENE (CLEANUP)
# ==============================================================================
def clean_scene():
    """Menghapus seluruh objek, material, mesh, lampu, dan kamera di scene aktif."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Membersihkan data orphan agar RAM tetap lega
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras]:
        for item in block:
            block.remove(item)

# ==============================================================================
# 2. HELPER FUNCTIONS
# ==============================================================================
def create_material(name, color, metallic=0.0, roughness=0.5, emission=None):
    """Membuat material Principled BSDF."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        if emission:
            bsdf.inputs['Emission Color'].default_value = emission
            bsdf.inputs['Emission Strength'].default_value = 5.0
    return mat

def apply_bevel_and_smooth(obj, width=0.01, segments=3):
    """Menambahkan Bevel modifier dan Shade Smooth."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = width
    bevel.segments = segments
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(35)

def create_cube(name, loc, scale, mat):
    """Membuat objek kubus dasar."""
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    if mat:
        obj.data.materials.append(mat)
    apply_bevel_and_smooth(obj)
    return obj

def create_cylinder(name, loc, radius, depth, rot=(0,0,0), mat=None):
    """Membuat objek silinder."""
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    apply_bevel_and_smooth(obj, width=0.005, segments=2)
    return obj

# ==============================================================================
# 3. SETUP MATERIAL
# ==============================================================================
def setup_materials():
    mats = {}
    mats['frame'] = create_material("Mat_Frame", (0.8, 0.6, 0.0, 1), metallic=0.7, roughness=0.4)
    mats['engine'] = create_material("Mat_Engine", (0.1, 0.1, 0.1, 1), metallic=0.8, roughness=0.6)
    mats['alternator'] = create_material("Mat_Alternator", (0.6, 0.6, 0.6, 1), metallic=0.9, roughness=0.3)
    mats['radiator'] = create_material("Mat_Radiator", (0.02, 0.02, 0.02, 1), metallic=0.5, roughness=0.8)
    mats['exhaust'] = create_material("Mat_Exhaust", (0.2, 0.15, 0.1, 1), metallic=0.9, roughness=0.7)
    mats['rubber'] = create_material("Mat_Rubber", (0.01, 0.01, 0.01, 1), metallic=0.0, roughness=0.9)
    mats['panel'] = create_material("Mat_Panel", (0.8, 0.8, 0.8, 1), metallic=0.5, roughness=0.2)
    mats['screen'] = create_material("Mat_Screen", (0.0, 0.0, 0.0, 1), metallic=0.0, roughness=0.2, emission=(0.0, 0.8, 0.2, 1))
    mats['button_red'] = create_material("Mat_ButtonRed", (0.8, 0.0, 0.0, 1), metallic=0.1, roughness=0.3)
    mats['floor'] = create_material("Mat_Floor", (0.15, 0.15, 0.17, 1), metallic=0.2, roughness=0.1)
    return mats

# ==============================================================================
# 4. PEMBUATAN KOMPONEN GENSET
# ==============================================================================
def build_generator(mats):
    # Kumpulan objek yang menjadi bagian generator untuk di-parent nantinya
    gen_parts = []
    
    # 1 & 8. Base Frame & Fuel Tank (Tangki Bahan Bakar Terintegrasi)
    base = create_cube("Base_FuelTank", (0, 0, 0.1), (1.4, 0.5, 0.1), mats['engine'])
    gen_parts.append(base)
    
    frame_bottom = create_cube("Frame_Bottom", (0, 0, 0.05), (1.45, 0.55, 0.05), mats['frame'])
    gen_parts.append(frame_bottom)

    # Rubber Mounts (Kaki Karet)
    for x in [-1.2, 1.2]:
        for y in [-0.4, 0.4]:
            foot = create_cylinder(f"Rubber_Foot_{x}_{y}", (x, y, -0.02), 0.08, 0.05, mat=mats['rubber'])
            gen_parts.append(foot)

    # 2. Blok Mesin Diesel
    engine_block = create_cube("Engine_Block", (-0.3, 0, 0.45), (0.4, 0.25, 0.25), mats['engine'])
    gen_parts.append(engine_block)
    
    cylinder_head = create_cube("Cylinder_Head", (-0.3, 0, 0.75), (0.35, 0.2, 0.1), mats['alternator'])
    gen_parts.append(cylinder_head)

    # 3. Alternator (Generator Listrik)
    alternator = create_cylinder("Alternator", (0.6, 0, 0.45), 0.3, 0.7, rot=(0, math.radians(90), 0), mat=mats['alternator'])
    gen_parts.append(alternator)
    
    # Detail Alternator (Ventilasi Cincin)
    alt_vent = create_cylinder("Alternator_Vent", (0.3, 0, 0.45), 0.31, 0.1, rot=(0, math.radians(90), 0), mat=mats['engine'])
    gen_parts.append(alt_vent)

    # Engine Mounts (Peredam Karet Mesin ke Base)
    for pos_x in [-0.6, 0.0, 0.8]:
        for pos_y in [-0.2, 0.2]:
            mount = create_cylinder(f"EngineMount_{pos_x}_{pos_y}", (pos_x, pos_y, 0.25), 0.06, 0.1, mat=mats['rubber'])
            gen_parts.append(mount)

    # 4. Radiator
    radiator_body = create_cube("Radiator_Body", (-0.95, 0, 0.55), (0.05, 0.4, 0.35), mats['radiator'])
    gen_parts.append(radiator_body)
    
    # Kisi-kisi Radiator (Grilles)
    for z_offset in range(-6, 7):
        grille = create_cube(f"Radiator_Grille_{z_offset}", (-0.97, 0, 0.55 + (z_offset * 0.04)), (0.06, 0.35, 0.01), mats['frame'])
        gen_parts.append(grille)

    # 5. Cooling Fan (Kipas Pendingin)
    fan_hub = create_cylinder("Fan_Hub", (-0.8, 0, 0.55), 0.08, 0.1, rot=(0, math.radians(90), 0), mat=mats['engine'])
    gen_parts.append(fan_hub)
    for i in range(6):
        angle = math.radians(i * 60)
        blade = create_cube(f"Fan_Blade_{i}", (-0.8, math.cos(angle)*0.15, 0.55 + math.sin(angle)*0.15), 
                            (0.01, 0.15, 0.04), mats['frame'])
        # Rotasi pisau agar terlihat seperti bilah kipas
        blade.rotation_euler = (angle, math.radians(20), 0)
        gen_parts.append(blade)

    # 6. Exhaust & Muffler (Knalpot)
    exhaust_pipe = create_cylinder("Exhaust_Pipe", (-0.3, 0.25, 0.95), 0.04, 0.3, mat=mats['exhaust'])
    gen_parts.append(exhaust_pipe)
    
    muffler = create_cylinder("Muffler", (-0.3, 0.25, 1.25), 0.1, 0.4, mat=mats['exhaust'])
    gen_parts.append(muffler)
    
    exhaust_tip = create_cylinder("Exhaust_Tip", (-0.3, 0.25, 1.5), 0.03, 0.15, mat=mats['exhaust'])
    gen_parts.append(exhaust_tip)

    # 7. Control Panel
    panel_box = create_cube("Control_Panel", (0.8, 0.4, 0.7), (0.15, 0.1, 0.2), mats['panel'])
    # Memiringkan panel ke arah depan/kamera sedikit
    panel_box.rotation_euler = (math.radians(-15), math.radians(15), 0)
    gen_parts.append(panel_box)
    
    # Layar Control Panel
    screen = create_cube("Panel_Screen", (0.8, 0.5, 0.75), (0.08, 0.01, 0.05), mats['screen'])
    screen.rotation_euler = panel_box.rotation_euler
    gen_parts.append(screen)

    # Tombol Emergency Stop
    btn_red = create_cylinder("Button_Red", (0.75, 0.5, 0.65), 0.02, 0.02, rot=(math.radians(90), 0, 0), mat=mats['button_red'])
    btn_red.rotation_euler = panel_box.rotation_euler
    gen_parts.append(btn_red)

    # 9. Simple Bolts (Baut Sederhana di Rangka Bawah)
    for x in [-1.35, 1.35]:
        for y in [-0.5, 0.5]:
            bolt = create_cylinder(f"Bolt_{x}_{y}", (x, y, 0.1), 0.015, 0.02, mat=mats['alternator'])
            gen_parts.append(bolt)

# ==============================================================================
# 5. ENVIRONMENT, LIGHTING, DAN KAMERA
# ==============================================================================
def setup_environment(mats):
    # Lantai (Studio Floor)
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.05))
    floor = bpy.context.active_object
    floor.name = "Studio_Floor"
    floor.data.materials.append(mats['floor'])

    # Pencahayaan Studio (3-Point Lighting)
    lights_setup = [
        {"name": "Key_Light", "loc": (3, -3, 4), "energy": 3000, "color": (1, 0.9, 0.8), "size": 2.0},
        {"name": "Fill_Light", "loc": (-3, -4, 2), "energy": 1000, "color": (0.8, 0.9, 1), "size": 3.0},
        {"name": "Rim_Light", "loc": (-1, 4, 3), "energy": 2500, "color": (1, 1, 1), "size": 2.5}
    ]
    
    for l in lights_setup:
        bpy.ops.object.light_add(type='AREA', location=l['loc'])
        light = bpy.context.active_object
        light.name = l['name']
        light.data.energy = l['energy']
        light.data.color = l['color']
        light.data.size = l['size']
        
        # Arahkan lampu ke tengah (0,0,0.5)
        direction = mathutils.Vector((0, 0, 0.5)) - light.location
        light.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # Kamera 3/4 Perspektif
    bpy.ops.object.camera_add(location=(3.2, -3.2, 2.0))
    cam = bpy.context.active_object
    cam.name = "Render_Camera"
    
    # Arahkan kamera ke titik pusat model
    target = mathutils.Vector((0, 0, 0.4))
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    bpy.context.scene.camera = cam

# ==============================================================================
# 6. RENDER SETTINGS
# ==============================================================================
def setup_render():
    scene = bpy.context.scene
    # Gunakan EEVEE
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.idname for e in bpy.types.RenderEngine.__subclasses__()] else 'BLENDER_EEVEE'
    
    # Resolusi
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    
    # Kualitas (Ringan untuk laptop RAM 16GB)
    scene.eevee.taa_render_samples = 64
    
    # Efek Eevee untuk realisme industrial
    scene.eevee.use_gtao = True         # Ambient Occlusion (bayangan sudut)
    scene.eevee.use_bloom = True        # Efek pendar (bagus untuk layar control panel)
    scene.eevee.use_ssr = True          # Screen Space Reflections (pantulan logam)

    # Warna background netral (World)
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs[0].default_value = (0.05, 0.05, 0.06, 1) # Abu-abu gelap profesional

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    clean_scene()
    mats = setup_materials()
    build_generator(mats)
    setup_environment(mats)
    setup_render()
    
    # Memastikan view mengarah ke seluruh model setelah di-generate
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            override = bpy.context.copy()
            override['area'] = area
            override['region'] = area.regions[-1]
            try:
                bpy.ops.view3d.view_all(override)
            except:
                pass
            break
            
    print("Model Portofolio Genset Diesel 3D berhasil di-generate!")