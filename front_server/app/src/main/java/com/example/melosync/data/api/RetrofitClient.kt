package com.example.melosync.data.api

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

/**
 * Retrofitのインスタンスをシングルトンで提供するオブジェクト
 */
object RetrofitClient {

    // 1. あなたのバックエンドサーバーのURL
    private const val BACKEND_BASE_URL = "http://10.0.2.2:8000/" // Androidエミュレータ用のIP

    // 2. Spotify Web APIのURL
    private const val SPOTIFY_API_BASE_URL = "https://api.spotify.com/"

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    /**
     * あなたのバックエンドと通信するためのApiService
     */
    val backendApi: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BACKEND_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }

    /**
     * Spotify Web APIと通信するためのApiService
     */
    val spotifyApi: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(SPOTIFY_API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
