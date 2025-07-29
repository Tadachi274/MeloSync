// ui/auth/NetworkModule.kt
package com.example.melosync.ui.auth

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object NetworkModule {
    //private const val BASE_URL = "https://bd1a97e38112.ngrok-free.app"
    private const val BASE_URL = "http://10.0.2.2:8000"
    val authApi: AuthApi = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(AuthApi::class.java)
}