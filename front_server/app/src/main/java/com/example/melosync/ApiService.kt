package com.example.melosync

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {
    @POST("/heartrate")
    suspend fun sendHeartRate(@Body heartRate: HeartRate): Response<ApiResponse>
}