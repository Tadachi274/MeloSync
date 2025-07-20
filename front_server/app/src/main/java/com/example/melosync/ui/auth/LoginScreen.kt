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
    println(2)
    val value = 2
    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        when(value) {
            0 -> {
                CircularProgressIndicator()
            }
            1 -> {
                Text("ログイン済みです")
            }
            else -> {
                AuthButton { viewModel.signIn()}
            }
        }
    }
}