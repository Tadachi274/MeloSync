// ui/auth/AuthApi.kt
package com.example.melosync.ui.auth

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

data class JwtResponse(val access_token: String)

interface AuthApi {
    @POST("api/auth/google-login")
    suspend fun LoginRequest(): Response<JwtResponse>
}