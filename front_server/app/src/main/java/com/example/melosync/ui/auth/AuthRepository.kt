// ui/auth/AuthRepository.kt
package com.example.melosync.ui.auth

import com.example.melosync.R
import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import androidx.datastore.preferences.core.booleanPreferencesKey

private object PrefKeys {
    val SPOTIFY_LOGGED_IN = booleanPreferencesKey("spotify_logged_in")
}
class AuthRepository(private val ctx: Context) {
    private val dataStore = ctx.dataStore
    private val JWT_KEY = stringPreferencesKey("jwt_token")

    /** ID トークンをバックエンドに送って JWT をもらう */
    suspend fun exchangeIdToken(idToken: String): String? {
        println("[AuthRepository.exchangeIdToken]exchangeIdToken")
        val resp = NetworkModule.authApi.exchangeIdToken(IdTokenRequest(idToken))
        println("[AuthRepository.exchangeIdToken]exchange.res:${resp}")
        return if (resp.isSuccessful) resp.body()?.access_token else null
    }

    /** JWT 保存 */
    suspend fun saveJwt(token: String) {
        println("[AuthRepository.saveJwt]")
        dataStore.edit { it[JWT_KEY] = token }
    }

    suspend fun getJwt(): String? {
        val prefs = dataStore.data.first()  // kotlinx.coroutines.flow.first を使います
        return prefs[JWT_KEY]
    }

    /** JWT クリア（ログアウト） */
    suspend fun clearJwt() {
        println("[AuthRepository.clearJwt]")
        dataStore.edit { it.remove(JWT_KEY) }
    }

    /** JWT があるか */
    suspend fun hasJwt():Boolean {
        return dataStore.data.map { prefs -> prefs[JWT_KEY] }.first() != null
    }

    suspend fun setSpotifyLoggedIn(loggedIn: Boolean) {
        dataStore.edit { prefs ->
            prefs[PrefKeys.SPOTIFY_LOGGED_IN] = loggedIn
        }
    }
    suspend fun getSpotifyLoggedIn(): Boolean? {
        val prefs = dataStore.data.first()  // kotlinx.coroutines.flow.first を使います
        return prefs[PrefKeys.SPOTIFY_LOGGED_IN]
    }

    suspend fun hasSpotifyLoggedIn(): Boolean {
        val prefs = dataStore.data.first()
        return prefs[PrefKeys.SPOTIFY_LOGGED_IN] ?: false
    }
}