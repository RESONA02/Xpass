package th.xrayth.xpass.ui

import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import th.xrayth.xpass.XPassViewModel
import th.xrayth.xpass.ui.screens.LockScreen
import th.xrayth.xpass.ui.screens.MainScaffold
import th.xrayth.xpass.ui.theme.XPassTheme

@Composable
fun XPassApp(vm: XPassViewModel) {
    val context = LocalContext.current

    XPassTheme(theme = vm.settings.theme, fontScale = vm.settings.fontScale) {
        LaunchedEffect(vm.toast) {
            val message = vm.toast ?: return@LaunchedEffect
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
            vm.consumeToast()
        }

        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background,
        ) {
            when (vm.lockState) {
                XPassViewModel.LockState.Checking -> LoadingScreen()
                XPassViewModel.LockState.Locked -> LockScreen(vm)
                XPassViewModel.LockState.Unlocked -> MainScaffold(vm)
            }
        }
    }
}

@Composable
private fun LoadingScreen() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            CircularProgressIndicator(modifier = Modifier.size(36.dp))
            Text("กำลังโหลด…", style = MaterialTheme.typography.bodyMedium)
        }
    }
}
