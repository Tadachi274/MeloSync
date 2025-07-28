package com.example.melosync

import com.example.melosync.data.Emotion
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {
    @POST("/heartrate")
    suspend fun sendHeartRate(@Body heartRate: HeartRate): Response<ApiResponse>

    @POST("/analyze_emotion")
    suspend fun analyzeEmotion(@Body mood: Emotion2): Response<EmotionResponse>

}

