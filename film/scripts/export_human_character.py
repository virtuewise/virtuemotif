"""
VirtueMotif MPFB2 character validation/export gate.

Run with Blender 4.2+ and MPFB2 after generating and artist-approving a
character in Blender:
  blender --background character.blend --python film/scripts/export_human_character.py

This script does not invent animation or claim artistic approval. It verifies
that the scene contains a weighted human body, a usable armature, facial
morph targets, and authored animation actions before exporting a self-contained
GLB. Hair/clothing meshes are allowed to share the rig without each carrying
their own facial shape keys.
"""
import bpy
import os

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

rigged_meshes = []
body_meshes = []
for mesh in meshes:
    modifiers = [mod for mod in mesh.modifiers if mod.type == "ARMATURE" and mod.object]
    if not modifiers:
        errors.append(f"{mesh.name}: missing armature modifier")
        continue
    rigged_meshes.append(mesh)
    if not mesh.data.materials:
        errors.append(f"{mesh.name}: missing materials")
    for material in mesh.data.materials:
        if material and not material.use_nodes:
            errors.append(f"{mesh.name}/{material.name}: material must use nodes")
    # MPFB basemesh/body carries facial expression morphs. Clothing, hair,
    # eyes and teeth are separate skinned meshes and need not duplicate them.
    if any(token in mesh.name.lower() for token in ("basemesh", "body", "human")):
        body_meshes.append(mesh)

if not body_meshes:
    errors.append("No identifiable body/basemesh mesh found for facial morph validation.")
elif not any(mesh.data.shape_keys and len(mesh.data.shape_keys.key_blocks) > 1 for mesh in body_meshes):
    errors.append("Body mesh has no usable shape keys; facial morph targets are required.")

if not rigged_meshes:
    errors.append("No skinned mesh found.")
for armature in armatures:
    if not armature.data.bones:
        errors.append(f"{armature.name}: armature contains no bones")

actions = {}
for action in bpy.data.actions:
    normalized = action.name.lower().replace(" ", "_")
    if getattr(action, "fcurves", None):
        if len(action.fcurves):
            actions[normalized] = action
    elif getattr(action, "layers", None):
        # Blender 4.4+ layered actions expose channels through layers/strips.
        if len(action.layers):
            actions[normalized] = action

missing = REQUIRED_ACTIONS - set(actions)
if missing:
    errors.append("Missing authored animation actions: " + ", ".join(sorted(missing)))

if errors:
    print("VirtueMotif character export blocked:")
    for error in errors:
        print(" - " + error)
    raise SystemExit(2)

# Export only the character's skinned hierarchy, not unrelated scene props.
character_objects = set(rigged_meshes + armatures)
for mesh in rigged_meshes:
    for modifier in mesh.modifiers:
        if modifier.type == "ARMATURE" and modifier.object:
            character_objects.add(modifier.object)
    parent = mesh.parent
    while parent:
        character_objects.add(parent)
        parent = parent.parent

bpy.ops.object.select_all(action="DESELECT")
for obj in character_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = armatures[0]

os.makedirs(os.path.dirname(os.path.abspath(OUTPUT)), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUTPUT,
    export_format="GLB",
    use_selection=True,
    export_animations=True,
    export_skins=True,
    export_morph=True,
    export_materials="EXPORT",
    export_image_format="AUTO",
)
print("Exported approved rigged character:", OUTPUT)
