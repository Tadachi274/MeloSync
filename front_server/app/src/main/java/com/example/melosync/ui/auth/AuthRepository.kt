// ui/auth/AuthRepository.kt
package com.example.melosync.ui.auth

import com.example.melosync.R
import android.content.Context
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AuthRepository(private val ctx: Context) {


    /** ID トークンをバックエンドに送って JWT をもらう */
    suspend fun exchangeIdToken(idToken: String): String? {
        val resp = NetworkModule.authApi.exchangeIdToken(IdTokenRequest(idToken))
        return if (resp.isSuccessful) resp.body()?.access_token else null
    }

    /** JWT 保存 */
    suspend fun saveJwt(token: String) {
        //dataStore.edit { it[JWT_KEY] = token }
    }

    /** JWT クリア（ログアウト） */
    suspend fun clearJwt() {
        //dataStore.edit { it.remove(JWT_KEY) }
    }

    /** JWT があるか */
    suspend fun hasJwt() {
        //return dataStore.data.map { prefs -> prefs[JWT_KEY] }.first() != null
    }
}