package com.example.melosync

data class ApiResponse(
    val status: String,
    val data: HeartRate
)

data class EmotionResponse(
    val emotion: String
)