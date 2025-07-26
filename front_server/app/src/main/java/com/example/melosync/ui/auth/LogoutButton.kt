// ui/auth/AuthButton.kt
package com.example.melosync.ui.auth

import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable

@Composable
fun LogoutButton(onClick: () -> Unit) {
    Button(onClick = onClick) {
        Text("ログアウト")
    }
}