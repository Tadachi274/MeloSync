package com.example.melosync

// Android Framework
import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log

// AndroidX (Jetpack)
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

// App-specific packages
import com.example.melosync.navigation.AppNavigation
import com.example.melosync.ui.theme.AppBackground
import com.example.melosync.ui.theme.MeloSyncTheme

// Coroutines
import kotlinx.coroutines.*

class MainActivity : ComponentActivity() {
    private val apiService = ApiClient.apiService
    private lateinit var phoneHeartRateReceiver: PhoneHeartRateReceiver
    private var logMessage by mutableStateOf("尚未傳送")

    override fun onCreate(savedInstanceState: Bundle?) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT)
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                arrayOf(Manifest.permission.BLUETOOTH_CONNECT), REQUEST_CODE_BLUETOOTH)
        }
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MeloSyncTheme {
                AppBackground {


                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = MaterialTheme.colorScheme.background
                    ) {
                        // ナビゲーションを開始
                        AppNavigation()
//                        MainScreen()
//                    }
//                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
//                    Greeting(
//                        name = "Android",
//                        modifier = Modifier.padding(innerPadding)
//                    )
                }
                }
            }
        }
    }
    companion object {
        private const val REQUEST_CODE_BLUETOOTH = 1001
    }
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_BLUETOOTH) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Log.d("PermissionCheck", "BLUETOOTH_CONNECT permission granted")
            } else {
                Log.e("PermissionCheck", "BLUETOOTH_CONNECT permission denied")
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