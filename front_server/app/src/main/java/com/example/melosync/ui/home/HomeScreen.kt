package com.example.melosync.ui.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.melosync.data.Emotion
import com.example.melosync.ui.spotify.SpotifyViewModel


@Composable
fun HomeScreen(
    // 感情が選択されたら、その情報を元に次の画面へ遷移する
    onNavigateToMain: (Emotion) -> Unit,
    spotifyViewModel: SpotifyViewModel,
    viewModel: HomeViewModel = viewModel()
) {
    Scaffold { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
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
                    Text(
                        text = emotion.emoji,
                        fontSize = 64.sp,
                        modifier = Modifier.clickable {
                            // アイコンクリックでViewModelを更新し、画面遷移を実行
                            viewModel.onEmotionSelected(emotion)
                            spotifyViewModel.loadPlaylists()
                            onNavigateToMain(emotion)
                        }
                    )
                }
            }
        }
    }
}