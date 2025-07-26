package com.example.melosync.ui.main

import androidx.compose.ui.geometry.Offset
//import androidx.compose.ui.unit.Dp
//import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import com.example.melosync.data.Emotion
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin
import kotlin.random.Random

data class EmotionCoordinate(val x: Float, val y: Float)

class MainViewModel : ViewModel() {
    private val _emotionCoordinate = MutableStateFlow(EmotionCoordinate(0f, 0f))
    val emotionCoordinate = _emotionCoordinate.asStateFlow()

    // 現在の象限を保持する (1, 2, 3, 4 もしくは 0)
    private val _currentQuadrant = MutableStateFlow(0)
    val currentQuadrant = _currentQuadrant.asStateFlow()

    fun setEmotion(emotion: Emotion) {
        val x = when (emotion) {
            Emotion.HAPPY -> 0.6f
            Emotion.NEUTRAL -> 0.2f
            Emotion.SAD -> -0.6f
        }
        // y座標は-1.0から1.0の間のランダムな値
        val y = (Random.nextFloat() * 2f - 1f) * 0.7f

        _emotionCoordinate.value = EmotionCoordinate(x, y)
        updateQuadrant(x, y)
    }

    fun updateCoordinate(rawOffset: Offset, canvasSizePx: Float, radiusPx: Float) {
        // Canvasの中心を原点(0,0)とした座標に変換
        val centerX = canvasSizePx / 2f
        val centerY = canvasSizePx / 2f

        var dx = rawOffset.x - centerX
        var dy = rawOffset.y - centerY

        // 距離を計算
        val distance = kotlin.math.sqrt(dx * dx + dy * dy)
        val r = radiusPx

        // 円の外に出ないように座標を制限
        if (distance > r) {
            dx = (dx / distance) * r
            dy = (dy / distance) * r
        }

        // -1.0f ~ 1.0f の正規化された座標に変換
        val normalizedX = dx / r
        val normalizedY = -dy / r // Y軸を反転

        _emotionCoordinate.value = EmotionCoordinate(normalizedX, normalizedY)
        updateQuadrant(normalizedX, normalizedY)
    }

    /**
     * 座標から現在の象限を計算します。
     */
    private fun updateQuadrant(x: Float, y: Float) {
        _currentQuadrant.value = when {
            x > 0 && y > 0 -> 1
            x < 0 && y > 0 -> 2
            x < 0 && y < 0 -> 3
            x > 0 && y < 0 -> 4
            else -> 0 // 軸上
        }
    }
}