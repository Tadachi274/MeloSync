package com.example.melosync.ui.setting

import androidx.compose.foundation.basicMarquee
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.draw.clip
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.res.painterResource
import com.example.melosync.R
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
//import coil.compose.SubcomposeAsyncImage

import com.example.melosync.data.Emotion
import com.example.melosync.data.api.Playlist
import com.example.melosync.ui.spotify.SpotifyViewModel
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.background // ★追加

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
//import androidx.compose.foundation.lazy.grid.GridCells
//import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
//import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.LazyRow // ★変更
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.window.Dialog
import android.content.Context
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.window.DialogProperties
import coil.ImageLoader
import okhttp3.OkHttpClient
import android.util.Log
import com.example.melosync.ui.theme.AppPurple2
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext

//import android.graphics.Bitmap
//import android.graphics.BitmapFactory
//import androidx.compose.runtime.*
//import androidx.compose.ui.graphics.asImageBitmap
//import androidx.compose.foundation.Image
//import kotlinx.coroutines.Dispatchers
//import kotlinx.coroutines.withContext
//import java.net.URL

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingScreen(
        onConfirm: () -> Unit,
        onDismissRequest:() -> Unit,
//            mainviewModel: ViewModel = viewModel(),
        spotifyViewModel: SpotifyViewModel
    ) {
    // ViewModelからプレイリストのリストを監視
    val playlists by spotifyViewModel.playlists.collectAsState()
    val context = LocalContext.current
    val imageLoader = rememberCustomImageLoader(context)
    var isAllTrue by remember { mutableStateOf(true) }

    Dialog(
        onDismissRequest = onDismissRequest,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Card(
            modifier = Modifier
                .fillMaxWidth() // 画面幅いっぱいに広げる
                .padding(horizontal = 12.dp)
                .heightIn(max = 600.dp), // 左右にカスタムの余白を指定
            shape = MaterialTheme.shapes.large,
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surface
            )
        ) {
            Column(
                modifier = Modifier.padding(12.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
//                TopAppBar(
//                    title = { Text("Playlist") },
//                    colors = TopAppBarDefaults.topAppBarColors(
//                        containerColor = Color.Transparent
//                    )
//                )
                TopAppBar(
                    title = { Text("Playlist") },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = Color.Transparent
                    ),
                    // 右側に表示するアクションボタン
                    actions = {
                        TextButton(
                            onClick = {
                                if(isAllTrue){
                                    spotifyViewModel.falsePlaylistAll()
                                    isAllTrue = false
                                }else{
                                    spotifyViewModel.truePlaylistAll()
                                    isAllTrue = true
                                }
                            }) {
                            if(isAllTrue) {
                                Text(
                                    text = "All Off",
                                    color = AppPurple2 // 指定の色を適用
                                )
                            }else{
                                Text(
                                    text = "All On",
                                    color = AppPurple2 // 指定の色を適用
                                )
                            }
                        }
                    }
                )
                // タイトル
//                Text(
//                    text = "プレイリストを選択",
//                    style = MaterialTheme.typography.titleLarge
//                )
//                Spacer(modifier = Modifier.height(8.dp))
                BoxWithConstraints(modifier = Modifier.fillMaxWidth()) {
                    // 親の最大幅の3分の1を計算
                    val itemWidth = this.maxWidth / 3
                    LazyRow(
                        modifier = Modifier.fillMaxWidth(), // 横幅いっぱいに広げる
                        contentPadding = PaddingValues(horizontal = 8.dp), // 横方向のパディング
                        horizontalArrangement = Arrangement.spacedBy(8.dp) // アイテム間のスペース
                    ) {
                        items(playlists, key = { it.playlistId }) { playlist ->
                            PlaylistItem(
                                playlist = playlist,
                                modifier = Modifier.width(itemWidth),
                                onClick = {
                                    spotifyViewModel.togglePlaylistSelection(playlist.playlistId)
                                },
                                imageLoader = imageLoader,
                            )
                        }
                    }
                }

                    // LazyVerticalGridでプレイリストを2列のグリッド表示
//                    LazyVerticalGrid(
//                        columns = GridCells.Fixed(3), // 2列に設定
//                        modifier = Modifier
//                            .fillMaxSize()
//                            .padding(paddingValues),
//                        contentPadding = PaddingValues(8.dp),
//                        verticalArrangement = Arrangement.spacedBy(8.dp),
//                        horizontalArrangement = Arrangement.spacedBy(8.dp)
//                    ) {
//                        items(playlists, key = { it.playlistId }) { playlist ->
//                            PlaylistItem(
//                                playlist = playlist,
//                                onClick = {
//                                    spotifyViewModel.togglePlaylistSelection(playlist.playlistId)
//                                },
//                                imageLoader = imageLoader,
//                            )
//                        }
                // 決定ボタン
                Button(
                    onClick = onConfirm,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AppPurple2 // テーマに合わせて色を設定
                    )
                ) {
                    Text("決定")
                }
                Divider(modifier = Modifier.padding(vertical = 2.dp))
                Button(
                    onClick = {
                        val spotifyIntent = Intent(Intent.ACTION_MAIN).apply {
                            `package` = "com.spotify.music"
                        }
                        try {
                            context.startActivity(spotifyIntent)
                        } catch (e: ActivityNotFoundException) {
                            val fallbackIntent = Intent(
                                Intent.ACTION_VIEW,
                                Uri.parse("https://open.spotify.com/")
                            )
                            context.startActivity(fallbackIntent)
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color.Transparent, // Spotifyグリーン
                        contentColor = Color.Black
                    )
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            painter = painterResource(id = R.drawable.spotify_logo),
                            contentDescription = "Spotify Logo",
                            modifier = Modifier.size(24.dp)
                        )
                        Text("Spotifyで開く")
                    }
                }

            }
        }
    }
}


