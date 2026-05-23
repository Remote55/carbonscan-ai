allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

// ----------------------------------------------------------------------------
// Force JVM 17 for all Android subprojects (including Flutter plugins).
//
// Why: Third-party plugins like tflite_flutter / shared_preferences_android /
// camera_android_camerax default to Java 1.8 source/target while Kotlin 2.x
// targets JVM 21 by default. The result is a hard error:
//   "Inconsistent JVM-target compatibility detected for tasks
//    compileDebugJavaWithJavac (1.8) and compileDebugKotlin (21)"
// (Flutter 3.27+ ships AGP 8+ and Kotlin 2.x which is much stricter about
//  this than older Flutter versions used to be.)
//
// Solution: force Java 17 + Kotlin jvmTarget 17 across every subproject
// after evaluation, so plugins inherit the same JVM target as `:app`.
// ----------------------------------------------------------------------------
// Note: do NOT wrap the below in afterEvaluate — the earlier
// `subprojects { project.evaluationDependsOn(":app") }` block triggers
// eager evaluation of subprojects, so by the time afterEvaluate{} is
// registered the projects are already past their evaluation phase and
// Gradle throws: "Cannot run Project.afterEvaluate(Action) when the
// project is already evaluated."
//
// Instead, use tasks.withType<…>().configureEach which is *lazy* — it
// applies to tasks regardless of when they are added to the graph.
subprojects {
    // Java 17 source/target for every JavaCompile in every subproject
    tasks.withType<JavaCompile>().configureEach {
        sourceCompatibility = JavaVersion.VERSION_17.toString()
        targetCompatibility = JavaVersion.VERSION_17.toString()
    }
    // Kotlin 2.0+ requires the typed `compilerOptions { }` DSL — the old
    // `kotlinOptions { jvmTarget = "17" }` was promoted from deprecation
    // warning to hard error in KGP 2.x.
    tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
