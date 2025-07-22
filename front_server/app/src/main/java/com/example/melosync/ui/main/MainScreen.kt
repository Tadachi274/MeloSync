package com.example.melosync.ui.main

import android.graphics.Bitmap
import android.widget.Toast
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.foundation.Image
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.PlayArrow

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
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.melosync.data.Emotion
import com.example.melosync.ui.theme.*
import kotlin.math.roundToInt
import com.example.melosync.R
import androidx.compose.ui.res.imageResource
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.res.painterResource
import androidx.compose.material3.ButtonDefaults
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.font.FontWeight
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import com.example.melosync.ui.spotify.SpotifyViewModel
import com.spotify.protocol.types.PlayerState
import com.spotify.sdk.android.auth.AuthorizationClient
import kotlinx.coroutines.delay
import kotlin.math.roundToInt
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.CircleShape



@OptIn(ExperimentalMaterial3Api::class) // TopAppBar用に追記
@Composable
fun MainScreen(
    emotion: Emotion,
    onNavigateToSettings: () -> Unit,
    mainviewModel: MainViewModel = viewModel() ,
    spotifyViewModel: SpotifyViewModel
) {
    // ViewModelに選択された感情をセット
    LaunchedEffect(key1 = emotion) {
        mainviewModel.setEmotion(emotion)
    }

    var showMenu by remember { mutableStateOf(false) }
    val context = LocalContext.current
    // MainViewModelからの状態
    val emotionCoordinate by mainviewModel.emotionCoordinate.collectAsStateWithLifecycle()
    val firstEmotionCoordinate by mainviewModel.firstEmotionCoordinate.collectAsStateWithLifecycle()
//    val currentEmotion by mainviewModel.currentEmotion.collectAsStateWithLifecycle()
    val pointColor by mainviewModel.pointColor.collectAsStateWithLifecycle()
    // SpotifyViewModelからの状態
    val appRemote by spotifyViewModel.appRemote.collectAsState()
    val playerState by spotifyViewModel.playerState.collectAsState()
    val currentTrackImage by spotifyViewModel.currentTrackImage.collectAsState()
    // Spotify認証の結果を受け取るためのランチャー
    val authLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val response = AuthorizationClient.getResponse(result.resultCode, result.data)
        spotifyViewModel.handleAppRemoteAuthResponse(response, context)
    }
    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            // --- ここからが修正箇所 ---
            TopAppBar(
                title = {
                    Text(
                        text = emotion.emoji,
                        fontSize = 40.sp,
                    )
                },
                actions = {
                    Box {
                        IconButton(onClick = { showMenu = true }) {
                            Icon(Icons.Default.Menu, contentDescription = "メニュー")
                        }
                        DropdownMenu(
                            expanded = showMenu,
                            onDismissRequest = { showMenu = false }
                        ) {
                            if (appRemote == null) {
                                DropdownMenuItem(
                                    text = { Text("Spotifyにログイン") },
                                    onClick = {
                                        spotifyViewModel.connectToAppRemote(context, authLauncher)
                                        showMenu = false
                                    }
                                )
                            } else {
                                DropdownMenuItem(
                                    text = { Text("Spotifyから切断") },
                                    onClick = {
                                        spotifyViewModel.disconnect()
                                        showMenu = false
                                    }
                                )
                            }
                            DropdownMenuItem(
                                text = { Text("リストの設定") },
                                onClick = {
                                    onNavigateToSettings()
                                    showMenu = false
                                }
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            )
            // --- 修正箇所ここまで ---
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
//                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text =  "なりたい気分にスライドしてね",
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.padding(top = 1.dp)
            )
            // 感情グラフを表示
            EmotionGraph(
                coordinate = emotionCoordinate,
                firstCoordinate = firstEmotionCoordinate,
                pointColor = pointColor,
                onCoordinateChange = { newOffset, canvasSize, radius ->
                    mainviewModel.updateCoordinate(newOffset, canvasSize, radius)
                }
            )

            Row(
                modifier = Modifier
//                    .offset(y = (-80).dp)
//                    .padding(paddingValues)
//                    .padding(16.dp),
            ){
                OutlinedButton(
                    onClick = {
                        Toast.makeText(context, "プレイリスト選択は後で実装します", Toast.LENGTH_SHORT).show()
                    },
                    // ボタンの色をテーマに合わせて調整
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AppBackground,
                        contentColor = AppPurple2
                    )
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.change_playlist),
                        contentDescription = "プレイリスト変更",
                        modifier = Modifier.size(ButtonDefaults.IconSize) // デフォルトのアイコンサイズ
                    )
                    Spacer(modifier = Modifier.width(ButtonDefaults.IconSpacing)) // アイコンとテキストの間のスペース
                    Text("プレイリスト変更")
                }

                // 「更新」ボタン
                Button(
                    onClick = {
//                        Toast.makeText(context, "プレイリスト更新は後で実装します", Toast.LENGTH_SHORT).show()
                        spotifyViewModel.play("spotify:track:7v6DqVMaljJDUXYavMY4kf")
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AppPurple2,
                        contentColor = AppBackground
                    )
                ) {
                    Icon(
                        painter = painterResource(id = R.drawable.update_playlist),
                        contentDescription = "更新",
                        modifier = Modifier.size(ButtonDefaults.IconSize)
                    )
                    Spacer(modifier = Modifier.width(ButtonDefaults.IconSpacing))
                    Text("更新")
                }
            }

            // 現在の象限を表示
