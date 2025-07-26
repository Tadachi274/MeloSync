//package com.example.melosync.data
//
//enum class Emotion(val emoji: String) {
//    SAD("😢"),
//    NEUTRAL("😐"),
//    HAPPY("😄")
//}

package com.example.melosync.data

import androidx.annotation.DrawableRes
import com.example.melosync.R // Make sure this path is correct for your project

enum class Emotion(
    val emoji: String, // You can keep the emoji if you still want it for some purpose
    @DrawableRes val drawableId: Int // This will hold the resource ID of your image
) {
    SAD(emoji = "😢", drawableId = R.drawable.sad), // Replace with your actual drawable
    NEUTRAL(emoji = "😐", drawableId = R.drawable.neutral), // Replace with your actual drawable
    HAPPY(emoji = "😄", drawableId = R.drawable.happy) // Replace with your actual drawable
}