package com.example.melosync

import android.content.Context
import android.util.Log
import com.google.android.gms.wearable.Wearable
import kotlinx.coroutines.tasks.await

class HeartRateSender(private val context: Context) {

    private val messageClient = Wearable.getMessageClient(context)

    suspend fun sendHeartRateToPhone(bpm: Double) {
        Log.d("WearDataSender", "Preparing to send bpm: $bpm")
        val nodeId = getPairedNodeId()
        if (nodeId == null) {
            Log.e("WearDataSender", "No connected node found.")
            return
        }

        val messagePath = "/heartrate"
        val payload = bpm.toString().toByteArray()

        val testPayload = "hello".toByteArray()
        Wearable.getMessageClient(context).sendMessage(nodeId, "/test", testPayload).await()

        try {
            Wearable.getMessageClient(context).sendMessage(nodeId, messagePath, payload).await()
            Log.d("WearDataSender", "Heart rate sent to phone")
        } catch(e: Exception) {
            Log.e("WearDataSender", "Failed to send heart rate", e)
        }
    }

    suspend fun getPairedNodeId(): String? {
        val nodes = Wearable.getNodeClient(context).connectedNodes.await()
        Log.d("WearDataSender", "Connected nodes count: ${nodes.size}")
        nodes.forEach {
            Log.d("WearDataSender", "Node found: ${it.displayName}, id: ${it.id}")
        }
        return nodes.firstOrNull()?.id
    }
}