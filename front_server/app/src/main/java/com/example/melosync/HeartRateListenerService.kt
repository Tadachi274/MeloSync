package com.example.melosync

import android.util.Log
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.WearableListenerService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class HeartRateListenerService : WearableListenerService() {

    private val apiService = ApiClient.apiService

    override fun onMessageReceived(messageEvent: MessageEvent) {
        Log.d("HeartRateListener", "onMessageReceived called")
        Log.d("HeartRateListener", "Received message path: ${messageEvent.path}")

        if (messageEvent.path == "/test") {
            val data = messageEvent.data.toString(Charsets.UTF_8)
            Log.d("HeartRateListener", "Test message received: $data")
        }

        super.onMessageReceived(messageEvent)

        Log.d("HeartRateListener", "Received message path: ${messageEvent.path}")

        if (messageEvent.path == "/heartrate") {
            val bpmString = messageEvent.data.toString(Charsets.UTF_8)
            val bpm = bpmString.toDoubleOrNull() ?: return

            Log.d("HeartRateListener", "Received bpm: $bpm")

            postHeartRate(bpm.toInt())
        }
    }

    private fun postHeartRate(hr: Int) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val response = apiService.sendHeartRate(HeartRate(hr))
                if (response.isSuccessful) {
                    val responseBody = response.body()
                    Log.d("HeartRateListener", "Status: ${responseBody?.status}, HeartRate: ${responseBody?.data?.heartrate}")
                } else {
                    Log.e("HeartRateListener", "Error: ${response.errorBody()?.string()}")
                }
            } catch (e: Exception) {
                Log.e("HeartRateListener", "例外錯誤: ${e.message}")
            }
        }
    }
}