//            Text(
//                text =  currentEmotion.name,
//                style = MaterialTheme.typography.headlineSmall,
////                modifier = Modifier.padding(top = 16.dp)
//            )
//
//            Spacer(modifier = Modifier.weight(1f))

            // Spotifyプレーヤーのプレースホルダー
            SpotifyPlayerUI(
                isConnected = appRemote != null,
                playerState = playerState,
//                currentTrack = currentTrack,
                trackImage = currentTrackImage, // ★追加
                onConnectClick = { spotifyViewModel.connectToAppRemote(context, authLauncher) },
                onPauseClick = { spotifyViewModel.pause() },
                onResumeClick = { spotifyViewModel.resume() },
                onSeekTo = { position -> spotifyViewModel.seekTo(position) },
                onSkipPreviousClick = { spotifyViewModel.skipPrevious() },
                onSkipNextClick = { spotifyViewModel.skipNext() }
            )
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
    firstCoordinate: EmotionCoordinate,
    pointColor: Color,
    onCoordinateChange: (offset: Offset, canvasSizePx: Float, radiusPx: Float) -> Unit
) {
//    val primaryColor = MaterialTheme.colorScheme.primary
    val imageBitmap = ImageBitmap.imageResource(id = R.drawable.feeling)
    val textMeasurer = rememberTextMeasurer()
    val textStyle = MaterialTheme.typography.bodyMedium.copy(color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold )
    Box(
        modifier = Modifier
//            .offset(y = (-40).dp)
            .fillMaxWidth(0.9f)
            .aspectRatio(1f) // 正方形を維持
            .padding(start = 16.dp, end = 16.dp),
        contentAlignment = Alignment.Center
    ) {
        val density = LocalDensity.current
        var canvasSize by remember { mutableStateOf(0.dp) }
        val radi_rate = 2.7f

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
                color = pointColor,
//                color = Color.LightGray,
                radius = radius,
                center = center,
//                style = Stroke(width = 2.dp.toPx())
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
            val textOffset = 20.dp.toPx() // 円の外側の余白
            drawText(
                textMeasurer = textMeasurer,
                text = "快適",
                style = textStyle,
                topLeft = Offset(center.x + radius + 5.dp.toPx(), center.y - 10.dp.toPx()) // 右
            )
            drawText(
                textMeasurer = textMeasurer,
                text = "不快",
                style = textStyle,
                topLeft = Offset(center.x - radius - 35.dp.toPx(), center.y - 10.dp.toPx()) // 左
            )
            drawText(
                textMeasurer = textMeasurer,
                text = "落ち着いている",
                style = textStyle,
                topLeft = Offset(center.x - 49.dp.toPx(), center.y + radius + 3.dp.toPx()) // 下
            )
            drawText(
                textMeasurer = textMeasurer,
                text = "興奮",
                style = textStyle,
                topLeft = Offset(center.x - 15.dp.toPx(), center.y - radius - 21.dp.toPx()) // 上
            )

            // 感情の位置を計算 (-1.0f ~ 1.0f の座標をCanvasの座標に変換)
            val pointX = center.x + coordinate.x * radius
            val pointY = center.y - coordinate.y * radius // Y軸は下がプラスなので反転

            val constPointX = center.x + firstCoordinate.x * radius
            val constPointY = center.y - firstCoordinate.y * radius // Y軸は下がプラスなので反転
            // 感情の位置に点を描画
            drawCircle(
                color = PastPoint,
                radius = 12.dp.toPx(),
                center = Offset(constPointX, constPointY)
            )
            drawCircle(
                color = Shadow,
                radius = 14.dp.toPx(),
                center = Offset(pointX, pointY)
            )
            drawCircle(
//                color = pointColor,
                color = CurrentPoint,
                radius = 12.dp.toPx(),
                center = Offset(pointX, pointY)
            )
        }
    }
}

