plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.example.melosync"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.melosync"
        minSdk = 30
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        manifestPlaceholders["redirectSchemeName"] = "com.example.melosync"
        manifestPlaceholders["redirectHostName"] = "callback"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    buildFeatures {
        compose = true
    }
}

dependencies {

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    // ViewModel と Navigation
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.navigation.compose)
    // Spotify 認証ライブラリ
    implementation(libs.spotify.auth)
    // Spotify 再生コントロールライブラリ
//    implementation(libs.spotify.app.remote)
    implementation(files("libs/spotify-app-remote-release-0.8.0.aar"))
    implementation(libs.gson) // Spotify SDKが必要とするGson
    // Retrofit (Web API通信用)
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.gson)
    // テストライブラリ
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)

    implementation("androidx.datastore:datastore-preferences:1.1.7")
}