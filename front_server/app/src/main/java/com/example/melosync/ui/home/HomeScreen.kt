package com.example.melosync.ui.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.melosync.data.Emotion

import com.example.melosync.ui.auth.LoginScreen
import com.example.melosync.ui.auth.AuthViewModel
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.LifecycleOwner
import com.example.melosync.ui.auth.AuthRepository
import com.example.melosync.ui.auth.LogoutButton
import kotlinx.coroutines.launch
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.lifecycle.compose.LocalLifecycleOwner

@Composable
fun HomeScreen(
    // 感情が選択されたら、その情報を元に次の画面へ遷移する
    onNavigateToMain: (Emotion) -> Unit={},
    viewModel: HomeViewModel = viewModel() ,
    authViewModel: AuthViewModel,
    repository: AuthRepository
) {
    // ログイン状態を監視
    val uiState by authViewModel.uiState.collectAsState()
    println("[HomeScreen]isLoggedIn:${uiState.isLoggedIn}")
    println("[HomeScreen]isSpotifyLoggedIn:${uiState.isSpotifyLoggedIn}")
    println(!uiState.isLoggedIn && !uiState.isSpotifyLoggedIn)

    if (!uiState.isLoggedIn || !uiState.isSpotifyLoggedIn) {
        LoginScreen(viewModel = authViewModel)
        return
    }

    Scaffold { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "今の気分は？",
                style = MaterialTheme.typography.headlineMedium
            )
            Spacer(modifier = Modifier.height(32.dp))

            // 感情アイコンを横に並べる
            Row(
                horizontalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                // 各感情アイコンをループで表示
                Emotion.entries.forEach { emotion ->
                    Text(
                        text = emotion.emoji,
                        fontSize = 64.sp,
                        modifier = Modifier.clickable {
                            // アイコンクリックでViewModelを更新し、画面遷移を実行
                            viewModel.onEmotionSelected(emotion)
                            onNavigateToMain(emotion)
                        }
                    )
                }
            }
            LogoutButton { authViewModel.logout() }
        }
    }
}