@Composable
fun SpotifyPlayerUI(
    isConnected: Boolean,
    playerState: PlayerState?,
    trackImage: Bitmap?,
    onConnectClick: () -> Unit,
    onPauseClick: () -> Unit,
    onResumeClick: () -> Unit,
    onSeekTo: (Long) -> Unit,
    onSkipPreviousClick: () -> Unit,
    onSkipNextClick: () -> Unit
) {
    val currentTrack = playerState?.track
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(4.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(
//            modifier = Modifier.padding(16.dp),
            modifier = Modifier.fillMaxWidth(),
//            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("作成されたプレイリスト", style = MaterialTheme.typography.titleSmall)
            if (isConnected) {
                // --- 接続済みのUI ---
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    // ★修正：アルバムアートを表示
                    trackImage?.let {
                        Image(
                            bitmap = it.asImageBitmap(),
                            contentDescription = "Album Art",
                            modifier = Modifier.size(64.dp)
                        )
                    } ?: Box( // 画像がない場合のフォールバック
                        modifier = Modifier
                            .size(64.dp)
                            .background(Color.Gray),
                        contentAlignment = Alignment.Center
                    ) {
                        Text("Art", color = Color.White)
                    }

                    Spacer(Modifier.width(16.dp))

                    // 曲情報
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = currentTrack?.name ?: "曲が選択されていません",
                            style = MaterialTheme.typography.titleMedium,
                            maxLines = 1,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = currentTrack?.artist?.name ?: "",
                            style = MaterialTheme.typography.bodyMedium,
                            maxLines = 1,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                Spacer(Modifier.height(16.dp))

                // --- ここからがスライダーの実装 ---
                val trackDuration = currentTrack?.duration ?: 0L
                val playbackPosition = playerState?.playbackPosition ?: 0L
                val isPaused = playerState?.isPaused ?: true

                var sliderPosition by remember { mutableFloatStateOf(0f) }
                var isSeeking by remember { mutableStateOf(false) }

                // SDKからの再生位置(playbackPosition)が変更されたときに、スライダーの位置を更新します。
                // ただし、ユーザーがスライダーを操作中(isSeeking)は更新しません。
                // これにより、SDKからの不定期な更新と、ユーザー操作が両立します。
                LaunchedEffect(playbackPosition) {
                    if (!isSeeking) {
                        sliderPosition = playbackPosition.toFloat()
                    }
                }

                // 再生中かつユーザーが操作していないときに、スライダーを滑らかに進めるためのタイマーです。
                LaunchedEffect(isPaused, isSeeking) {
                    // 再生中で、ユーザーがシークバーを操作していない場合にのみループを実行
                    if (!isPaused && !isSeeking) {
                        while (true) {
                            delay(200L) // 0.2秒ごとにスライダーを更新
                            if (sliderPosition < trackDuration) {
                                sliderPosition += 200f
                            }
                        }
                    }
                }

                Slider(
                    value = sliderPosition.coerceIn(0f, trackDuration.toFloat()), // 値が意図せず範囲外になることを防ぐ
                    onValueChange = {
                        isSeeking = true
                        sliderPosition = it
                    },
                    onValueChangeFinished = {
                        onSeekTo(sliderPosition.toLong())
                        isSeeking = false
                    },
                    valueRange = 0f..(trackDuration.toFloat().takeIf { it > 0f } ?: 1f), // durationが0の場合にエラーにならないように
                    modifier = Modifier.fillMaxWidth(),
                    colors = SliderDefaults.colors(
                        thumbColor = AppPurple2,
                        activeTrackColor = AppPurple2,
                        inactiveTrackColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.24f)
                    ),

                )

                // --- スライダーの実装ここまで ---
                // 再生コントロールボタン
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(onClick = onSkipPreviousClick) {
                        Icon(
                            painter = painterResource(id = R.drawable.skip_previous),
                            contentDescription = "前の曲へ",
                            modifier = Modifier.size(32.dp), // ★アイコンサイズを大きく
                            tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    FilledIconButton(
                        onClick = if (playerState?.isPaused == true) onResumeClick else onPauseClick,
                        modifier = Modifier.size(56.dp),
                        colors = IconButtonDefaults.filledIconButtonColors(
                            containerColor = AppPurple2,
                            contentColor = MaterialTheme.colorScheme.onPrimary
                        )
                    ) {
                        if (playerState?.isPaused == true) {
                            Icon(
                                imageVector = Icons.Default.PlayArrow,
                                contentDescription = "再開",
                                modifier = Modifier.size(36.dp)
                            )
                        } else {
                            Icon(
                                painter = painterResource(id = R.drawable.pause),
                                contentDescription = "一時停止",
                                modifier = Modifier.size(36.dp)
                            )
                        }
                    }
                    IconButton(onClick = onSkipNextClick) {
                        Icon(
                            painter = painterResource(id = R.drawable.skip),
                            contentDescription = "次の曲へ",
                            modifier = Modifier.size(32.dp), // ★アイコンサイズを大きく
                            tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            } else {
                // --- 未接続のUI ---
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .background(Color.Gray),
                        contentAlignment = Alignment.Center
                    ) {
                        Text("Art", color = Color.White)
                    }
                    Spacer(Modifier.width(16.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text("曲名", style = MaterialTheme.typography.titleMedium)
                        Text("アーティスト名", style = MaterialTheme.typography.bodyMedium)
                    }
                }
                Spacer(Modifier.height(16.dp))
                Button(
                    onClick = onConnectClick,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = AppPurple2)
                ) {
                    Text("Spotifyに接続して再生")
                }
            }

        }
    }

}
private fun formatMillis(millis: Long): String {
    val totalSeconds = millis / 1000
    val minutes = totalSeconds / 60
    val seconds = totalSeconds % 60
    return String.format("%02d:%02d", minutes, seconds)
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