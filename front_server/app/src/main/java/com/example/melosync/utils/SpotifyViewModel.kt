package com.example.melosync.ui.spotify

import android.app.Activity
import android.app.Application
import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.activity.result.ActivityResultLauncher
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.melosync.data.api.ApiService
import com.example.melosync.data.api.Playlist
import com.example.melosync.data.api.TrackAPI
import com.example.melosync.data.SendEmotion
import android.graphics.Bitmap
import androidx.lifecycle.AndroidViewModel
import com.example.melosync.data.api.CurrentlyPlayingContext
import com.example.melosync.data.api.PlayRequest
import com.spotify.android.appremote.api.ConnectionParams
import com.spotify.android.appremote.api.Connector
import com.spotify.android.appremote.api.SpotifyAppRemote
import com.spotify.protocol.types.PlayerState
import com.spotify.protocol.types.Track
import com.example.melosync.data.api.RetrofitClient
import com.example.melosync.ui.auth.AuthRepository
import com.spotify.sdk.android.auth.AuthorizationClient
import com.spotify.sdk.android.auth.AuthorizationRequest
import com.spotify.sdk.android.auth.AuthorizationResponse
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import com.google.gson.Gson


private const val CLIENT_ID = "ced2ee375b444183a40d0a95de22d132" // あなたのClientIDに書き換えてください
private const val REDIRECT_URI = "com.example.melosync://callback"

class SpotifyViewModel(app: Application) : AndroidViewModel(app) {
    private val repository = AuthRepository(app.applicationContext)
    val TAG = "SpotifyViewModel"

    // バックエンドとの通信用
    private val backendApiService: ApiService = RetrofitClient.backendApi
    private val backendApiServiceAI: ApiService = RetrofitClient.backendApiAI
    // Spotify Web APIとの通信用
    private val spotifyApiService: ApiService = RetrofitClient.spotifyApi

    // 直前のPlayerStateを保持するための変数
    private var previousPlayerState: PlayerState? = null

    // App Remoteの接続状態
    private val _appRemote = MutableStateFlow<SpotifyAppRemote?>(null)
    val appRemote = _appRemote.asStateFlow()

    // 現在のトラック情報
    private val _currentTrack = MutableStateFlow<Track?>(null)
    val currentTrack = _currentTrack.asStateFlow()

    // 現在のPlayerStateを保持する (再生位置や曲の長さも含む)
    private val _playerState = MutableStateFlow<PlayerState?>(null)
    val playerState = _playerState.asStateFlow()

    // アクセストークン
    private val _accessToken = MutableStateFlow<String?>(null)
    val accessToken = _accessToken.asStateFlow()

    //バックエンド認証用のJWTを保持する変数
    private val _jwt = MutableStateFlow<String?>("ced2ee375b444183a40d0a95de22d132")
    val jwt = _jwt.asStateFlow()

    //再生の待ち列
    private val _playbackQueue = MutableStateFlow<List<TrackAPI>>(emptyList())
    val playbackQueue = _playbackQueue.asStateFlow()

    // ★追加：現在のアルバムアートを保持する
    private val _currentTrackImage = MutableStateFlow<Bitmap?>(null)
    val currentTrackImage = _currentTrackImage.asStateFlow()

    //
    private val _playlists = MutableStateFlow<List<Playlist>>(emptyList())
    val playlists = _playlists.asStateFlow()

    private val _isLoading = MutableStateFlow<Boolean>(false)
    val isLoading = _isLoading.asStateFlow()

    private val _isClassifying = MutableStateFlow(false)
    val isClassifying = _isClassifying.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error = _error.asStateFlow()
    // --- App Remote SDKの接続フロー ---

    /**
     * App Remoteに接続するための認証を開始します (TOKENフロー)
     * UIからこの関数を呼び出して、結果をhandleAppRemoteAuthResponseに渡します。
     */
    fun connectToAppRemote(context: Context, launcher: ActivityResultLauncher<Intent>) {
        val request = AuthorizationRequest.Builder(
            CLIENT_ID,
            AuthorizationResponse.Type.TOKEN, // App Remote接続にはTOKENタイプが必須
            REDIRECT_URI
        ).setScopes(arrayOf("app-remote-control", "user-read-playback-state"))
            .build()
        val intent = AuthorizationClient.createLoginActivityIntent(context as Activity, request)
        launcher.launch(intent)
    }

