Unreal Engine: 5.8.2
 
Compiler: Visual Studio Community 2026
 
Project: CourseGame

Level: L_Test

Blueprints: BP_Pickup10, BP_Pickup25

Native class: AConfigurablePickup

Final values: 10, 25



---------------------------------

Acceptance Checks
1. Expected both blueprint children to be derived from the same native class ConfigurablePickup. Result successful since both blueprint children were dereived fromn AConfigurablePickup.

2. Expected configured values to remain the same after reopening the editor. result was configured values remained the correct configured values after reopening the editor.

3. expected non-positive value to result in a validation error. result successful when value set to 0 or negative integer.

4.  expected no tick function required. Tick disabled, successfully.

5. clean rebuild expected result was 58 succeeed, 0 failed, 1 skipped.
