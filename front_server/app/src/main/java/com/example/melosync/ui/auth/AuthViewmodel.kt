package com.example.melosync.ui.auth

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import android.util.Log
/**
 * 認証状態を表す UI モデル
 */
data class AuthUiState(
    val isLoading: Boolean = false,
    val isLoggedIn: Boolean = false,
    val isSpotifyLoggedIn:Boolean = false,
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
            Log.d("[AuthViewmodel]"," hasJwt:${hasJwt}")
            _uiState.update { it.copy(isLoggedIn = hasJwt) }
            val hasSpotifyLoggedIn = repository.hasSpotifyLoggedIn()
            Log.d("[AuthViewmodel]","hasSpotifyLoggedIn:${hasSpotifyLoggedIn}")
            _uiState.update { it.copy(isLoggedIn = hasSpotifyLoggedIn) }
        }
    }

    /** ボタンなどから呼び出すサインイン処理 */
    fun signIn() {
        Log.d("AuthViewModel","SignIn Click")
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            try {
                // バックエンドとやりとりして JWT を取得
                val jwt = repository.loginRequest()
                Log.d("AuthViewmodel","jwt:${jwt}")
                if (jwt != null) {
                    repository.saveJwt(jwt)
                    _uiState.update { it.copy(isLoggedIn = true) }
                    _uiState.update { it.copy(isSpotifyLoggedIn = false) }
                } else {
                    _uiState.update { it.copy(errorMessage = "サーバーから JWT を取得できませんでした") }
                }
            } catch (e: Exception) {
                _uiState.update { it.copy(errorMessage = e.localizedMessage) }
            } finally {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }

    fun onSpotifyLoginSuccess() {
        Log.d("AuthViewmodel","SpotifyLoginSuccess!")
        viewModelScope.launch {
            // 永続化
            repository.setSpotifyLoggedIn(true)
            //_uiState.update { it.copy(isSpotifyLoggedIn = true) }
            _uiState.update {
                val updated = it.copy(isSpotifyLoggedIn = true)
                Log.d("ViewModel", "Updating isSpotifyLoggedIn to: ${updated.isSpotifyLoggedIn}")
                updated
            }
        }
    }

    /** ログアウト処理 */
    fun logout() {
        viewModelScope.launch {
            repository.clearJwt()
            repository.setSpotifyLoggedIn(false)
            _uiState.update { it.copy(isLoggedIn = false) }
            _uiState.update { it.copy(isSpotifyLoggedIn = false) }
        }}
    }

