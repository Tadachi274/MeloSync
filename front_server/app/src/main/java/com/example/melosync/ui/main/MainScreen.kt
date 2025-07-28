package com.example.melosync.ui.main

import android.content.Context
import android.graphics.Bitmap
import android.util.Log
import android.widget.Toast
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.foundation.Image
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.PlayArrow
import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically

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
import com.example.melosync.data.SendEmotion
import com.example.melosync.data.api.TrackAPI
import com.example.melosync.ui.setting.SettingScreen
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
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.clickable
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.ui.draw.rotate
import com.spotify.protocol.types.Track // SpotifyのTrackモデルをインポート
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.layout.heightIn
import androidx.compose.ui.layout.ContentScale
import coil.ImageLoader
import okhttp3.OkHttpClient
import coil.compose.AsyncImage
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.compose.material3.Divider
import androidx.compose.foundation.layout.navigationBarsPadding
import com.example.melosync.ui.auth.AuthViewModel

@OptIn(ExperimentalMaterial3Api::class) // TopAppBar用に追記
@Composable
fun MainScreen(
    emotion: SendEmotion,
    onNavigateToSettings: () -> Unit,
    onNavigateToHome: () -> Unit,
    mainviewModel: MainViewModel = viewModel() ,
    spotifyViewModel: SpotifyViewModel,
    authViewModel : AuthViewModel,
) {
    val TAG ="MainScreen"
    // ViewModelに選択された感情をセット
    LaunchedEffect(key1 = emotion) {
        mainviewModel.setEmotion(emotion)
    }

    var showMenu by remember { mutableStateOf(false) }
    var showPlaylistDialog by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val imageLoader = com.example.melosync.ui.setting.rememberCustomImageLoader(context)
    // MainViewModelからの状態
    val emotionCoordinate by mainviewModel.emotionCoordinate.collectAsStateWithLifecycle()
    val firstEmotionCoordinate by mainviewModel.firstEmotionCoordinate.collectAsStateWithLifecycle()
    //    val currentEmotion by mainviewModel.currentEmotion.collectAsStateWithLifecycle()
    val pointColor by mainviewModel.pointColor.collectAsStateWithLifecycle()
    val firstEmotion by mainviewModel.firstEmotion.collectAsStateWithLifecycle()
    val currentEmotion by mainviewModel.currentEmotion.collectAsStateWithLifecycle()
    // SpotifyViewModelからの状態
    val appRemote by spotifyViewModel.appRemote.collectAsState()
    val playerState by spotifyViewModel.playerState.collectAsState()
    val currentTrackImage by spotifyViewModel.currentTrackImage.collectAsState()
    val playbackQueue by spotifyViewModel.playbackQueue.collectAsStateWithLifecycle()
    // Spotify認証の結果を受け取るためのランチャー
    val authLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val response = AuthorizationClient.getResponse(result.resultCode, result.data)
        spotifyViewModel.handleAppRemoteAuthResponse(response, context)
    }

    LaunchedEffect(authLauncher) {
        spotifyViewModel.connectToAppRemote(context, authLauncher)
    }
    if (showPlaylistDialog) {
//        PlaylistSelectionDialog(
        SettingScreen(
            spotifyViewModel = spotifyViewModel,
            onDismissRequest = { showPlaylistDialog = false }, // ダイアログの外側をタップで閉じる
            onConfirm = {
                // ここでプレイリスト選択後の処理を実装します
                Toast.makeText(context, "プレイリストが決定されました", Toast.LENGTH_SHORT).show()
                showPlaylistDialog = false // ダイアログを閉じる
            }
        )
    }

    Scaffold(
        containerColor = Color.Transparent,
        topBar = {
            // --- ここからが修正箇所 ---
            TopAppBar(
                title = {
                    IconButton(
                        colors = IconButtonDefaults.iconButtonColors(
//                            containerColor = AppPurple2,
                            contentColor = AppPurple2,
                        ),
                        onClick = {
                            onNavigateToHome()
                        }
                    ){
                        Icon(
                        painter = painterResource(id = R.drawable.app_logo),
                        contentDescription = "ロゴ",
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(32.dp)
                        )
                    }
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
                            DropdownMenuItem(
                                text = {Text("ログアウト")},
                                onClick = {
                                    authViewModel.logout()
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
//            verticalArrangement = Arrangement.Center
//            verticalArrangement = Arrangement.Top
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text =  "なりたい気分にスライドしてね",
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.padding(top = 1.dp)
            )
            // 感情グラフを表示
            Spacer(Modifier.weight(1f))
            EmotionGraph(
                coordinate = emotionCoordinate,
                firstCoordinate = firstEmotionCoordinate,
                pointColor = pointColor,
                onCoordinateChange = { newOffset, canvasSize, radius ->
                    mainviewModel.updateCoordinate(newOffset, canvasSize, radius)
                }
            )
            Spacer(Modifier.weight(1f))
            Row(
                modifier = Modifier
                    .fillMaxWidth() // ← 親要素の幅いっぱいに広げる
                    .padding(horizontal = 16.dp), // ← 左右に余白を追加
                horizontalArrangement = Arrangement.spacedBy(8.dp) // ← ボタン間にスペースを設ける
            ){
                OutlinedButton(
                    modifier = Modifier.weight(1f), // ← weightを追加
                    onClick = {
//                        onNavigateToSettings()
                        showPlaylistDialog = true
//                        Toast.makeText(context, "プレイリスト選択は後で実装します", Toast.LENGTH_SHORT).show()
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
                    Text(
                        style = MaterialTheme.typography.bodySmall, // ← テーマからスタイルを適用
                        maxLines = 1,
                        text = "プレイリスト変更"
                    )
                }

                // 「更新」ボタン
                Button(
                    modifier = Modifier.weight(1f), // ← weightを追加
                    onClick = {
                        Log.d("Main","Click更新")
//                        Toast.makeText(context, "プレイリスト更新は後で実装します", Toast.LENGTH_SHORT).show()
//                        spotifyViewModel.play("spotify:track:7v6DqVMaljJDUXYavMY4kf")
                        spotifyViewModel.loadQueue(firstEmotion, currentEmotion)
//                        spotifyViewModel.play("spotify:track:${playbackQueue[0].trackId}")
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
            Spacer(modifier = Modifier.height(16.dp))

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
                onSkipNextClick = { spotifyViewModel.skipNext() },
                onPlayItem = {item -> spotifyViewModel.play("spotify:track:${item}")},
                queue = playbackQueue,
                imageLoader = imageLoader,
            )
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
fun TopBarWithEmotion(emotion: SendEmotion, onMenuClick: () -> Unit) {
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
                text = emotion.name,
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
    onSkipNextClick: () -> Unit,
    onPlayItem:(String) -> Unit,
    queue: List<TrackAPI>,
    imageLoader: ImageLoader,
) {
    val currentTrack = playerState?.track
    var showQueue by remember { mutableStateOf(false) }
    if (showQueue) {
        FullScreenQueue(
            playerState = playerState,
            trackImage = trackImage,
            queue = queue,
            imageLoader = imageLoader,
            onClose = { showQueue = false },
            onPauseClick = onPauseClick,
            onResumeClick = onResumeClick,
            onSeekTo = onSeekTo,
            onSkipPreviousClick = onSkipPreviousClick,
            onSkipNextClick = onSkipNextClick,
            onPlayItem = onPlayItem
        )
    }
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
                    // ★追加：キュー表示切り替えボタン
                    IconButton(onClick = { showQueue = true }) {
                        Icon(
                            imageVector = Icons.Default.KeyboardArrowUp,
                            contentDescription = "キューを表示",
//                            // showQueueがtrueのとき180度回転させて「v」にする
//                            modifier = Modifier.rotate(if (showQueue) 180f else 0f)
                        )
                    }
                }
                // ★追加：キューリストの表示エリア
//                AnimatedVisibility(visible = showQueue) {
//                    // 長いリストでもパフォーマンスが良いようにLazyColumnを使用
//                    LazyColumn(
//                        // リストが長くなりすぎないように高さを制限
//                        modifier = Modifier.heightIn(max = 200.dp).padding(top = 8.dp)
//                    ) {
//                        items(queue) { track ->
//                            QueueItem(
//                                track = track,
//                                imageLoader = imageLoader,
//                                onPlayItem = {onPlayItem(track.trackId)}
//                            ) // 各アイテムのUI
//                        }
//                    }
//                }
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
//                LaunchedEffect(isPaused, isSeeking) {
//                    // 再生中で、ユーザーがシークバーを操作していない場合にのみループを実行
//                    if (!isPaused && !isSeeking) {
//                        while (true) {
//                            delay(200L) // 0.2秒ごとにスライダーを更新
//                            if (sliderPosition < trackDuration) {
//                                sliderPosition += 200f
//                            }
//                        }
//                    }
//                }
                LaunchedEffect(isPaused, isSeeking, trackDuration, currentTrack?.uri) {
                    // 再生中で、ユーザーがシークバーを操作していない場合にのみループを実行
                    if (!isPaused && !isSeeking) {
                        while (true) {
                            delay(200L) // 0.2秒ごとにスライダーを更新

                            // スライダーが曲の最後に達したかチェック
                            if (sliderPosition < trackDuration-800f) {
                                // まだの場合はスライダーを進める
                                sliderPosition += 200f
                            } else {
                                // 曲の最後に達した場合 (または超えた場合)
                                if (trackDuration > 0) { // durationが0でないことを確認
                                    onSkipNextClick()
                                }
                                // ループを抜けてタイマーを停止
                                break
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
//                    //テストよう
                    IconButton(onClick = { showQueue = true }) {
                        Icon(
                            imageVector = Icons.Default.KeyboardArrowUp,
                            contentDescription = "キューを表示",
//                            // showQueueがtrueのとき180度回転させて「v」にする
//                            modifier = Modifier.rotate(if (showQueue) 180f else 0f)
                        )
                    }
                }
//                AnimatedVisibility(visible = showQueue) {
//                    // 長いリストでもパフォーマンスが良いようにLazyColumnを使用
//                    LazyColumn(
//                        // リストが長くなりすぎないように高さを制限
//                        modifier = Modifier.heightIn(max = 200.dp).padding(top = 8.dp)
//                    ) {
//                        items(queue) { track ->
//                            QueueItem(
//                                track = track,
//                                imageLoader = imageLoader,
//                                onPlayItem = {onPlayItem(track.trackId)}
//                            ) // 各アイテムのUI
//                        }
//                    }
//                }

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

@Composable
fun QueueItem(track: TrackAPI,imageLoader: ImageLoader,onPlayItem: () -> Unit,isCurrentlyPlaying: Boolean) {
    val backgroundColor = if (isCurrentlyPlaying) {
        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.1f)
    } else {
        Color.Transparent
    }

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
//            .size(50.dp)
            .background(backgroundColor, shape = MaterialTheme.shapes.medium) // ★背景色を適用
            .clickable { onPlayItem() }
            .padding(vertical = 2.dp)
    ) {
        // ここでは簡単なプレースホルダーを表示
        // もしキューの曲のアルバムアートも取得できるならImageに置き換える
        AsyncImage(
            model = track.imageName,
            imageLoader = imageLoader,
            contentDescription = track.trackName,
            placeholder = painterResource(id = R.drawable.pause),
            error = painterResource(id = R.drawable.skip),
            modifier = Modifier
                .size(50.dp)
                .aspectRatio(1f),
            contentScale = ContentScale.Crop
        )
        Spacer(Modifier.width(12.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = track.trackName,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 1
            )
            Text(
                text = track.artistName,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1
            )
        }
    }
}

@Composable
fun rememberCustomImageLoader(context: Context): ImageLoader {
    return remember {
        ImageLoader.Builder(context)
            .okHttpClient {
                OkHttpClient.Builder()
                    .addInterceptor { chain ->
                        val request = chain.request().newBuilder()
                            .header("User-Agent", "Android")
                            .build()
                        chain.proceed(request)
                    }
                    .build()
            }
            .build()
    }
}

@Composable
fun FullScreenQueue(
    playerState: PlayerState?,
    trackImage: Bitmap?,
    queue: List<TrackAPI>,
    imageLoader: ImageLoader,
    onClose: () -> Unit,
    onPauseClick: () -> Unit,
    onResumeClick: () -> Unit,
    onSeekTo: (Long) -> Unit,
    onSkipPreviousClick: () -> Unit,
    onSkipNextClick: () -> Unit,
    onPlayItem: (String) -> Unit
) {
    val currentTrack = playerState?.track
    val currentPlayingTrackId = playerState?.track?.uri?.substringAfter("spotify:track:")

    Dialog(
        onDismissRequest = onClose,
//        properties = DialogProperties(usePlatformDefaultWidth = false) // 全画面表示
    ) {
        // ✅ Scaffoldを使って画面の主要領域を構成
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            containerColor = MaterialTheme.colorScheme.surface,
            topBar = {
                // --- ✅ 上部：再生中の曲と閉じるボタン ---
                Column {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(start = 16.dp, end = 8.dp, top = 16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        // 再生中の曲情報
                        Row(modifier = Modifier.weight(1f), verticalAlignment = Alignment.CenterVertically) {
                            trackImage?.let {
                                Image(
                                    bitmap = it.asImageBitmap(),
                                    contentDescription = "Album Art",
                                    modifier = Modifier.size(56.dp)
                                )
                            } ?: Box(
                                modifier = Modifier
                                    .size(56.dp)
                                    .background(Color.Gray),
                                contentAlignment = Alignment.Center
                            ) { Text("Art", color = Color.White) }

                            Spacer(Modifier.width(16.dp))

                            Column {
                                Text(
                                    text = currentTrack?.name ?: "曲が選択されていません",
                                    style = MaterialTheme.typography.titleMedium,
                                    maxLines = 1,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                Text(
                                    text = currentTrack?.artist?.name ?: "",
                                    style = MaterialTheme.typography.bodyMedium,
                                    maxLines = 1,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        // 閉じるボタン
                        IconButton(onClick = onClose) {
                            Icon(Icons.Default.KeyboardArrowDown, contentDescription = "閉じる")
                        }
                    }
                    Divider(modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
                }
            },
            bottomBar = {
                // --- ✅ 下部：再生コントロールパネル ---
                Column(
                    modifier = Modifier
                        .background(MaterialTheme.colorScheme.surface)
                        .navigationBarsPadding() // システムナビゲーションバーとの重なりを回避
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    val trackDuration = currentTrack?.duration ?: 0L
                    val playbackPosition = playerState?.playbackPosition ?: 0L
                    val isPaused = playerState?.isPaused ?: true
                    var sliderPosition by remember { mutableFloatStateOf(0f) }
                    var isSeeking by remember { mutableStateOf(false) }

                    LaunchedEffect(playbackPosition) {
                        if (!isSeeking) {
                            sliderPosition = playbackPosition.toFloat()
                        }
                    }

                    LaunchedEffect(isPaused, isSeeking) {
                        if (!isPaused && !isSeeking) {
                            while (true) {
                                delay(200L)
                                if (sliderPosition < trackDuration) {
                                    sliderPosition += 200f
                                }
                            }
                        }
                    }

                    Slider(
                        value = sliderPosition.coerceIn(0f, trackDuration.toFloat()),
                        onValueChange = {
                            isSeeking = true
                            sliderPosition = it
                        },
                        onValueChangeFinished = {
                            onSeekTo(sliderPosition.toLong())
                            isSeeking = false
                        },
                        valueRange = 0f..(trackDuration.toFloat().takeIf { it > 0f } ?: 1f),
                        modifier = Modifier.fillMaxWidth(),
                        colors = SliderDefaults.colors(
                            thumbColor = AppPurple2,
                            activeTrackColor = AppPurple2,
                            inactiveTrackColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.24f)
                        )
                    )
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 8.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(onClick = onSkipPreviousClick) {
                            Icon(painter = painterResource(id = R.drawable.skip_previous), contentDescription = "前の曲へ", modifier = Modifier.size(32.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        FilledIconButton(
                            onClick = if (playerState?.isPaused == true) onResumeClick else onPauseClick,
                            modifier = Modifier.size(56.dp),
                            colors = IconButtonDefaults.filledIconButtonColors(containerColor = AppPurple2, contentColor = MaterialTheme.colorScheme.onPrimary)
                        ) {
                            if (playerState?.isPaused == true) {
                                Icon(imageVector = Icons.Default.PlayArrow, contentDescription = "再開", modifier = Modifier.size(36.dp))
                            } else {
                                Icon(painter = painterResource(id = R.drawable.pause), contentDescription = "一時停止", modifier = Modifier.size(36.dp))
                            }
                        }
                        IconButton(onClick = onSkipNextClick) {
                            Icon(painter = painterResource(id = R.drawable.skip), contentDescription = "次の曲へ", modifier = Modifier.size(32.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        ) { paddingValues ->
            // --- ✅ 中央：キューリスト ---
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues) // Scaffoldが計算したpaddingを適用
                    .padding(horizontal = 16.dp)
            ) {
                item {
                    Text(
                        text = "次に再生",
                        style = MaterialTheme.typography.titleLarge,
                        modifier = Modifier.padding(top = 8.dp, bottom = 8.dp)
                    )
                }
                items(queue) { track ->
                    val isPlaying = track.trackId == currentPlayingTrackId
                    QueueItem(
                        track = track,
                        imageLoader = imageLoader,
                        onPlayItem = { onPlayItem(track.trackId) },
                        isCurrentlyPlaying = isPlaying
                    )
                    Divider(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f))
                }
            }
        }
    }
}