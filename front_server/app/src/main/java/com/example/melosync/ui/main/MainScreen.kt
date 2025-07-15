package com.example.melosync.ui.main

import android.widget.Toast
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.melosync.data.Emotion
import kotlin.math.roundToInt
import com.example.melosync.R
import androidx.compose.ui.res.imageResource
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.graphics.drawscope.clipPath

@Composable
fun MainScreen(
    emotion: Emotion,
    onNavigateToSettings: () -> Unit,
    viewModel: MainViewModel = viewModel()
) {
    // ViewModelに選択された感情をセット
    LaunchedEffect(key1 = emotion) {
        viewModel.setEmotion(emotion)
    }

    var showMenu by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val emotionCoordinate by viewModel.emotionCoordinate.collectAsStateWithLifecycle()
    val currentQuadrant by viewModel.currentQuadrant.collectAsStateWithLifecycle()

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            TopBarWithEmotion(
                emotion = emotion,
                onMenuClick = { showMenu = true }
            )
        }
    ) { paddingValues ->
//        DropdownMenu(
//            expanded = showMenu,
//            onDismissRequest = { showMenu = false }
//        ) {
//            DropdownMenuItem(
//                text = { Text("Spotifyにログイン") },
//                onClick = {
//                    Toast.makeText(context, "ログイン機能は後で実装します", Toast.LENGTH_SHORT).show()
//                    showMenu = false
//                }
//            )
//            DropdownMenuItem(
//                text = { Text("リストの設定") },
//                onClick = {
//                    onNavigateToSettings()
//                    showMenu = false
//                }
//            )
//        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // 感情グラフを表示
            EmotionGraph(
                coordinate = emotionCoordinate,
                onCoordinateChange = { newOffset, canvasSize, radius ->
                    viewModel.updateCoordinate(newOffset, canvasSize, radius)
                }
            )

            // 現在の象限を表示
            Text(
                text = if (currentQuadrant != 0) "第 $currentQuadrant 象限" else "軸上",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(top = 16.dp)
            )

            Spacer(modifier = Modifier.weight(1f))

            // Spotifyプレーヤーのプレースホルダー
            SpotifyPlayerPlaceholder(onConnectClick = {
                Toast.makeText(context, "ログイン機能は後で実装します", Toast.LENGTH_SHORT).show()
            })
        }
    }
}

@Composable
fun TopBarWithEmotion(emotion: Emotion, onMenuClick: () -> Unit) {
    var offsetX by remember { mutableStateOf(0f) }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(80.dp)
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .padding(horizontal = 16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxSize(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = emotion.emoji,
                fontSize = 40.sp,
                modifier = Modifier
                    .offset { IntOffset(offsetX.roundToInt(), 0) }
                    .pointerInput(Unit) {
                        detectDragGestures { change, dragAmount ->
                            change.consume()
                            offsetX += dragAmount.x
                        }
                    }
            )

            IconButton(onClick = onMenuClick) {
                Icon(Icons.Default.Menu, contentDescription = "メニュー")
            }
        }
    }
}

@Composable
fun EmotionGraph(
    coordinate: EmotionCoordinate,
    onCoordinateChange: (offset: Offset, canvasSizePx: Float, radiusPx: Float) -> Unit
) {
    val primaryColor = MaterialTheme.colorScheme.primary
    val imageBitmap = ImageBitmap.imageResource(id = R.drawable.feeling)
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(1f) // 正方形を維持
            .padding(16.dp),
        contentAlignment = Alignment.Center
    ) {
        val density = LocalDensity.current
        var canvasSize by remember { mutableStateOf(0.dp) }
        val radi_rate = 2.5f
        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .pointerInput(Unit) {
                    detectDragGestures { change, _ ->
                        // ドラッグ位置をViewModelに通知
                        val canvasSizePx = this.size.width.toFloat()
                        val radiusPx = canvasSizePx / radi_rate
                        onCoordinateChange(change.position, canvasSizePx, radiusPx)
                        change.consume()
                    }
                }
        ) {

            val center = this.center
            val radius = size.minDimension / radi_rate
            val circlePath = Path().apply {
                addOval(Rect(center = center, radius = radius))
            }
            clipPath(circlePath) {
                drawImage(
                    image = imageBitmap,
                    dstSize = IntSize(
                        (radius * 2).roundToInt(),
                        (radius * 2).roundToInt()
                    ),
                    dstOffset = IntOffset(
                        (center.x - radius).roundToInt(),
                        (center.y - radius).roundToInt()
                    )
                )
            }
            // 円を描画
            drawCircle(
                color = Color.LightGray,
                radius = radius,
                center = center,
                style = Stroke(width = 2.dp.toPx())
            )

            // 十字線を描画
            drawLine(
                color = Color.LightGray,
                start = Offset(center.x - radius, center.y),
                end = Offset(center.x + radius, center.y),
                strokeWidth = 2.dp.toPx()
            )
            drawLine(
                color = Color.LightGray,
                start = Offset(center.x, center.y - radius),
                end = Offset(center.x, center.y + radius),
                strokeWidth = 2.dp.toPx()
            )

            // 感情の位置を計算 (-1.0f ~ 1.0f の座標をCanvasの座標に変換)
            val pointX = center.x + coordinate.x * radius
            val pointY = center.y - coordinate.y * radius // Y軸は下がプラスなので反転

            // 感情の位置に点を描画
            drawCircle(
                color = primaryColor,
                radius = 12.dp.toPx(),
                center = Offset(pointX, pointY)
            )
        }
    }
}

@Composable
fun SpotifyPlayerPlaceholder(onConnectClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("Spotify プレイリスト", style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(16.dp))
            Box(
                modifier = Modifier
                    .size(150.dp)
                    .background(Color.Gray),
                contentAlignment = Alignment.Center
            ) {
                Text("アルバムアート", color = Color.White)
            }
            Spacer(Modifier.height(16.dp))
            Text("曲名", style = MaterialTheme.typography.titleMedium)
            Text("アーティスト名", style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(8.dp))
            Button(onClick = onConnectClick) {
                Text("Spotifyに接続して再生")
            }
        }
    }
}
//fun SpotifyPlayerPlaceholder() {
//    // Spotifyの再生画面はSDKの制約上、完全にUIを埋め込むのが難しいため
//    // このように自前でUIを構築し、バックグラウンドのSpotifyを操作するのが一般的です。
//    Card(
//        modifier = Modifier.fillMaxWidth(),
//        elevation = CardDefaults.cardElevation(4.dp)
//    ) {
//        Column(
//            modifier = Modifier.padding(16.dp),
//            horizontalAlignment = Alignment.CenterHorizontally
//        ) {
//            Text("Spotify プレイリスト", style = MaterialTheme.typography.titleLarge)
//            Spacer(Modifier.height(16.dp))
//            Box(
//                modifier = Modifier
//                    .size(200.dp)
//                    .background(Color.Gray),
//                contentAlignment = Alignment.Center
//            ) {
//                Text("アルバムアート", color = Color.White)
//            }
//            Spacer(Modifier.height(16.dp))
//            Text("曲名", style = MaterialTheme.typography.titleMedium)
//            Text("アーティスト名", style = MaterialTheme.typography.bodyMedium)
//            Spacer(Modifier.height(8.dp))
//            Button(onClick = { /* TODO: Spotifyログイン処理 */ }) {
//                Text("Spotifyに接続して再生")
//            }
//        }
//    }
//}