// ui/auth/AuthRepository.kt
package com.example.melosync.ui.auth

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import androidx.datastore.preferences.core.booleanPreferencesKey
import android.util.Log

//private object PrefKeys {
//    val SPOTIFY_LOGGED_IN = booleanPreferencesKey("spotify_logged_in")
//}

class AuthRepository(private val ctx: Context) {
    private val dataStore = ctx.dataStore
    private val JWT_KEY = stringPreferencesKey("jwt_token")
    val SPOTIFY_LOGGED_IN = booleanPreferencesKey("spotify_logged_in")

    /** ID トークンをバックエンドに送って JWT をもらう */
    suspend fun loginRequest(): String? {
        println("[AuthRepository.LoginRequest]LoginRequest")
        val resp = NetworkModule.authApi.LoginRequest()
        println("[AuthRepository.LoginRequest]exchange.res:${resp}")
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
        //dataStore.edit { prefs ->
        //    prefs[PrefKeys.SPOTIFY_LOGGED_IN] = loggedIn
        //}
        dataStore.edit { it[SPOTIFY_LOGGED_IN] = loggedIn }
        Log.d("AuthRepository","setSpotifyLoggedIn:${loggedIn}")
    }

    suspend fun hasSpotifyLoggedIn(): Boolean {
        return dataStore.data
            .map { prefs -> prefs[SPOTIFY_LOGGED_IN] ?: false }
            .first()
    }
}