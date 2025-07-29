// ui/auth/AuthButton.kt
package com.example.melosync.ui.auth

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import com.example.melosync.ui.theme.AppBackground
import com.example.melosync.ui.theme.AppPurple2

@Composable
fun AuthButton(onClick: () -> Unit) {
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
        onClick = onClick) {
        Text("ログイン")
    }
}