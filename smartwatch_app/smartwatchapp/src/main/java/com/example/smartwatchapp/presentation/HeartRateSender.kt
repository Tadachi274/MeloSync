package com.example.smartwatchapp.presentation

import android.content.Context
import android.util.Log
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.MessageClient
import com.google.android.gms.wearable.NodeClient
import com.google.android.gms.wearable.Wearable
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.tasks.await

class HeartRateSender(private val context: Context) {

    private val messageClient = Wearable.getMessageClient(context)

    suspend fun sendHeartRateToPhone(bpm: Double) {
        val nodeId = getPairedNodeId() ?: return

        val messagePath = "/heartrate"
        val payload = bpm.toString().toByteArray()

        try {
            Wearable.getMessageClient(context).sendMessage(nodeId, messagePath, payload).await()
            Log.d("WearDataSender", "Heart rate sent to phone")
        } catch(e: Exception) {
            Log.e("WearDataSender", "Failed to send heart rate", e)
        }
    }

    suspend fun getPairedNodeId(): String? {
        val nodes = Wearable.getNodeClient(context).connectedNodes.await()
        return nodes.firstOrNull()?.id
    }
}
