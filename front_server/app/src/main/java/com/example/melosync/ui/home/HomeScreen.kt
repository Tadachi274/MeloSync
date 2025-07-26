package com.example.melosync.ui.home

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
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.melosync.R
import com.example.melosync.data.Emotion

@Composable
fun HomeScreen(
    // When an emotion is selected, navigate to the next screen with that information.
    onNavigateToMain: (Emotion) -> Unit,
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
            // --- App Logo ---
            // R.drawable.image should be replaced with your project's logo image ID
            Image(
                painter = painterResource(id = R.drawable.image),
                contentDescription = "App Logo",
                modifier = Modifier.size(240.dp) // Logo image size
            )
            Spacer(modifier = Modifier.height(32.dp))
            Text(
                text = "今の気分は？", // How are you feeling right now?
                style = MaterialTheme.typography.headlineMedium
            )
            Spacer(modifier = Modifier.height(32.dp))

            // Arrange emotion icons horizontally
            Row(
                horizontalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                // Loop through each emotion icon and display it
                Emotion.entries.forEach { emotion ->
                    Button(
                        onClick = {
                            // Update ViewModel and navigate when icon is clicked
                            viewModel.onEmotionSelected(emotion)
                            onNavigateToMain(emotion)
                        },
                        modifier = Modifier.size(80.dp), // Button size
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primaryContainer) // Button background color
                    ) {
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