package com.example.melosync.ui.auth.spotify

import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.ComponentActivity
import androidx.lifecycle.lifecycleScope
import com.example.melosync.ui.auth.AuthRepository
import com.example.melosync.ui.auth.AuthUiState
import com.example.melosync.ui.home.HomeScreen
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import android.content.Intent
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import com.example.melosync.MainActivity
import com.example.melosync.ui.auth.AuthViewModel
import androidx.activity.viewModels
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow


class SpotifyAuthCallbackActivity : ComponentActivity() {
    private val TAG = "SpotifyAuthCode"
    val repository by lazy { AuthRepository(applicationContext) }
    val authViewModel: AuthViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Intent の data をログ出力
        val uri = intent?.data
        Log.d(TAG, "onCreate: uri=$uri")

        // クエリパラメータから code を取得
        val code = uri?.getQueryParameter("code")
        val error = uri?.getQueryParameter("error")

        if (code != null) {
            Log.d(TAG, "認証コード(code) = $code")
            //if (code != null) {
            //    authViewModel.onSpotifyAuthCodeReceived(code)          // ※2
            //}
            lifecycleScope.launch {
                val jwt = repository.getJwt()  // suspend 関数なので coroutine 内で呼び出し
                Log.d(TAG,"jwt:${jwt}")
                if (!jwt.isNullOrEmpty()) {
                    Log.d(TAG,"sendCode" )
                    sendCodeAndJwtToBackend(code, jwt)
                } else {
                    Log.e("SpotifyAuth", "No JWT found")
                }
            }
        }
        else {
            Log.e(TAG, "認証エラー(error) = $error")
        }
        finish()
    }

//今は使っていない
    private fun sendCodeAndJwtToBackend(code: String, jwt: String) {
        val TAG = "SpotifyAuthCallback"
        val request = SpotifyCodeRequest(code)
        val call: Call<SpotifyAuthResponse> =
            SpotifyNetworkModule.spotifyAuthApi.sendCode("Bearer $jwt", request)

        call.enqueue(object : Callback<SpotifyAuthResponse> {
            override fun onResponse(
                call: Call<SpotifyAuthResponse>,
                response: Response<SpotifyAuthResponse>
            ) {
                if (response.isSuccessful) {
                    val body = response.body()
                    Log.d(TAG, "送信成功: jwt=${body?.jwt}, refreshToken=${body?.refreshToken}")
                    // 必要ならここで UI 更新や次画面遷移などを行う
                    lifecycleScope.launch {
                        repository.setSpotifyLoggedIn(true)
                        Log.d(TAG,"SpotifyLoggedIn:${repository.getSpotifyLoggedIn()}")
                        // 必要に応じて JWT も保存
                    }
                    startActivity(
                        Intent(
                            this@SpotifyAuthCallbackActivity,
                            MainActivity::class.java
                        ).apply {
                            flags =
                                Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
                        })
                    finish()

                } else {
                    Log.e(
                        TAG,
                        "送信失敗: status=${response.code()}, error=${response.errorBody()?.string()}"
                    )
                    finish()
                }
            }

            override fun onFailure(call: Call<SpotifyAuthResponse>, t: Throwable) {
                Log.e(TAG, "ネットワークエラー", t)
                finish()
            }
        })
    }
}