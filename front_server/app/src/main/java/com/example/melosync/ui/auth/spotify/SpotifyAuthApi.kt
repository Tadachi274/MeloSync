package com.example.melosync.ui.auth.spotify

import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Header
import retrofit2.Call

// リクエストボディには code のみ
data class SpotifyCodeRequest(val code: String)

// レスポンス例
data class SpotifyAuthResponse(val jwt: String, val refreshToken: String)

interface SpotifyAuthApi {
    @POST("api/spotify/callback")
    fun sendCode(
        @Header("Authorization") authorization: String,
        @Body body: SpotifyCodeRequest
    ): Call<SpotifyAuthResponse>
}