    /**
     * App Remote認証のレスポンスを処理します
     */
    fun handleAppRemoteAuthResponse(response: AuthorizationResponse, context: Context) {
        if (response.type == AuthorizationResponse.Type.TOKEN) {
            val connectionParams = ConnectionParams.Builder(CLIENT_ID)
                .setRedirectUri(REDIRECT_URI)
                .showAuthView(false)
                .build()

            SpotifyAppRemote.connect(context, connectionParams, object : Connector.ConnectionListener {
                override fun onConnected(remote: SpotifyAppRemote) {
                    _appRemote.value = remote
                    subscribeToPlayerState(remote)
                    Log.d("SpotifyViewModel", "Connected to App Remote!")
                }
                override fun onFailure(throwable: Throwable) {
                    Log.e("SpotifyViewModel", "Could not connect to App Remote: ${throwable.message}")
                }
            })
        } else if (response.type == AuthorizationResponse.Type.ERROR) {
            Log.e("SpotifyViewModel", "App Remote Auth Error: ${response.error}")
        }
    }

    // --- バックエンド連携の認証フロー ---

    /**
     * バックエンド経由でトークンを取得するための認証を開始します (CODEフロー)
     * UIからこの関数を呼び出して、結果をhandleBackendAuthResponseに渡します。
     */
    fun authenticateWithBackend(context: Context, launcher: ActivityResultLauncher<Intent>) {
        val request = AuthorizationRequest.Builder(
            CLIENT_ID,
            AuthorizationResponse.Type.CODE, // バックエンド連携にはCODEタイプが必須
            REDIRECT_URI
        ).setScopes(arrayOf("user-read-private", "playlist-read-private")) // Web APIで使いたい権限
            .build()
        val intent = AuthorizationClient.createLoginActivityIntent(context as Activity, request)
        launcher.launch(intent)
    }

    /**
     * バックエンド認証のレスポンス（認証コード）を処理します
     */
    fun handleBackendAuthResponse(response: AuthorizationResponse) {
        if (response.type == AuthorizationResponse.Type.CODE) {
            viewModelScope.launch {
                try {
                    val apiResponse = backendApiService.getAccessToken(response.code)
                    if (apiResponse.isSuccessful && apiResponse.body() != null) {
                        _accessToken.value = apiResponse.body()!!.accessToken
                        Log.d("SpotifyViewModel", "Access Token from backend is ready!")
                    } else {
                        Log.e("SpotifyViewModel", "Backend API Error: ${apiResponse.errorBody()?.string()}")
                    }
                } catch (e: Exception) {
                    Log.e("SpotifyViewModel", "Failed to get token from backend", e)
                }
            }
        } else if (response.type == AuthorizationResponse.Type.ERROR) {
            Log.e("SpotifyViewModel", "Backend Auth Error: ${response.error}")
        }
    }

    suspend fun setJwt() {
        val jwt = repository.getJwt()
        Log.d(TAG,"setJwt.jwt:${jwt}")
        _jwt.value = jwt
    }

    fun setLoading(isLoading: Boolean) {
        _isLoading.value = isLoading
    }

    fun setClassifying(isProcessing: Boolean) {
        _isClassifying.value = isProcessing
    }
    // --- Web APIを使った再生コントロール ---

    /**
     * トラックIDのリストを受け取り、再生を開始する
     */
    // --- 共通のヘルパー関数と再生コントロール ---

    private fun subscribeToPlayerState(remote: SpotifyAppRemote) {
        remote.playerApi.subscribeToPlayerState().setEventCallback { playerState ->
            // PlayerState全体を更新
            _playerState.value = playerState
            // トラック情報を更新
            _currentTrack.value = playerState.track
            // トラックのimageUriを使って画像を取得
            playerState.track?.imageUri?.let {
                remote.imagesApi.getImage(it).setResultCallback { bitmap ->
                    _currentTrackImage.value = bitmap
                }
            }
//            playerState.track?.imageUri?.let {
//                // 画像が現在のものと違う場合のみ取得
//                if (it.id != _currentTrack.value?.imageUri?.id) {
//                    remote.imagesApi.getImage(it).setResultCallback { bitmap ->
//                        _currentTrackImage.value = bitmap
//                    }
//                }
//            }
        }
    }

