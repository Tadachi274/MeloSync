package com.example.melosync

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.example.melosync.ui.theme.MeloSyncTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import com.example.melosync.navigation.AppNavigation
import com.example.melosync.ui.theme.AppBackground
import androidx.activity.viewModels
import com.example.melosync.ui.auth.AuthViewModel
import android.util.Log

class MainActivity : ComponentActivity() {
    private val authViewModel: AuthViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
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
                        Log.d("MainActivity","open")
                        AppNavigation(authViewModel)

                    }
//                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
//                    Greeting(
//                        name = "Android",
//                        modifier = Modifier.padding(innerPadding)
//                    )
                }
            }
        }
    }
    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        Log.d("MainActivity","onNewIntent")
        enableEdgeToEdge()
        setContent {
            MeloSyncTheme {
                AppBackground {
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = MaterialTheme.colorScheme.background
                    ) {
                        // ナビゲーションを開始
                        Log.d("MainActivity","new open")
                        AppNavigation(authViewModel)

                    }
//                    )
//                }
                }
            }
        }
        setIntent(intent) // 新しいIntentで上書きする（省略すると getIntent() が古いままになる）

        //handleIntent(intent)
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