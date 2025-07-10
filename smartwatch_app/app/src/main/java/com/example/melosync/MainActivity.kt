package com.example.melosync

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.example.melosync.ui.theme.MeloSyncTheme
import kotlinx.coroutines.*
import retrofit2.Response
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import android.util.Log
import com.google.android.gms.wearable.MessageClient
import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.Wearable
import com.example.melosync.PhoneHeartRateReceiver
import com.example.melosync.HeartRateListenerService

class MainActivity : ComponentActivity() {
    private val apiService = ApiClient.apiService
    private lateinit var phoneHeartRateReceiver: PhoneHeartRateReceiver
    private var logMessage by mutableStateOf("尚未傳送")

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()


        setContent {
            MeloSyncTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Column(
                        modifier = Modifier
                            .padding(innerPadding)
                            .fillMaxSize(),
                        verticalArrangement = Arrangement.Center,
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Greeting(
                            name = "Android",
                            modifier = Modifier.padding(bottom = 16.dp)
                        )
                    }
                }
            }
        }
    }
    private fun postHeartRate(hr: Int) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val response = apiService.sendHeartRate(HeartRate(hr))
                if (response.isSuccessful) {
                    val responseBody = response.body()
                    Log.d("MainActivity", "Status: ${responseBody?.status}, HeartRate: ${responseBody?.data?.heartrate}")
                } else {
                    Log.e("MainActivity", "Error: ${response.errorBody()?.string()}")
                }
            } catch (e: Exception) {
                Log.e("MainActivity", "例外錯誤: ${e.message}")
            }
        }
    }
}



@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    MeloSyncTheme {
        Greeting("Android")
    }
}

