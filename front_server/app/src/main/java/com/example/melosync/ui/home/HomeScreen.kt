package com.example.melosync.ui.home

import android.content.Intent
import android.net.Uri
import android.util.Log
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Button
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
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.LifecycleOwner
import com.example.melosync.ui.auth.SignInWithGoogleFunctions
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
) {
    // ログイン状態を監視
    val uiState by authViewModel.uiState.collectAsState()
    val context = LocalContext.current
    println("[HomeScreen]isLoggedIn:${uiState.isLoggedIn}")
    println("[HomeScreen]isSpotifyLoggedIn:${uiState.isSpotifyLoggedIn}")
    println(!uiState.isLoggedIn && !uiState.isSpotifyLoggedIn)



    Scaffold { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text("ログイン済みです")

            Spacer(modifier = Modifier.height(24.dp))
            // 追加：Spotify 認証ボタン
            Button(onClick = {
                // クライアントID／リダイレクトURI は適宜置き換えてください
                Log.d("LoginScreen","SpotifyLoginButton Click.")
                val clientId = "ced2ee375b444183a40d0a95de22d132"
                val redirectUri = "com.example.melosync://callback"
                val authUri = Uri.Builder()
                    .scheme("https")
                    .authority("accounts.spotify.com")
                    .appendPath("authorize")
                    .appendQueryParameter("client_id", clientId)
                    .appendQueryParameter("response_type", "code")
                    .appendQueryParameter("redirect_uri", redirectUri)
                    .appendQueryParameter("scope", "user-read-private playlist-modify-public playlist-read-private")  // 必要なスコープを追加
                    .appendQueryParameter("show_dialog", "true")
                    .build()
                context.startActivity(Intent(Intent.ACTION_VIEW, authUri))
            }) {
                Text("Spotifyで認証")
            }

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