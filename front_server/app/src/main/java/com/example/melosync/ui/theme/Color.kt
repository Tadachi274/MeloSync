package com.example.melosync.ui.theme

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush

val Purple80 = Color(0xFFE5E3F6)
val PurpleGrey80 = Color(0xFFCCC2DC)
val Pink80 = Color(0xFFEFB8C8)

val Purple40 = Color(0xFF6650a4)
val PurpleGrey40 = Color(0xFF625b71)
val Pink40 = Color(0xFF7D5260)

val AppPurple = Color(0xFF432BFF)
val AppCyan = Color(0xFF86D8D5)
val AppPink = Color(0xFFE8A9BE)
val AppBackground = Color(0xFFF4F1FF)
val AppDarkBackground = Color(0xFFD5D5D5)

val AppBackgroundBrush = Brush.verticalGradient(
    colors = listOf(
        Color(0xFFFFFFFF), // AppPink
        Color(0xFFEDE8FD), // AppPurple
        Color(0xFFE2D6FF)  // AppCyan
    )
)

val AppDarkBackgroundBrush = Brush.verticalGradient(
    colors = listOf(
        Color(0xFF211A16), // 温かみのあるダークブラウン
        Color(0xFF1A1C20)  // チャコールグレー
    )
)