package com.example.melosync.ui.auth

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

/**
 * 認証状態を表す UI モデル
 */
data class AuthUiState(
    val isLoading: Boolean = false,
    val isLoggedIn: Boolean = false,
    val errorMessage: String? = null
)

class AuthViewModel(app: Application) : AndroidViewModel(app) {
    private val repository = AuthRepository(app.applicationContext)

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    init {
        // 起動時に既存トークンの有無をチェック
        viewModelScope.launch {
            val hasJwt = repository.hasJwt()
            println("[AuthViewmodel] hasJwt:${hasJwt}")
            //val hasJwt = false
            _uiState.update { it.copy(isLoggedIn = hasJwt) }
        }
    }

    /** ボタンなどから呼び出すサインイン処理 */
    fun signIn() {
        println("SignIn Click")
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            try {
                // Google ID トークン取得（ユーザー操作でダイアログが出ます）
                val idToken = "example_user_id"  // :contentReference[oaicite:0]{index=0}
                println("[AuthViewmodel]idToken: ${idToken}")
                if (idToken != null) {
                    // バックエンドとやりとりして JWT を取得
                    val jwt = repository.exchangeIdToken(idToken)
                    println("[AuthViewmodel]jwt:${jwt}")
                    if (jwt != null) {
                        repository.saveJwt(jwt)
                        _uiState.update { it.copy(isLoggedIn = true) }
                    } else {
                        _uiState.update { it.copy(errorMessage = "サーバーから JWT を取得できませんでした") }
                    }
                } else {
                    _uiState.update { it.copy(errorMessage = "サインインがキャンセルされました") }
                }
            } catch (e: Exception) {
                _uiState.update { it.copy(errorMessage = e.localizedMessage) }
            } finally {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }

    /** ログアウト処理 */
    fun logout() {
        viewModelScope.launch {
            repository.clearJwt()
            _uiState.update { it.copy(isLoggedIn = false) }
        }
    }
}
