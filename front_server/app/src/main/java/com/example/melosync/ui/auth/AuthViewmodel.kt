package com.example.melosync.ui.auth

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import android.util.Log
import com.example.melosync.ui.auth.spotify.*
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

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

    fun onSpotifyAuthCodeReceived(code: String) {
        viewModelScope.launch {
            val jwt = repository.getJwt()
            val request = SpotifyCodeRequest(code)
            if (jwt.isNullOrEmpty()) return@launch


            val call: Call<SpotifyAuthResponse> =
                SpotifyNetworkModule.spotifyAuthApi.sendCode("Bearer $jwt", request)
            call.enqueue(object : Callback<SpotifyAuthResponse> {
                override fun onResponse(
                    call: Call<SpotifyAuthResponse>,
                    response: Response<SpotifyAuthResponse>
                ) {
                    if (response.isSuccessful) {
                        viewModelScope.launch {
                            repository.setSpotifyLoggedIn(true)
                            _uiState.update { it.copy(isSpotifyLoggedIn = true) }  // ← これで HomeScreen が再コンポーズ
                            Log.d("AuthViewmodel", "送信成功: jwt=, refreshToken=")
                        }
                    } else {
                        Log.e(
                            "AuthViewmodel",
                            "送信失敗: status=${response.code()}, error=${response.errorBody()?.string()}"
                        )
                    }
                }

                override fun onFailure(call: Call<SpotifyAuthResponse>, t: Throwable) {
                    Log.e("AuthViewmodel", "ネットワークエラー", t)
                }
            })
        }
    }

    fun onSpotifyLoginSuccess() {
        Log.d("AuthViewmodel","SpotifyLoginSuccess!")
        viewModelScope.launch {
            // 永続化
            repository.setSpotifyLoggedIn(true)
            _uiState.update { it.copy(isSpotifyLoggedIn = true) }
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

