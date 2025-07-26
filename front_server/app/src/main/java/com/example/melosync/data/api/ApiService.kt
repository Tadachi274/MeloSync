package com.example.melosync.data.api

import com.google.gson.annotations.SerializedName
import retrofit2.Response
import retrofit2.http.*

/**
 * バックエンドおよびSpotify Web APIとの通信を定義するRetrofitインターフェース
 */
interface ApiService {

    // --- バックエンドとの通信 ---

    @FormUrlEncoded
    @POST("api/spotify/token")
    suspend fun getAccessToken(
        @Field("code") code: String
    ): Response<TokenResponse>

    /**
     * (1) doClassify: ボディなし、返り値なし
     * ヘッダーにJWTを付与してPOSTリクエストを送信します。
     */
    @POST("api/classify")
    suspend fun doClassify(
        @Header("Authorization") token: String
    ): Response<Unit> // 返り値がない場合はUnitを指定

    /**
     * (2) getEmotionPlaylist: フォーム形式のボディ、返り値あり
     * ヘッダーにJWTを付与し、リクエストボディをフォーム形式で送信します。
     */
    @FormUrlEncoded
    @POST("api/playlist/emotion")
    suspend fun getEmotionPlaylist(
        @Header("Authorization") token: String,
        @Field("before_emotion") before_emotion: String,
        @Field("after_emotion") after_emotion: String,
        @Field("chosen_playlists") chosen_playlists: List<String> // List<String>として送信
    ): Response<EmotionPlaylistResponse>

    /**
     * (3) getPlaylistList: ボディなし、返り値あり
     * ヘッダーにJWTを付与してPOSTリクエストを送信します。
     */
    @POST("api/playlist")
    suspend fun getPlaylistList(
        @Header("Authorization") token: String
    ): Response<PlaylistListResponse>

//    /**
//     * (4) getAccessToken: ボディなし、返り値なし
//     * ヘッダーにJWTを付与してGETリクエストを送信します。
//     */
//    @GET("api/token")
//    suspend fun getAccessToken(
//        @Header("Authorization") token: String
//    ): Response<Unit> // 返り値がない場合はUnitを指定


    @POST("api/playlist/recommend")
    suspend fun getRecommendedPlaylist(
        @Body emotionRequest: EmotionRequest
    ): Response<PlaylistResponse>



    // --- Spotify Web APIとの通信 ---

    /**
     * 使うデバイスを指定する
     */
    @GET("v1/me/player/devices")
    suspend fun getAvailableDevices(
        @Header("Authorization") token: String
    ): Response<DeviceListResponse>
    /**
     * 指定したトラックを再生する
     */
    @PUT("v1/me/player/play")
    suspend fun startOrResumePlayback(
        @Header("Authorization") token: String,
        @Body request: PlayRequest
    ): Response<Unit>

    /**
     * 再生キューの末尾にトラックを追加する
     */
    @POST("v1/me/player/queue")
    suspend fun addToQueue(
        @Header("Authorization") token: String,
        @Query("uri") trackUri: String
    ): Response<Unit>
    /**
     * 現在再生中のトラック情報を取得
     */
    @GET("v1/me/player/currently-playing")
    suspend fun getCurrentPlayback(
        @Header("Authorization") token: String
    ): Response<CurrentlyPlayingContext>

    /**
     * 一時停止する
     */
    @PUT("v1/me/player/pause")
    suspend fun pausePlayback(
        @Header("Authorization") token: String
    ): Response<Unit>

    /**
     * 再生をスキップする（次の曲へ）
     */
    @POST("v1/me/player/next")
    suspend fun skipToNext(
        @Header("Authorization") token: String
    ): Response<Unit>
    /**
     * 一時停止後の再生
     */
    @PUT("v1/me/player/play")
    suspend fun resumePlayback(
        @Header("Authorization") token: String
    ): Response<Unit>
}

data class EmotionRequest(
    val emotion: String
)

// (2) getEmotionPlaylistのレスポンス用
data class EmotionPlaylistResponse(
    val data: List<TrackAPI>
)

data class TrackAPI(
    @SerializedName("track_id")
    val trackId: String,

    @SerializedName("track_name")
    val trackName: String,

    @SerializedName("artist_name")
    val artistName: String,

    @SerializedName("image_url")
    val imageName: String
)

// (3) getPlaylistのレスポンス用
data class PlaylistListResponse(
    val data: List<Playlist>
)

data class Playlist(
    @SerializedName("playlist_id")
    val playlistId: String,

    @SerializedName("playlist_name")
    val playlistName: String,

    @SerializedName("image_url") // JSONのキーが "image_name" の場合は "image_name" に修正してください
    val imageUrl: String,

    var isActive: Boolean = true
)

data class TokenResponse(
    val accessToken: String
)

data class PlayRequest(
    val uris: List<String>, // 例: ["spotify:track:xxxx", ...]
    val position_ms: Int? = null // オプション: 再生位置（ミリ秒単位）
)

data class PlaylistResponse(
    val tracks: List<TrackObject>
)

data class CurrentlyPlayingContext(
    val item: TrackObject?,         // 再生中のトラック情報
    val is_playing: Boolean         // 再生中かどうか
)

data class TrackObject(
    val trackId: String,
    val name: String,
    val artists: List<ArtistObject>,
    val album: AlbumObject
)

data class ArtistObject(
    val name: String
)

data class AlbumObject(
    val images: List<ImageObject>
)

data class ImageObject(
    val url: String
)

//デバイス探す用
data class DeviceListResponse(
    val devices: List<DeviceObject>
)

data class DeviceObject(
    val id: String,
    val is_active: Boolean,
    val name: String,
    val type: String,
    val volume_percent: Int
)
