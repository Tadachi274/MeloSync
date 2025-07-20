// ui/auth/AuthApi.kt
package com.example.melosync.ui.auth

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

data class IdTokenRequest(val id_token: String)
data class JwtResponse(val access_token: String)

interface AuthApi {
    @POST("auth/google-login")
    suspend fun exchangeIdToken(@Body req: IdTokenRequest): Response<JwtResponse>
}