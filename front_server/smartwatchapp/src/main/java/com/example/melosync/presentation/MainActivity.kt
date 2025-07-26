package com.example.melosync

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.wear.compose.material.Text
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import android.util.Log
import kotlinx.coroutines.tasks.await
import com.google.android.gms.wearable.Wearable

class MainActivity : ComponentActivity() {

    private lateinit var healthServiceManager: HealthServiceManager

    override fun onCreate(savedInstanceState: Bundle?) {
        CoroutineScope(Dispatchers.IO).launch {
            val nodes = Wearable.getNodeClient(this@MainActivity).connectedNodes.await()
            Log.d("MainActivity", "Connected nodes count: ${nodes.size}")
            nodes.forEach {
                Log.d("MainActivity", "Node found: ${it.displayName}, id: ${it.id}")
            }
        }
        super.onCreate(savedInstanceState)

        // 初始化 permission launcher
        val permissionLauncher = registerForActivityResult(
            ActivityResultContracts.RequestPermission()
        ) { granted ->
            if (granted) {
                healthServiceManager.startHeartRateMonitoring()
            }
        }

        // 初始化 HealthServiceManager
        healthServiceManager = HealthServiceManager(this, permissionLauncher)
        healthServiceManager.checkPermissionAndStart()

        // UI
        setContent {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text(text = "Hello Wear OS")
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        healthServiceManager.stopHeartRateMonitoring()
    }
}