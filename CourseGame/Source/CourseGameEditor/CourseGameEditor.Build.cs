using UnrealBuildTool;
public class CourseGameEditor : ModuleRules
{
    public CourseGameEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PrivateDependencyModuleNames.AddRange(new[] {
            "Core", "CoreUObject", "Engine", "CourseGame", "UnrealEd",
            "BlueprintGraph", "Kismet", "KismetCompiler", "AssetRegistry"
        });
    }
}