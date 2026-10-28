package th.xrayth.xpass.ui.screens

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Link
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Password
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import th.xrayth.xpass.XPassViewModel

private data class TabInfo(val label: String, val icon: ImageVector)

private val TABS = listOf(
    TabInfo("รหัสผ่าน", Icons.Filled.Password),
    TabInfo("2FA", Icons.Filled.Timer),
    TabInfo("ชื่อหน้า", Icons.Filled.Link),
    TabInfo("AI", Icons.Filled.AutoAwesome),
    TabInfo("ตั้งค่า", Icons.Filled.Settings),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScaffold(vm: XPassViewModel) {
    var tab by rememberSaveable { mutableStateOf(0) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = if (tab == 0) "xpass" else TABS[tab].label,
                        fontWeight = FontWeight.SemiBold,
                    )
                },
                actions = {
                    if (vm.pinEnabled || vm.biometricEnabled) {
                        IconButton(onClick = { vm.lockNow() }) {
                            Icon(Icons.Filled.Lock, contentDescription = "ล็อก")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                ),
            )
        },
        bottomBar = {
            NavigationBar(containerColor = MaterialTheme.colorScheme.surfaceContainer) {
                TABS.forEachIndexed { index, info ->
                    NavigationBarItem(
                        selected = tab == index,
                        onClick = { tab = index },
                        icon = { Icon(info.icon, contentDescription = info.label) },
                        label = { Text(info.label) },
                    )
                }
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (tab) {
                0 -> PasswordScreen(vm)
                1 -> TotpScreen(vm)
                2 -> NamesScreen(vm)
                3 -> AiScreen(vm)
                else -> SettingsScreen(vm)
            }
        }
    }
}
