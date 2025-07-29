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
    private const val BACKEND_BASE_URL = "http://172.20.10.14:8003/" // Androidエミュレータ用のIP
    private const val BACKEND_BASE_URL_AI = "http://172.20.10.14:8004/"
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

    val backendApiAI: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BACKEND_BASE_URL_AI)
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