    fun classify() {
        Log.d(TAG,"classify")
        viewModelScope.launch {
            val token = _jwt.value // ★accessTokenからjwtに変更
            if (token == null) {
                Log.e(TAG, "JWT is not available.")
                return@launch
            }
            val authHeader = "Bearer $token"
            _isLoading.value = true
            setClassifying(true)
            try {
                val playlistIds: List<String> = _playlists.value.map { it.playlistId }
                Log.d(TAG, "Playlist IDs: $playlistIds")
                val response = backendApiServiceAI.doClassify(authHeader,playlistIds)
                Log.d(TAG,"response:${response.isSuccessful}")
                if (!response.isSuccessful) {
                    _error.value = "Classify failed: ${response.code()}"
                }
            } catch (e: Exception) {
                _error.value = "Error: ${e.message}"
            } finally {
                _isLoading.value = false
                setClassifying(false)
            }
        }
    }

    suspend fun fetchEmotionPlaylist(
        beforeEmotion: SendEmotion,
        afterEmotion: SendEmotion,
        chosenPlaylists: List<String>
    ) {
        Log.d(TAG,"fetchEmotionPlaylist")
            // 1. JWTの準備
            val token = _jwt.value // ★accessTokenからjwtに変更
            Log.d(TAG,"fetchE.token:${token}" )
            if (token == null) {
                Log.e("SpotifyViewModel", "JWT is not available.")
                return
            }
            // Bearerプレフィックスは通常、ヘッダーに含めます
            val authHeader = "Bearer $token"

            // 2. 引数の準備
            val beforeEmotionStr = beforeEmotion.name
            val afterEmotionStr = afterEmotion.name
            _isLoading.value = true

            try {
                val response = backendApiService.getEmotionPlaylist(
                    token = authHeader,
                    before_emotion = beforeEmotionStr,
                    after_emotion = afterEmotionStr,
                    chosen_playlists = chosenPlaylists
                )
                if (response.isSuccessful) {
                    val tracks = response.body()?.data ?: emptyList()
                    Log.d(TAG, "Successfully fetched ${tracks.size} tracks.")
                    Log.d(TAG,"tracks:${tracks}")
                    _playbackQueue.value = tracks
                } else {
                    val errorBody = response.errorBody()?.string()
                    _error.value = "Playlist fetch failed: ${response.code()}"
                    Log.e(TAG, "API Error: ${response.code()} $errorBody")
                }
            } catch (e: Exception) {
                _error.value = "Error: ${e.message}"
                Log.e(TAG, "Network request failed", e)
            }
            finally {
                _isLoading.value = false

        }
    }

    suspend fun fetchPlaylistList() {
        Log.d(TAG,"fetchPlaylistList")
        val token = _jwt.value
        Log.d(TAG,"fetchPlaylistList.jwt:${token}")
        if (token == null) {
            Log.e("SpotifyViewModel", "JWT is not available.")
            return
        }
        val authHeader = "Bearer $token"
        _isLoading.value = true
        try {
            val response = backendApiService.getPlaylistList(authHeader)
            if (response.isSuccessful) {
                val playlists = response.body()?.data ?: emptyList()
                val json = Gson().toJson(playlists)
                Log.d(TAG, "全プレイリストJSON: $json")
                _playlists.value = playlists
                truePlaylistAll()
            } else {
                _error.value = "Playlist fetch failed: ${response.code()}"
                Log.e("SpotifyViewModel", "fetchPlaylist error ${response.code()}.")
            }
        } catch (e: Exception) {
            _error.value = "Error: ${e.message}"
        } finally {
            _isLoading.value = false
        }
    }

    fun play(uri: String) {
        _appRemote.value?.playerApi?.play(uri)
    }

    fun pause() {
        _appRemote.value?.playerApi?.pause()
    }

    fun resume() {
        _appRemote.value?.playerApi?.resume()
    }

    // ★追加：再生位置を変更する
    fun seekTo(position: Long) {
        _appRemote.value?.playerApi?.seekTo(position)
    }

    // ★追加：次の曲へ
    fun skipNext() {
//        _appRemote.value?.playerApi?.skipNext()
        val currentTrackUri = _playerState.value?.track?.uri
        if (currentTrackUri != null) {
            val currentIndex = _playbackQueue.value.indexOfFirst { "spotify:track:${it.trackId}" == currentTrackUri }
            if (currentIndex != -1 && currentIndex < _playbackQueue.value.size - 1) {
                val nextTrack = _playbackQueue.value[currentIndex + 1]
                play("spotify:track:${nextTrack.trackId}")
            }
        }
    }

