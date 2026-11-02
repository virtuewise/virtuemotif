"""
VirtueMotif MPFB2 character validation/export gate.

Run with Blender's Python interpreter after generating and artist-approving a
character in Blender with MPFB2 installed:
  blender --background character.blend --python film/scripts/export_human_character.py

This script intentionally refuses to fabricate a human model. It exports only
a real, rigged and approved scene, and checks for skinning, PBR materials,
facial shape keys and named animation actions before writing the GLB.
"""
import bpy
import os
import sys

OUTPUT = os.environ.get(
    "VIRTUEMOTIF_CHARACTER_OUTPUT",
    os.path.join(bpy.path.abspath("//"), "horizon-protagonist.glb"),
)
REQUIRED_ACTIONS = {"idle", "walk", "turn", "look_to_horizon"}
errors = []

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
if not meshes:
    errors.append("No mesh found: generate and artist-approve the MPFB2 character first.")
if not armatures:
    errors.append("No armature found: export requires a rigged human character.")

for mesh in meshes:
    if not any(mod.type == "ARMATURE" and mod.object for mod in mesh.modifiers):
        errors.append(f"{mesh.name}: missing armature modifier")
    if not mesh.data.materials:
        errors.append(f"{mesh.name}: missing materials")
    for material in mesh.data.materials:
        if material and not material.use_nodes:
            errors.append(f"{mesh.name}/{material.name}: material must use nodes")
    if mesh.data.shape_keys is None:
        errors.append(f"{mesh.name}: facial/body shape keys are required")

actions = {
    action.name.lower().replace(" ", "_")
    for action in bpy.data.actions
}
missing = REQUIRED_ACTIONS - actions
if missing:
    errors.append("Missing named animation actions: " + ", ".join(sorted(missing)))

if errors:
    print("VirtueMotif character export blocked:")
    for error in errors:
        print(" - " + error)
    raise SystemExit(2)

os.makedirs(os.path.dirname(os.path.abspath(OUTPUT)), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUTPUT,
    export_format="GLB",
    export_animations=True,
    export_skins=True,
    export_morph=True,
    export_materials="EXPORT",
    export_image_format="AUTO",
)
print("Exported approved rigged character:", OUTPUT)
