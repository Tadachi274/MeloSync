package com.example.melosync.ui.auth

import android.content.Context
import androidx.datastore.preferences.preferencesDataStore

// Context.dataStore でアクセスできるように
val Context.dataStore by preferencesDataStore(name = "auth_prefs")