package com.example.melosync.ui.home

import android.util.Log
import androidx.compose.foundation.clickable
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.melosync.R
import com.example.melosync.ApiClient
import com.example.melosync.data.Emotion
import com.example.melosync.data.SendEmotion
import com.example.melosync.Emotion2
import com.example.melosync.ui.auth.AuthViewModel
import com.example.melosync.ui.auth.LogoutButton
import com.example.melosync.ui.spotify.SpotifyViewModel
import kotlinx.coroutines.launch
import androidx.compose.runtime.rememberCoroutineScope
import com.example.melosync.EmotionResponse
import retrofit2.Response

@Composable
fun HomeScreen(
    // 感情が選択されたら、その情報を元に次の画面へ遷移する
    onNavigateToMain: (SendEmotion) -> Unit={},
    viewModel: HomeViewModel = viewModel() ,
    authViewModel: AuthViewModel,
    spotifyViewModel: SpotifyViewModel
) {
    val apiService = ApiClient.apiService
    val scope = rememberCoroutineScope()
    Scaffold { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // --- App Logo ---
            // R.drawable.image should be replaced with your project's logo image ID
            Image(
                painter = painterResource(id = R.drawable.image),
                contentDescription = "App Logo",
                modifier = Modifier.size(240.dp) // Logo image size
            )
            Spacer(modifier = Modifier.height(32.dp))
            Text(
                text = "今の気分は？",
                style = MaterialTheme.typography.headlineMedium
            )
            Spacer(modifier = Modifier.height(32.dp))

            // 感情アイコンを横に並べる
            Row(
                horizontalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                // 各感情アイコンをループで表示
                Emotion.entries.forEach { emotion ->
                    Button(
                        modifier = Modifier.size(80.dp), // Button size
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primaryContainer), // Button background color
                        shape = RoundedCornerShape(50), // 丸み
                        elevation = ButtonDefaults.buttonElevation(
                            defaultElevation = 6.dp,
                            pressedElevation = 8.dp,
                            disabledElevation = 0.dp
                        ),
                        onClick = {
                            scope.launch {
                                try {
                                    Log.d("HomeScreen","EmotionButtonClick")
                                    spotifyViewModel.setJwt() //JWTセット
                                    spotifyViewModel.loadPlaylists()
                                    // 1. APIを呼び出し、レスポンスを取得
                                    val response = apiService.analyzeEmotion(Emotion2(emotion.name))
                                    Log.d("HomeScreen","analyzeEmotion:${response.isSuccessful}")
                                    // 2. レスポンスが成功し、中身がnullでないことを確認
                                    if (response.isSuccessful && response.body() != null) {
                                        val emotionResponse = response.body()!!

                                        // APIから返されたID（文字列）をIntに変換
                                        val emotionId = emotionResponse.emotion.toIntOrNull()

                                        // IDを使って正しいenum定数を検索
                                        val analyzedEmotion = SendEmotion.entries.firstOrNull { it.id == emotionId }

                                        // analyzedEmotionがnullでないことを確認
                                        if (analyzedEmotion != null) {
                                            // このブロック内では analyzedEmotion は non-null (SendEmotion型) として扱える
                                            Log.d("TransPage", "Analyzed as: ${analyzedEmotion.name}") // OK
                                            viewModel.onEmotionSelected(analyzedEmotion) // OK
                                            onNavigateToMain(analyzedEmotion) // OK
                                        } else {
                                            // APIから返されたIDが不正で、enumが見つからなかった場合の処理
                                            Log.e("HomeScreen", "Invalid emotion ID from API: ${emotionResponse.emotion}. Falling back.")
                                            viewModel.onEmotionSelected(emotion.toSendEmotion())
                                            onNavigateToMain(emotion.toSendEmotion())
                                        }
                                    } else {
                                        // API呼び出しが失敗した場合の処理
                                        Log.e("HomeScreen", "API Error: ${response.errorBody()?.string()}")
                                        // エラー時も、クリックした感情で遷移させるなどのフォールバック処理
                                        viewModel.onEmotionSelected(emotion.toSendEmotion())
                                        onNavigateToMain(emotion.toSendEmotion())
                                    }
                                } catch (e: Exception) {
                                    // ネットワークエラーなどの例外処理
                                    Log.e("HomeScreen", "Exception: ${e.message}")
                                    viewModel.onEmotionSelected(emotion.toSendEmotion())
                                    onNavigateToMain(emotion.toSendEmotion())
                                }
                            }

                        }
                    ){
                        Box(
                            modifier = Modifier.fillMaxSize(), // Expand Box to fill the entire button
                            contentAlignment = Alignment.Center // Center content within the Box
                        ) {
                            Image(
                                painter = painterResource(id = emotion.drawableId),
                                contentDescription = emotion.name, // For accessibility
                                modifier = Modifier.size(48.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

fun Emotion.toSendEmotion(): SendEmotion = when (this) {
    Emotion.HAPPY -> SendEmotion.HAPPY
    Emotion.SAD -> SendEmotion.SAD
    Emotion.NEUTRAL -> SendEmotion.RELAX // or any fallback
}
