package com.example.melosync

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

class SendHeartRateToServer {
    private val client = OkHttpClient()
    private val TAG = "HeartRateApiSender"

    suspend fun sendHeartRateToFastApi(bpm: Double) {
        withContext(Dispatchers.IO) {
            try {
                val json = "{\"bpm\": $bpm}"
                val requestBody = json.toRequestBody("application/json".toMediaTypeOrNull())

                val request = Request.Builder()
                    .url("http://192.168.11.3:5000/heartrate") // change to your ip
                    .post(requestBody)
                    .build()

                client.newCall(request).execute().use { response ->
                    if (!response.isSuccessful) {
                        Log.e(TAG, "Unexpected code $response")
                    } else {
                        Log.d(TAG, "Sent heart rate successfully: $bpm")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to send heart rate", e)
            }
        }
    }
}