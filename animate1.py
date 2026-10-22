import bpy
import mathutils

def generate_assembly_animation():
    print("\n" + "="*50)
    print("      MEMBUAT ANIMASI PERAKITAN (ASSEMBLY)      ")
    print("="*50)

    # 1. Atur Pengaturan Timeline Scene
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 240
    scene.render.fps = 24
    
    # Kumpulan objek yang dikecualikan (Lantai, Lampu, Kamera)
    excluded_names = ["studio_floor"]
    
    components_to_animate = []
    excluded_components = []

    # 2. Identifikasi Objek yang Layak Dianimasikan
    for obj in scene.objects:
        obj_name = obj.name.lower()
        
        # Mengecualikan Kamera, Lampu, dan Lantai (hanya MESH dan CURVE yang dianimasikan)
        if obj.type not in {'MESH', 'CURVE'}:
            excluded_components.append(f"{obj.name} (Bukan Mesh/Curve)")
            continue
        if any(ex in obj_name for ex in excluded_names):
            excluded_components.append(f"{obj.name} (Dikecualikan manual)")
            continue
        
        # Mencegah gerakan ganda akibat hierarki Parent-Child
        if obj.parent is not None:
            # Jika punya induk, biarkan anaknya diam (nanti ikut bergerak bersama induknya)
            excluded_components.append(f"{obj.name} (Child dari {obj.parent.name})")
            continue
            
        components_to_animate.append(obj)

    # Cetak Laporan Objek
    print(f"\n[INFO] Menemukan {len(components_to_animate)} komponen genset untuk dianimasikan.")
    print(f"[INFO] {len(excluded_components)} objek dikecualikan dari animasi komponen.")

    # 3. Proses Animasi per Komponen
    center_mass = mathutils.Vector((0.0, 0.0, 0.5)) # Asumsi pusat genset
    
    for obj in components_to_animate:
        # Bersihkan animasi lama HANYA untuk objek ini agar aman jika skrip di-run ulang
        obj.animation_data_clear()
        
        # Simpan posisi asli (Posisi Terakit / Akhir)
        orig_loc = obj.location.copy()
        
        # Tentukan posisi terpisah (Exploded View)
        obj_name = obj.name.lower()
        offset = mathutils.Vector((0, 0, 0))
        
        if any(k in obj_name for k in ["roof", "canopy", "lifting"]):
            offset = mathutils.Vector((0, 0, 1.5)) # Atap ke atas
        elif any(k in obj_name for k in ["frame_bottom", "base", "foot", "mount"]):
            offset = mathutils.Vector((0, 0, -0.2)) # Rangka ke bawah sedikit
        elif any(k in obj_name for k in ["panel", "screen", "button", "lcd"]):
            offset = mathutils.Vector((0, -1.2, 0.2)) # Panel ke arah luar (depan operator)
        elif any(k in obj_name for k in ["radiator", "fan"]):
            offset = mathutils.Vector((-1.5, 0, 0)) # Radiator ke samping kiri
        elif "alternator" in obj_name:
            offset = mathutils.Vector((1.2, 0, 0)) # Alternator ke samping kanan
        elif any(k in obj_name for k in ["exhaust", "muffler"]):
            offset = mathutils.Vector((-1.0, 0, 1.2)) # Knalpot serong atas
        else:
            # Komponen lainnya meledak menjauh secara radial dari pusat mesin
            direction = orig_loc - center_mass
            if direction.length < 0.01:
                direction = mathutils.Vector((0, 0, 1))
            direction.normalize()
            offset = direction * 0.8
            
        exploded_loc = orig_loc + offset

        # --- MEMASUKKAN KEYFRAME (LOCATION SAJA) ---
        
        # Frame 1 - 40: Posisi terpisah (Diam agar penonton melihat komponen)
        obj.location = exploded_loc
        obj.keyframe_insert(data_path="location", frame=1)
        obj.keyframe_insert(data_path="location", frame=40)
        
        # Frame 180: Kembali ke posisi asli (Perakitan Selesai)
        obj.location = orig_loc
        obj.keyframe_insert(data_path="location", frame=180)
        
        # Frame 240: Pertahankan posisi asli hingga akhir video
        obj.keyframe_insert(data_path="location", frame=240)

    # 4. Animasi Kamera Sinematik Halus (Frame 217 - 240)
    camera = scene.camera
    if camera:
        camera.animation_data_clear()
        orig_cam_loc = camera.location.copy()
        
        # Frame 1 - 216: Kamera diam di tempat aslinya
        camera.location = orig_cam_loc
        camera.keyframe_insert(data_path="location", frame=1)
        camera.keyframe_insert(data_path="location", frame=216)
        
        # Frame 240: Kamera geser sangat sedikit ke samping dan bawah (efek dramatis)
        subtle_pan = orig_cam_loc + mathutils.Vector((0.15, -0.15, -0.05))
        camera.location = subtle_pan
        camera.keyframe_insert(data_path="location", frame=240)
        
        # Kembalikan posisi asli agar scene tidak rusak setelah skrip jalan
        camera.location = orig_cam_loc 
        print(f"\n[INFO] Menambahkan animasi panning halus pada '{camera.name}' di frame 217-240.")

    print("\n" + "="*50)
    print("      ANIMASI BERHASIL DIBUAT DENGAN AMAN       ")
    print("="*50 + "\n")

if __name__ == "__main__":
    generate_assembly_animation()