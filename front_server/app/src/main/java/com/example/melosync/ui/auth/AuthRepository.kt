// ui/auth/AuthRepository.kt
package com.example.melosync.ui.auth

import com.example.melosync.R
import android.content.Context
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.single
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.credentials.CredentialManager
import androidx.credentials.GetCredentialRequest
import com.google.android.libraries.identity.googleid.GetGoogleIdOption
import androidx.credentials.exceptions.GetCredentialException
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import kotlinx.coroutines.withContext

class AuthRepository(private val ctx: Context) {
    private val dataStore = ctx.dataStore
    private val JWT_KEY = stringPreferencesKey("jwt_token")

    private val credentialManager = CredentialManager.create(ctx)
    private val serverClientId = ctx.getString(R.string.server_client_id)

    /**
     * Google ID トークンを取得する。
     * 成功すると ID トークン文字列、失敗（ユーザーキャンセル／未ログイン）すると null。
     */
    suspend fun requestGoogleIdToken(): String? = withContext(Dispatchers.Main) {
        val googleOption = GetGoogleIdOption.Builder()
            .setServerClientId(serverClientId)
            .setFilterByAuthorizedAccounts(false)  // 既存ユーザー選択なら true
            .build()

        val req = GetCredentialRequest.Builder()
            .addCredentialOption(googleOption)
            .build()

        return@withContext try {
            val resp = credentialManager.getCredential(ctx,req)
            // レスポンスから ID トークンを取り出す
            (resp.credential as? GoogleIdTokenCredential)?.idToken
        } catch (e: GetCredentialException) {
            null
        }
    }

    /** ID トークンをバックエンドに送って JWT をもらう */
    suspend fun exchangeIdToken(idToken: String): String? {
        val resp = NetworkModule.authApi.exchangeIdToken(IdTokenRequest(idToken))
        return if (resp.isSuccessful) resp.body()?.access_token else null
    }

    /** JWT 保存 */
    suspend fun saveJwt(token: String) {
        dataStore.edit { it[JWT_KEY] = token }
    }

    /** JWT クリア（ログアウト） */
    suspend fun clearJwt() {
        dataStore.edit { it.remove(JWT_KEY) }
    }

    /** JWT があるか */
    suspend fun hasJwt(): Boolean {
        return dataStore.data.map { prefs -> prefs[JWT_KEY] }.first() != null
    }
}
