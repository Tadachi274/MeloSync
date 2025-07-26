package com.example.melosync

import com.google.android.gms.wearable.MessageClient
import com.google.android.gms.wearable.MessageEvent

class PhoneHeartRateReceiver(
    private val onHeartRateReceived: (Double) -> Unit
) : MessageClient.OnMessageReceivedListener {

    override fun onMessageReceived(event: MessageEvent) {
        if (event.path == "/heartrate") {
            val bpmString = event.data.toString(Charsets.UTF_8)
            val bpm = bpmString.toDoubleOrNull() ?: return
            onHeartRateReceived(bpm)
        }
    }
}