@Composable
fun PlaylistItem(
    playlist: Playlist,
    modifier: Modifier = Modifier, // Modifierを受け取るように変更
    imageLoader: ImageLoader,
    onClick: () -> Unit
) {
//    var bitmap by remember { mutableStateOf<Bitmap?>(null) }
//
//    LaunchedEffect(playlist.imageUrl) {
//        bitmap = loadBitmapFromUrl(playlist.imageUrl)
//    }
    Card(
        modifier = modifier
//            .fillMaxWidth(1/3f)
//            .width(140.dp) // ダイアログに合わせて少し幅を調整
            .clickable(onClick = onClick)
            .padding(2.dp),
//            .fillMaxWidth()
//            .background(Color.Transparent)
//            .clickable(onClick = onClick)
//            .padding(2.dp),
        shape = RectangleShape,
        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
    ) {
        // Boxを使用して画像を基礎に、オーバーレイを重ねる
        Box(
            modifier = Modifier
                .clip(RectangleShape),
//                .clip(MaterialTheme.shapes.medium), // Cardの角丸に合わせる
//                .background(Color.Transparent),
//                .clickable(onClick = onClick),
            contentAlignment = Alignment.Center

        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Box(contentAlignment = Alignment.BottomEnd) {
                    AsyncImage(
                        model = playlist.imageUrl,
                        imageLoader = imageLoader,
                        contentDescription = playlist.playlistName,
                        placeholder = painterResource(id = R.drawable.pause),
                        error = painterResource(id = R.drawable.skip),
                        modifier = Modifier
                            .fillMaxWidth()
                            .aspectRatio(1f),
                        contentScale = ContentScale.Crop
                    )
//                    if (bitmap != null) {
//                        Image(
//                            bitmap = bitmap!!.asImageBitmap(),
//                            contentDescription = playlist.playlistName,
//                            modifier = Modifier
//                                .fillMaxWidth()
//                                .aspectRatio(1f),
//                            contentScale = ContentScale.Crop
//                        )
//                    } else {
//                        // 読み込み中やエラー時のプレースホルダー画像
//                        androidx.compose.foundation.Image(
//                            painter = painterResource(id = R.drawable.pause),
//                            contentDescription = "placeholder",
//                            modifier = Modifier
//                                .fillMaxWidth()
//                                .aspectRatio(1f),
//                            contentScale = ContentScale.Crop
//                        )
//                    }
                    if (playlist.isActive) {
                        // 半透明の黒いオーバーレイ
                        Box(
                            modifier = Modifier
                                .matchParentSize() // 親(Box)と同じサイズにする
                                .background(Color.Black.copy(alpha = 0.5f))
                        )
                        // チェックマークアイコン

                        Icon(
                            imageVector = Icons.Default.Check,
                            contentDescription = "Selected",
                            tint = Color.White,
                            modifier = Modifier.size(30.dp)
                                .padding(5.dp)
                        )
                    }
                }

                Text(
                    text = playlist.playlistName,
                    style = MaterialTheme.typography.titleMedium,
                    textAlign = TextAlign.Center,
                    maxLines = 1,
                    modifier = Modifier
                        .fillMaxWidth()
                        .basicMarquee()
//                        .padding(vertical = 8.dp)

                )
            }
            // isActiveがtrueの場合にオーバーレイとチェックマークを表示

        }
    }
}

    @Composable
    fun NetworkImage(imageUrl: String) {
        AsyncImage(
            model = imageUrl, // 表示したい画像のURL
            contentDescription = "プレイリストのジャケット写真", // 画像の説明 (アクセシビリティのため)
            modifier = Modifier.size(128.dp), // 画像のサイズを指定
            contentScale = ContentScale.Crop // 画像の表示方法を調整
        )
    }

    @Preview(showBackground = true)
    @Composable
    fun PreviewNetworkImage() {
        // ユーザーが提供したJSON内のURLを例として使用
        val sampleUrl = "https://mosaic.scdn.co/640/ab67616d00001e0257a4e5830ef3e0aeee2874ceab67616d00001e028ac80cfc486397adceeaf15aab67616d00001e029cbe133c32610c326ec72a53ab67616d00001e02bf24352caf35d83d05519573"
        NetworkImage(imageUrl = sampleUrl)
    }

//suspend fun loadBitmapFromUrl(url: String): Bitmap? = withContext(Dispatchers.IO) {
//    try {
//        val connection = URL(url).openConnection()
//        connection.connect()
//        val input = connection.getInputStream()
//        BitmapFactory.decodeStream(input)
//    } catch (e: Exception) {
//        e.printStackTrace()
//        null
//    }
//}

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

