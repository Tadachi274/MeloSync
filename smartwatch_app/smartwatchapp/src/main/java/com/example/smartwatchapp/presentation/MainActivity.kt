package com.example.smartwatchapp.presentation

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.wear.compose.material.Text
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.example.smartwatchapp.presentation.HealthServiceManager

class MainActivity : ComponentActivity() {

    private lateinit var healthServiceManager: HealthServiceManager

    override fun onCreate(savedInstanceState: Bundle?) {
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
