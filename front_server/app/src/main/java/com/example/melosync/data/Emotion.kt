package com.example.melosync.data

enum class Emotion(val emoji: String) {
    SAD("😢"),
    NEUTRAL("😐"),
    HAPPY("😄")
}

enum class SendEmotion(val id: Int){
    HAPPY(1),
    ANGRY(2),
    SAD(3),
    RELAX(4)
}