    // ★追加：前の曲へ
    fun skipPrevious() {
//        _appRemote.value?.playerApi?.skipPrevious()
        val currentTrackUri = _playerState.value?.track?.uri
        if (currentTrackUri != null) {
            val currentIndex = _playbackQueue.value.indexOfFirst { "spotify:track:${it.trackId}" == currentTrackUri }
            if (currentIndex > 0) {
                val previousTrack = _playbackQueue.value[currentIndex - 1]
                play("spotify:track:${previousTrack.trackId}")
            }
        }
    }

    fun disconnect() {
        _appRemote.value?.let { SpotifyAppRemote.disconnect(it) }
        _appRemote.value = null
        _accessToken.value = null // バックエンドのトークンもクリア
        _currentTrackImage.value = null

    }

    fun loadPlaylists() {
        // viewModelScopeでコルーチンを開始
        Log.d(TAG,"loadPlaylists")
        viewModelScope.launch {
            fetchPlaylistList()
            classify()
        }
    }


    private fun abstractionChosenPlaylists(): List<String> {
        val activePlaylistIds = _playlists.value.filter { it.isActive }.map { it.playlistId }
        return activePlaylistIds
    }

    fun loadQueue(firstEmotion :SendEmotion, currentEmotion: SendEmotion) {
        viewModelScope.launch {
            Log.d(TAG,"LoadQueue")
            val chosenPlaylists = abstractionChosenPlaylists()
            Log.d(TAG,"loadQueue.chosenPlaylists:${chosenPlaylists}")

            fetchEmotionPlaylist(
                firstEmotion,
                currentEmotion,
                chosenPlaylists
            )            // 今回はダミーデータを表示

            //_playbackQueue.value = dummyTrackLists
            if (_playbackQueue.value.isNotEmpty()) {
                play("spotify:track:${_playbackQueue.value[0].trackId}")
            } else {
                Log.w(TAG, "Playback queue is empty, nothing to play.")
            }
        }
    }

    /**
     * プレイリストの選択状態をトグルする
     * @param playlistId トグル対象のプレイリストID
     */
    fun togglePlaylistSelection(playlistId: String) {
        _playlists.update { currentPlaylists ->
            currentPlaylists.map { playlist ->
                if (playlist.playlistId == playlistId) {
                    // isActivateの状態を反転させた新しいインスタンスを返す
                    playlist.copy(isActive = !playlist.isActive)
                } else {
                    playlist
                }
            }
        }
    }

    fun truePlaylistAll() {
        _playlists.update { currentPlaylists ->
            currentPlaylists.map { playlist ->
                playlist.copy(isActive = true)
            }
        }
    }
    fun falsePlaylistAll() {
        _playlists.update { currentPlaylists ->
            currentPlaylists.map { playlist ->
                playlist.copy(isActive = false)
            }
        }
    }
    override fun onCleared() {
        super.onCleared()
        disconnect()
    }

