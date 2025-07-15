package com.example.melosync.ui.theme

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush

val Purple80 = Color(0xFFE5E3F6)
val PurpleGrey80 = Color(0xFFCCC2DC)
val Pink80 = Color(0xFFEFB8C8)

val Purple40 = Color(0xFF7B4E80)
val PurpleGrey40 = Color(0xFF625b71)
val Pink40 = Color(0xFF7D5260)

val Happy = Color(0x27FFAA00)
val Angry = Color(0x27FF0000)
val Sad = Color(0x250048FF)
val Relax = Color(0x2767FF00)
val Base = Color(0x0CFFFFFF)

val PastPoint = Color(0x6B939393)
val CurrentPoint = Color(0xFFFFFFFF)
val Shadow = Color(0x5EB9B9B9)

val AppPurple = Color(0xFF432BFF)
val AppCyan = Color(0xFF86D8D5)
val AppPurple2 = Color(0xFF7B4E80)
val AppPink = Color(0xFFE8A9BE)
val AppBackground = Color(0xFFEAE6F5)
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