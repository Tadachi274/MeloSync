package com.example.melosync.ui.home

import androidx.lifecycle.ViewModel
import com.example.melosync.data.Emotion
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class HomeViewModel : ViewModel() {
    // UIの状態を保持
    private val _selectedEmotion = MutableStateFlow<Emotion?>(null)
    val selectedEmotion = _selectedEmotion.asStateFlow()

    fun onEmotionSelected(emotion: Emotion) {
        _selectedEmotion.value = emotion
    }
}