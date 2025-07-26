package com.example.melosync.ui.main

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import kotlin.math.hypot
import kotlin.math.pow
//import androidx.compose.ui.unit.Dp
//import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import com.example.melosync.data.Emotion
import com.example.melosync.data.SendEmotion
import com.example.melosync.ui.theme.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
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
    private val _firstEmotionCoordinate = MutableStateFlow(EmotionCoordinate(0f, 0f))
    val firstEmotionCoordinate = _firstEmotionCoordinate.asStateFlow()


    // 現在の象限を保持する (1, 2, 3, 4)
    private val _currentEmotion = MutableStateFlow(SendEmotion.HAPPY)
    val currentEmotion : StateFlow<SendEmotion> = _currentEmotion.asStateFlow()
    private val _firstEmotion = MutableStateFlow(SendEmotion.HAPPY)
    val firstEmotion : StateFlow<SendEmotion> = _firstEmotion.asStateFlow()

    private val _pointColor = MutableStateFlow(Color.Gray)
    val pointColor = _pointColor.asStateFlow()

    fun setEmotion(emotion: SendEmotion) {
        val x = when (emotion) {
//            Emotion.HAPPY -> 0.6f
//            Emotion.NEUTRAL -> 0.2f
//            Emotion.SAD -> -0.6f
            SendEmotion.HAPPY -> 0.4f
            SendEmotion.SAD -> -0.4f
            SendEmotion.ANGRY -> -0.4f
            SendEmotion.RELAX -> 0.4f

        }
        // y座標は-1.0から1.0の間のランダムな値
        val y =  when (emotion) {
//            Emotion.HAPPY -> 0.6f
//            Emotion.NEUTRAL -> 0.2f
//            Emotion.SAD -> -0.6f
            SendEmotion.HAPPY -> 0.4f
            SendEmotion.SAD -> -0.4f
            SendEmotion.ANGRY -> 0.4f
            SendEmotion.RELAX -> -0.4f

        }
        _emotionCoordinate.value = EmotionCoordinate(x, y)
        _firstEmotionCoordinate.value = EmotionCoordinate(x, y)
        updateQuadrant(x, y)
        _firstEmotion.value = _currentEmotion.value
        _pointColor.value = calculateColorFromCoordinate(x, y)
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
        _pointColor.value = calculateColorFromCoordinate(normalizedX, normalizedY)
    }

    /**
     * 座標から現在の象限を計算します。
     */
    private fun updateQuadrant(x: Float, y: Float) {
        _currentEmotion.value = when {
            x > 0 && y > 0 -> SendEmotion.HAPPY
            x < 0 && y > 0 -> SendEmotion.ANGRY
            x < 0 && y < 0 -> SendEmotion.SAD
            x > 0 && y < 0 -> SendEmotion.RELAX
            else -> SendEmotion.HAPPY // 軸上
        }
    }

    private fun calculateColorFromCoordinate(x: Float, y: Float): Color {
        // --- 準備 ---
        val colorQ1 = Happy // 第1象限 (右上が黄)
        val colorQ2 = Angry   // 第2象限 (左上が赤)
        val colorQ3 = Sad  // 第3象限 (左下が青)
        val colorQ4 = Relax   // 第4象限 (右下が緑)

        val distance = hypot(x, y)
        val maxDistance = hypot(1.0f, 1.0f)

        val innerThreshold = maxDistance * 0.5f
        val outerThreshold = maxDistance * 0.9f

        // --- エリアに応じて処理を分岐 ---
        return when {
            // --- 1. 中心エリア (変更なし) ---
            distance < innerThreshold -> {
                val fixedX: Float
                val fixedY: Float
                if (distance == 0f) {
                    fixedX = 0f
                    fixedY = 0f
                } else {
                    val scale = innerThreshold / distance
                    fixedX = x * scale
                    fixedY = y * scale
                }
                val tX = (fixedX + 1) / 2f
                val tY = (fixedY + 1) / 2f
                val baseColor = lerp(lerp(colorQ3, colorQ4, tX), lerp(colorQ2, colorQ1, tX), tY)
                val innerRatio = 1.0f - (distance / innerThreshold)
                val whiteBlendFraction = innerRatio.pow(2)
                lerp(baseColor, Base, whiteBlendFraction)
            }

            // --- 2. 外周エリア (変更なし) ---
            distance >= outerThreshold -> {
                val scale = outerThreshold / distance
                val fixedX = x * scale
                val fixedY = y * scale
                val tX = (fixedX + 1) / 2f
                val tY = (fixedY + 1) / 2f
                lerp(lerp(colorQ3, colorQ4, tX), lerp(colorQ2, colorQ1, tX), tY)
            }

            // --- 3. 中間エリア (★ここを修正) ---
            else -> {
                // 中間エリア内での進捗率を計算 (0.0 ~ 1.0)
                val progress = (distance - innerThreshold) / (outerThreshold - innerThreshold)

                // 進捗率を使って、色の計算に使う距離を再マッピング
                // (半径0.5から1.0の範囲にスケールアップ)
                val mappedDistance = innerThreshold + progress * (maxDistance - innerThreshold)

                // 再マッピングした距離に基づいて座標をスケーリング
                val scale = mappedDistance / distance
                val mappedX = x * scale
                val mappedY = y * scale

                // スケーリングした座標で色を計算
                val tX = (mappedX + 1) / 2f
                val tY = (mappedY + 1) / 2f
                lerp(lerp(colorQ3, colorQ4, tX), lerp(colorQ2, colorQ1, tX), tY)
            }
        }
    }
    // --- ↑↑↑ ここまで追加 ---
}