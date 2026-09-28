import json
import math
from pathlib import Path
import unreal as ue

root = Path(ue.Paths.project_dir())
manifest = json.loads((root / 'checkpoint.json').read_text(encoding='utf-8-sig'))
stage = manifest['stage']
level = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
checks = []

def check(label, condition):
    checks.append({'check': label, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(label)

def cls(name):
    result = ue.load_class(None, '/Game/Course/Items/' + name + '.' + name + '_C')
    check(name + ' reloads from saved asset', result is not None)
    return result

check('L_Test reopens from disk', level.load_level('/Game/Course/Maps/L_Test'))
saved_actors = actors.get_all_level_actors()
for camera in [a for a in saved_actors if isinstance(a,ue.CameraActor)]:
    rotation = camera.get_actor_rotation()
    check('Saved camera faces positive Y', abs(rotation.yaw-90.0)<0.01 and abs(rotation.pitch)<0.01)
if stage != 'Starter':
    for name, initial in [('BP_Beacon_Blue', 0.0), ('BP_Beacon_Amber', 25.0)]:
        bp_cls = cls(name)
        cdo = ue.get_default_object(bp_cls)
        check(name + ' retains InitialCharge', cdo.get_editor_property('initial_charge') == initial)
        placed = [a for a in saved_actors if a.get_actor_label() == name]
        check(name + ' has one saved level instance', len(placed) == 1)
        check(name + ' saved level instance retains InitialCharge', placed[0].get_editor_property('initial_charge') == initial)
        check(name + ' saved level instance has a visual material', bool(placed[0].get_editor_property('visual_material')))
        check(name + ' has native CourseBeacon parent', isinstance(cdo, ue.CourseBeacon))
        instance = actors.spawn_actor_from_class(bp_cls, ue.Vector(0, 0, 1000))
        original = instance.get_charge()
        instance.add_charge(-10.0)
        check(name + ' negative amount ignored', instance.get_charge() == original)
        instance.add_charge(float('nan'))
        check(name + ' non-finite amount ignored', instance.get_charge() == original)
        instance.add_charge(125.0)
        check(name + ' oversized amount clamps at 100', instance.get_charge() == 100.0)
        instance.add_charge(125.0)
        check(name + ' full charge remains bounded', instance.get_charge() == 100.0)
        check(name + ' has tick disabled', not ue.CourseAssetLibrary.can_actor_ever_tick(instance))
        actors.destroy_actor(instance)

if stage == 'Completed':
    for name, score in [('BP_Pickup_10', 10), ('BP_Pickup_25', 25), ('BP_Pickup_Invalid', 0)]:
        bp_cls = cls(name)
        cdo = ue.get_default_object(bp_cls)
        check(name + ' has native ConfigurablePickup parent', isinstance(cdo, ue.ConfigurablePickup))
        check(name + ' retains ScoreValue', cdo.get_score_value() == score)
        if score > 0:
            placed = [a for a in saved_actors if a.get_actor_label() == name]
            check(name + ' has one saved level instance', len(placed) == 1)
            check(name + ' saved level instance retains ScoreValue', placed[0].get_score_value() == score)
        check(name + ' validation result', cdo.validate_configuration() == (score > 0))
        check(name + ' has tick disabled', not ue.CourseAssetLibrary.can_actor_ever_tick(cdo))

receipt = {'engine': ue.SystemLibrary.get_engine_version(), 'stage': stage, 'checks': checks,
           'all_passed': all(c['passed'] for c in checks), 'scope': 'Fresh editor process, asset reload and native boundary checks; separate runtime verification required.'}
(root / 'verification-editor.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
ue.log('COURSE_EDITOR_VERIFICATION_PASSED: ' + str(len(checks)))
