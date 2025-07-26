pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // 🔽 Spotify SDK のリポジトリを明示的に追加
//        maven {
//            url = uri("https://maven.spotify.com")
//        }
    }
}

rootProject.name = "MeloSync"
include(":app")
include(":smartwatchapp")
