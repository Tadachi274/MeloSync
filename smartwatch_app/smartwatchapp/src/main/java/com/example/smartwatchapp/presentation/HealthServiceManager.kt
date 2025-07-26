package com.example.smartwatchapp.presentation

import android.Manifest
import android.content.Context
import android.util.Log
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.health.services.client.HealthServices
import androidx.health.services.client.MeasureCallback
import androidx.health.services.client.data.DataPointContainer
import androidx.health.services.client.data.DataType
import androidx.health.services.client.data.DeltaDataType
import androidx.lifecycle.LifecycleOwner
import com.example.smartwatchapp.presentation.HeartRateSender
import com.example.smartwatchapp.presentation.SendHeartRateToServer
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class HealthServiceManager(
    private val context: Context,
    private val permissionLauncher: ActivityResultLauncher<String>
) {
    private val heartRateSender: HeartRateSender by lazy { HeartRateSender(context) }
    private val sendHeartRateToServer by lazy { SendHeartRateToServer() }

    private val TAG = "HeartRateWear"

    private val scope = CoroutineScope(Dispatchers.IO)

    private val measureClient by lazy {
        HealthServices.getClient(context).measureClient
    }

    private val heartRateCallback = object : MeasureCallback {
        override fun onAvailabilityChanged(dataType: DeltaDataType<*, *>, availability: androidx.health.services.client.data.Availability) {
            Log.d(TAG, "Availability changed: $dataType -> $availability")
        }

        override fun onDataReceived(data: DataPointContainer) {
            val heartRatePoints = data.getData(DataType.HEART_RATE_BPM)
            val bpm = heartRatePoints.firstOrNull()?.value ?: return
            Log.d(TAG, "Heart rate: $bpm")

            sendHeartRateToServer(bpm)
        }
    }

    fun checkPermissionAndStart() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.BODY_SENSORS)
            == android.content.pm.PackageManager.PERMISSION_GRANTED) {
            startHeartRateMonitoring()
        } else {
            permissionLauncher.launch(Manifest.permission.BODY_SENSORS)
        }
    }

    fun startHeartRateMonitoring() {
        measureClient.registerMeasureCallback(DataType.HEART_RATE_BPM, heartRateCallback)
        Log.d(TAG, "Started heart rate monitoring")
    }

    fun stopHeartRateMonitoring() {
        measureClient.unregisterMeasureCallbackAsync(DataType.HEART_RATE_BPM, heartRateCallback)
            .addListener(
                { Log.d(TAG, "Stopped heart rate monitoring") },
                ContextCompat.getMainExecutor(context)
            )
    }

    private fun sendHeartRateToServer(bpm: Double) {
        scope.launch {
            sendHeartRateToServer.sendHeartRateToFastApi(bpm)
        }
    }
}
