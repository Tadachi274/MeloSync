package com.example.melosync.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.melosync.data.Emotion
import com.example.melosync.ui.home.HomeScreen
import com.example.melosync.ui.main.MainScreen
import com.example.melosync.ui.spotify.SpotifyViewModel // SpotifyViewModelをインポート
import androidx.lifecycle.viewmodel.compose.viewModel // ViewModelをインポート

// 画面遷移のルートを定義
object Routes {
    const val HOME = "home"
    // {emotion} の部分で、前の画面から感情データを受け取る
    const val MAIN = "main/{emotion}"
    const val SETTINGS = "settings"
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val spotifyViewModel: SpotifyViewModel = viewModel()

    NavHost(
        navController = navController,
        startDestination = Routes.HOME
    ) {
        // ホーム画面
        composable(Routes.HOME) {
            HomeScreen(
                onNavigateToMain = { emotion ->
                    // Main画面へ遷移。感情のenum名を渡す
                    navController.navigate("main/${emotion.name}")
                }
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
                spotifyViewModel = spotifyViewModel,
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
