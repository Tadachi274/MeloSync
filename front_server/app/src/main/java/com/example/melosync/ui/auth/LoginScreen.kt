// ui/auth/LoginScreen.kt
package com.example.melosync.ui.auth

import android.widget.Toast
import android.content.Intent
import android.net.Uri
import android.util.Log
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.example.melosync.MainActivity


@Composable
fun LoginScreen(
    viewModel: AuthViewModel,
    modifier: Modifier = Modifier
) {
    // ViewModel の UI 状態を監視
    val uiState by viewModel.uiState.collectAsState()

    val context = LocalContext.current
    // エラーが出たらトースト表示
    LaunchedEffect(uiState.errorMessage) {
        uiState.errorMessage?.let { msg ->
            Toast.makeText(context, msg, Toast.LENGTH_LONG).show()
        }
    }
    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        when {
            uiState.isLoading -> {
                CircularProgressIndicator()
            }
            uiState.isLoggedIn -> {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Googleログイン済みです")
                    Spacer(modifier = Modifier.height(24.dp))
                    LogoutButton { viewModel.logout() }

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
                    Button(
                        onClick = {
                            // MainActivity（HomeScreen を表示している Activity）を起動
                            val intent = Intent(context, MainActivity::class.java)
                            context.startActivity(intent)
                        }
                    ) {
                        Text("ホーム画面へ")
                    }
                }
            }
            else -> {
                    AuthButton { viewModel.signIn() }
                }
            }
        }
}