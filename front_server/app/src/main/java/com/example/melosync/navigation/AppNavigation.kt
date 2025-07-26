package com.example.melosync.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.melosync.data.Emotion
import com.example.melosync.ui.auth.LoginScreen
import com.example.melosync.ui.home.HomeScreen
import com.example.melosync.ui.main.MainScreen
import android.util.Log


import com.example.melosync.ui.auth.AuthViewModel

// 画面遷移のルートを定義
object Routes {
    const val HOME = "home"
    // {emotion} の部分で、前の画面から感情データを受け取る
    const val MAIN = "main/{emotion}"
    const val SETTINGS = "settings"
    const val LOGIN = "login"
}

@Composable
fun AppNavigation(
    authViewModel: AuthViewModel
) {
    val navController = rememberNavController()
    val uiState by authViewModel.uiState.collectAsState()
    Log.d("Navigation","isLoggedIn:${uiState.isLoggedIn}")
    Log.d("Navigation","isSpotifyLoggedIn:${uiState.isSpotifyLoggedIn}")
    val startDestination = if (uiState.isLoggedIn && uiState.isSpotifyLoggedIn) Routes.HOME else Routes.LOGIN


    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Routes.LOGIN) {
            LoginScreen(
                authViewModel = authViewModel
            )
        }

        // ホーム画面
        composable(Routes.HOME) {
            HomeScreen(
                onNavigateToMain = { emotion ->
                    // Main画面へ遷移。感情のenum名を渡す
                    navController.navigate("main/${emotion.name}")
                },
                authViewModel = authViewModel
            )
        }

        // メイン画面
        composable(
            route = Routes.MAIN,
            arguments = listOf(navArgument("emotion") { type = NavType.StringType })
        ) { backStackEntry ->
            // 受け取った感情の文字列からenumに変換
            val emotionString = backStackEntry.arguments?.getString("emotion")
            val emotion = Emotion.valueOf(emotionString ?: Emotion.NEUTRAL.name)

            MainScreen(
                emotion = emotion,
                onNavigateToSettings = {
                    // TODO: 設定画面への遷移を実装
                    // navController.navigate(Routes.SETTINGS)
                }
            )
        }

        // TODO: 設定画面のComposableをここに追加
        // composable(Routes.SETTINGS) { ... }
    }
}