    private val dummyTrackLists = listOf(
        TrackAPI(
            trackId = "0Ns63lt28epRgED3Tnhmth",
            imageName = "https://i.scdn.co/image/ab67616d0000b27357a4e5830ef3e0aeee2874ce",
            artistName = "ARASHI",
            trackName = "Happiness"
        ),
        TrackAPI(
            trackId = "1kdGYCHCff09E2FASM5IVY",
            imageName = "https://i.scdn.co/image/ab67616d0000b2738ac80cfc486397adceeaf15a",
            artistName = "ARASHI",
            trackName = "A・RA・SHI"
        ),
        TrackAPI(
            trackId = "0aaZG5azeJei81A2WptwC8",
            imageName = "https://i.scdn.co/image/ab67616d0000b273302dfd429f8d589a7ae2c3af",
            artistName = "Hump Back",
            trackName = "拝啓、少年よ"
        ),
        TrackAPI(
            trackId = "10Eyo4juZQFthKqlJgGMdp",
            imageName = "https://i.scdn.co/image/ab67616d0000b273ae51734d04ef431b65a09a9a",
            artistName = "back number",
            trackName = "怪盗"
        ),
        TrackAPI(
            trackId = "0Ns63lt28epRgED3Tnhmth",
            imageName = "https://i.scdn.co/image/ab67616d0000b27357a4e5830ef3e0aeee2874ce",
            artistName = "ARASHI",
            trackName = "Happiness"
        ),
        TrackAPI(
            trackId = "1kdGYCHCff09E2FASM5IVY",
            imageName = "https://i.scdn.co/image/ab67616d0000b2738ac80cfc486397adceeaf15a",
            artistName = "ARASHI",
            trackName = "A・RA・SHI"
        ),
        TrackAPI(
            trackId = "0aaZG5azeJei81A2WptwC8",
            imageName = "https://i.scdn.co/image/ab67616d0000b273302dfd429f8d589a7ae2c3af",
            artistName = "Hump Back",
            trackName = "拝啓、少年よ"
        ),
        TrackAPI(
            trackId = "10Eyo4juZQFthKqlJgGMdp",
            imageName = "https://i.scdn.co/image/ab67616d0000b273ae51734d04ef431b65a09a9a",
            artistName = "back number",
            trackName = "怪盗"
        ),
        TrackAPI(
            trackId = "0Ns63lt28epRgED3Tnhmth",
            imageName = "https://i.scdn.co/image/ab67616d0000b27357a4e5830ef3e0aeee2874ce",
            artistName = "ARASHI",
            trackName = "Happiness"
        ),
        TrackAPI(
            trackId = "1kdGYCHCff09E2FASM5IVY",
            imageName = "https://i.scdn.co/image/ab67616d0000b2738ac80cfc486397adceeaf15a",
            artistName = "ARASHI",
            trackName = "A・RA・SHI"
        ),
        TrackAPI(
            trackId = "0aaZG5azeJei81A2WptwC8",
            imageName = "https://i.scdn.co/image/ab67616d0000b273302dfd429f8d589a7ae2c3af",
            artistName = "Hump Back",
            trackName = "拝啓、少年よ"
        ),
        TrackAPI(
            trackId = "10Eyo4juZQFthKqlJgGMdp",
            imageName = "https://i.scdn.co/image/ab67616d0000b273ae51734d04ef431b65a09a9a",
            artistName = "back number",
            trackName = "怪盗"
        ),
        TrackAPI(
            trackId = "0Ns63lt28epRgED3Tnhmth",
            imageName = "https://i.scdn.co/image/ab67616d0000b27357a4e5830ef3e0aeee2874ce",
            artistName = "ARASHI",
            trackName = "Happiness"
        ),
        TrackAPI(
            trackId = "1kdGYCHCff09E2FASM5IVY",
            imageName = "https://i.scdn.co/image/ab67616d0000b2738ac80cfc486397adceeaf15a",
            artistName = "ARASHI",
            trackName = "A・RA・SHI"
        ),
        TrackAPI(
            trackId = "0aaZG5azeJei81A2WptwC8",
            imageName = "https://i.scdn.co/image/ab67616d0000b273302dfd429f8d589a7ae2c3af",
            artistName = "Hump Back",
            trackName = "拝啓、少年よ"
        ),
        TrackAPI(
            trackId = "10Eyo4juZQFthKqlJgGMdp",
            imageName = "https://i.scdn.co/image/ab67616d0000b273ae51734d04ef431b65a09a9a",
            artistName = "back number",
            trackName = "怪盗"
        )
    )

