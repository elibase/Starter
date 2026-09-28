"""Run inside the UE 5.8.2 editor after the native project builds.
Creates real saved assets; refuses to overwrite an existing course map.
"""
import json
from pathlib import Path
import unreal as ue

root = Path(ue.Paths.project_dir())
manifest = json.loads((root / 'checkpoint.json').read_text(encoding='utf-8-sig'))
stage = manifest['stage']
tools = ue.AssetToolsHelpers.get_asset_tools()
assets = ue.EditorAssetLibrary
level = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
if assets.does_asset_exist('/Game/Course/Maps/L_Test'):
    raise RuntimeError('L_Test already exists; refusing to overwrite instructor or student edits.')

def native(name):
    result = ue.load_class(None, '/Script/CourseGame.' + name)
    if not result:
        raise RuntimeError('Native class not loaded: ' + name)
    return result

def blueprint(name, parent, defaults=None, presentation=False):
    factory = ue.BlueprintFactory()
    factory.set_editor_property('parent_class', parent)
    bp = tools.create_asset(name, '/Game/Course/Items', ue.Blueprint, factory)
    if not bp:
        raise RuntimeError('Could not create ' + name)
    if presentation and not ue.CourseAssetLibrary.add_beacon_presentation(bp):
        raise RuntimeError('Blueprint event graph failed to compile: ' + name)
    cls = ue.load_class(None, bp.get_path_name() + '_C')
    cdo = ue.get_default_object(cls)
    for key, value in (defaults or {}).items():
        cdo.set_editor_property(key, value)
    ue.BlueprintEditorLibrary.compile_blueprint(bp)
    if not assets.save_loaded_asset(bp, only_if_is_dirty=False):
        raise RuntimeError('Could not save ' + name)
    return ue.load_class(None, bp.get_path_name() + '_C')

def material(name, color):
    mat = tools.create_asset(name, '/Game/Course/Items', ue.Material, ue.MaterialFactoryNew())
    mat.set_editor_property('shading_model', ue.MaterialShadingModel.MSM_UNLIT)
    expr = ue.MaterialEditingLibrary.create_material_expression(mat, ue.MaterialExpressionConstant3Vector)
    expr.set_editor_property('constant', ue.LinearColor(*color))
    ue.MaterialEditingLibrary.connect_material_property(expr, '', ue.MaterialProperty.MP_EMISSIVE_COLOR)
    ue.MaterialEditingLibrary.recompile_material(mat)
    assets.save_loaded_asset(mat, only_if_is_dirty=False)
    return mat

assets.make_directory('/Game/Course/Maps')
assets.make_directory('/Game/Course/Tests')
if not level.new_level('/Game/Course/Maps/L_Test'):
    raise RuntimeError('Could not create test map')
camera = actors.spawn_actor_from_class(ue.CameraActor, ue.Vector(150, -800, 170), ue.Rotator(pitch=0, yaw=90, roll=0))
camera.set_editor_property('auto_activate_for_player', ue.AutoReceiveInput.PLAYER0)
camera.get_component_by_class(ue.CameraComponent).set_editor_property('projection_mode', ue.CameraProjectionMode.ORTHOGRAPHIC)
camera.get_component_by_class(ue.CameraComponent).set_editor_property('ortho_width', 700)
camera.set_actor_label('Course overview camera')
actors.spawn_actor_from_class(ue.DirectionalLight, ue.Vector(150,-500,400), ue.Rotator(pitch=-45,yaw=90,roll=0))

if stage != 'Starter':
    for name, charge, color, x in [
        ('BP_Beacon_Blue', 0.0, (0.03, 0.35, 1.0, 1.0), 0),
        ('BP_Beacon_Amber', 25.0, (1.0, 0.45, 0.03, 1.0), 280),
    ]:
        mat = material('M_' + name.removeprefix('BP_'), color)
        cls = blueprint(name, native('CourseBeacon'), {'initial_charge': charge, 'visual_material': mat}, True)
        actor = actors.spawn_actor_from_class(cls, ue.Vector(x, 0, 170))
        actor.set_actor_label(name)
    actors.spawn_actor_from_class(native('BeaconTestStimulus'), ue.Vector())

if stage == 'Completed':
    for name, score, x in [('BP_Pickup_10', 10, 40), ('BP_Pickup_25', 25, 240)]:
        cls = blueprint(name, native('ConfigurablePickup'), {'score_value': score})
        actor = actors.spawn_actor_from_class(cls, ue.Vector(x, 0, 50))
        actor.set_actor_label(name)
    # Invalid fixture is an asset only; it does not create errors during ordinary L_Test play.
    blueprint('BP_Pickup_Invalid', native('ConfigurablePickup'), {'score_value': 0})

if not level.save_current_level():
    raise RuntimeError('Test map save failed')
receipt = {'stage': stage, 'assets_generated': True, 'engine': ue.SystemLibrary.get_engine_version(),
           'play_tested': False, 'assets': list(assets.list_assets('/Game/Course', recursive=True, include_folder=False))}
(root / 'asset-generation.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
ue.log('COURSE_ASSETS_CREATED: ' + stage)