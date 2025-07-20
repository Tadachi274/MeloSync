// ui/auth/LoginScreen.kt
package com.example.melosync.ui.auth

import android.widget.Toast
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.flow.collectLatest

@Composable
fun LoginScreen(viewModel: AuthViewModel,modifier: Modifier = Modifier) {
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
                Text("ログイン済みです")
            }
            else -> {
                AuthButton { viewModel.signIn()}
            }
        }
    }
}