    // プレイリストのダミーデータ
    private val dummyPlaylists = listOf(
        Playlist(
            playlistId = "75kV4GQqqjaxNSLImhDPyC",
//            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e0257a4e5830ef3e0aeee2874ceab67616d00001e028ac80cfc486397adceeaf15aab67616d00001e029cbe133c32610c326ec72a53ab67616d00001e02bf24352caf35d83d05519573",
            imageUrl = "https://i.scdn.co/image/ab67616d0000b27387d3260cd0a28a2f42d5d29e",
            playlistName = "melosync"
        ),
        Playlist(
            playlistId = "3OKozqqZdZojBJC85nQMOj",
//            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e0257a4e5830ef3e0aeee2874ceab67616d00001e028ac80cfc486397adceeaf15aab67616d00001e029cbe133c32610c326ec72a53ab67616d00001e02bf24352caf35d83d05519573",
//            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e020d0ebed90b54dc171c4b45d9ab67616d00001e02bf7c8b0d4f1eee0674561d87ab67616d00001e02c1b23fe0879585e9504168d7ab67616d00001e02f7ba0909eb3c7e47f6773944",
            imageUrl = "https://i.scdn.co/image/ab67616d0000b273ae51734d04ef431b65a09a9a",
            playlistName = "meloSync"
        ),
        Playlist(
            playlistId = "1NqZGxfmtJYwwIg7BsImil",
            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e022182bcbffb38e1195f896a90ab67616d00001e022d41c4dbcfb172ba5c992a3cab67616d00001e0264be01336a8f917538a60b74ab67616d00001e02ee9ddd9ff22b6ea5458b8f29",
            playlistName = "RUSH BALL 2024"
        ),
        Playlist(
            playlistId = "66ISSxGFVWjYoDUE7YZkJT",
            imageUrl = "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000da84229519873e5353486b72f1c8",
            playlistName = "METROCK大阪~2023.day1"
        ),
        Playlist(
            playlistId = "4GzK5dvJgDLq8XrBaguZsC",
            imageUrl = "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000d72ca806555973eea7db13b4c7fd",
            playlistName = "cell,core 2022"
        ),
        Playlist(
            playlistId = "1:75kV4GQqqjaxNSLImhDPyC",
            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e0257a4e5830ef3e0aeee2874ceab67616d00001e028ac80cfc486397adceeaf15aab67616d00001e029cbe133c32610c326ec72a53ab67616d00001e02bf24352caf35d83d05519573",
            playlistName = "melosync"
        ),
        Playlist(
            playlistId = "1:3OKozqqZdZojBJC85nQMOj",
            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e020d0ebed90b54dc171c4b45d9ab67616d00001e02bf7c8b0d4f1eee0674561d87ab67616d00001e02c1b23fe0879585e9504168d7ab67616d00001e02f7ba0909eb3c7e47f6773944",
            playlistName = "meloSync"
        ),
        Playlist(
            playlistId = "1:1NqZGxfmtJYwwIg7BsImil",
            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e022182bcbffb38e1195f896a90ab67616d00001e022d41c4dbcfb172ba5c992a3cab67616d00001e0264be01336a8f917538a60b74ab67616d00001e02ee9ddd9ff22b6ea5458b8f29",
            playlistName = "RUSH BALL 2024"
        ),
        Playlist(
            playlistId = "1:66ISSxGFVWjYoDUE7YZkJT",
            imageUrl = "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000da84229519873e5353486b72f1c8",
            playlistName = "METROCK大阪~2023.day1"
        ),
        Playlist(
            playlistId = "1:4GzK5dvJgDLq8XrBaguZsC",
            imageUrl = "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000d72ca806555973eea7db13b4c7fd",
            playlistName = "cell,core 2022"
        ),
        Playlist(
            playlistId = "2:75kV4GQqqjaxNSLImhDPyC",
            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e0257a4e5830ef3e0aeee2874ceab67616d00001e028ac80cfc486397adceeaf15aab67616d00001e029cbe133c32610c326ec72a53ab67616d00001e02bf24352caf35d83d05519573",
            playlistName = "melosync"
        ),
        Playlist(
            playlistId = "2:3OKozqqZdZojBJC85nQMOj",
            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e020d0ebed90b54dc171c4b45d9ab67616d00001e02bf7c8b0d4f1eee0674561d87ab67616d00001e02c1b23fe0879585e9504168d7ab67616d00001e02f7ba0909eb3c7e47f6773944",
            playlistName = "meloSync"
        ),
        Playlist(
            playlistId = "2:1NqZGxfmtJYwwIg7BsImil",
            imageUrl = "https://mosaic.scdn.co/640/ab67616d00001e022182bcbffb38e1195f896a90ab67616d00001e022d41c4dbcfb172ba5c992a3cab67616d00001e0264be01336a8f917538a60b74ab67616d00001e02ee9ddd9ff22b6ea5458b8f29",
            playlistName = "RUSH BALL 2024"
        ),
        Playlist(
            playlistId = "2:66ISSxGFVWjYoDUE7YZkJT",
            imageUrl = "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000da84229519873e5353486b72f1c8",
            playlistName = "METROCK大阪~2023.day1"
        ),
        Playlist(
            playlistId = "2:4GzK5dvJgDLq8XrBaguZsC",
            imageUrl = "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000d72ca806555973eea7db13b4c7fd",
            playlistName = "cell,core 2022"
        )
    )
}
