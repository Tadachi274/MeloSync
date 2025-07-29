// ui/auth/LoginScreen.kt
package com.example.melosync.ui.auth

import android.widget.Toast
import android.content.Intent
import android.net.Uri
import android.util.Log
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.example.melosync.MainActivity
import java.util.UUID
import androidx.lifecycle.viewModelScope
import com.example.melosync.R
import com.example.melosync.ui.theme.AppBackground
import com.example.melosync.ui.theme.AppPurple2
import kotlinx.coroutines.launch
import androidx.compose.foundation.shape.RoundedCornerShape


@Composable
fun LoginScreen(
    authViewModel: AuthViewModel,
) {
    // ViewModel の UI 状態を監視
    val uiState by authViewModel.uiState.collectAsState()
    val modifier = Modifier

    val context = LocalContext.current
    // エラーが出たらトースト表示
    LaunchedEffect(uiState.errorMessage) {
        uiState.errorMessage?.let { msg ->
            Toast.makeText(context, msg, Toast.LENGTH_LONG).show()
        }
    }
    LaunchedEffect(uiState.successMessage) {
        uiState.successMessage?.let { msg ->
            Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
            authViewModel.clearSuccessMessage() // 表示後クリア
        }
    }
    Scaffold { paddingValues ->
        Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Image(
                    painter = painterResource(id = R.drawable.image),
                    contentDescription = "App Logo",
                    modifier = Modifier.size(240.dp) // Logo image size
                )
                Spacer(modifier = Modifier.height(32.dp))
                when {
                    uiState.isLoading -> {
                        CircularProgressIndicator()
                    }

                    uiState.isLoggedIn -> {
                        Log.d("LoginScreen", "isSpotifyLoggedIn:${uiState.isSpotifyLoggedIn}")
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            //Text("ログイン済みです")

                            //Spacer(modifier = Modifier.height(24.dp))
                            // 追加：Spotify 認証ボタン
                            Button(
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = AppPurple2,
                                    contentColor = AppBackground
                                ),
                                shape = RoundedCornerShape(50), // 丸み
                                elevation = ButtonDefaults.buttonElevation(
                                    defaultElevation = 6.dp,
                                    pressedElevation = 8.dp,
                                    disabledElevation = 0.dp
                                ),
                                onClick = {
                                // クライアントID／リダイレクトURI は適宜置き換えてください
                                Log.d("LoginScreen", "SpotifyLoginButton Click.")
                                val clientId = "ced2ee375b444183a40d0a95de22d132"
                                val redirectUri = "com.example.melosync://callback"
                                val authUri = Uri.Builder()
                                    .scheme("https")
                                    .authority("accounts.spotify.com")
                                    .appendPath("authorize")
                                    .appendQueryParameter("client_id", clientId)
                                    .appendQueryParameter("response_type", "code")
                                    .appendQueryParameter("redirect_uri", redirectUri)
                                    .appendQueryParameter(
                                        "scope",
                                        "user-read-private playlist-modify-public playlist-read-private"
                                    )  // 必要なスコープを追加
                                    .appendQueryParameter("show_dialog", "true")
                                    .build()
                                context.startActivity(Intent(Intent.ACTION_VIEW, authUri))
                                authViewModel.onSpotifyLoginSuccess()
                            }) {
                                Text("Spotifyで認証")
                            }
                            //Spacer(modifier = Modifier.height(120.dp))
                            //LogoutButton { authViewModel.logout() }
                        }
                    }

                    else -> {
                        AuthButton { authViewModel.signIn() }

                    }
                }
            }
        }
    }
}