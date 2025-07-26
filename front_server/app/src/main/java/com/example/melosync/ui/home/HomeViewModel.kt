package com.example.melosync.ui.home

import androidx.lifecycle.ViewModel
import com.example.melosync.data.SendEmotion
import com.example.melosync.data.Emotion
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class HomeViewModel : ViewModel() {
    // UIの状態を保持
    private val _selectedEmotion = MutableStateFlow<SendEmotion?>(null)
    val selectedEmotion = _selectedEmotion.asStateFlow()

    fun onEmotionSelected(emotion: SendEmotion) {
        _selectedEmotion.value = emotion
    }
}