// ui/auth/NetworkModule.kt
package com.example.melosync.ui.auth.spotify

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object SpotifyNetworkModule {
    private const val BASE_URL = "https://d9b860c73694.ngrok-free.app"
    val spotifyAuthApi: SpotifyAuthApi = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(SpotifyAuthApi::class.java)
}