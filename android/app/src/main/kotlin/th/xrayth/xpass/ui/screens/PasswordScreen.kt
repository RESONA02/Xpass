package th.xrayth.xpass.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlin.math.roundToInt
import th.xrayth.xpass.XPassViewModel
import th.xrayth.xpass.core.Crypto
import th.xrayth.xpass.ui.components.CopyIconButton
import th.xrayth.xpass.ui.components.MonoText
import th.xrayth.xpass.ui.components.SectionCard
import th.xrayth.xpass.ui.components.rememberClipboardCopy
import th.xrayth.xpass.ui.theme.LocalMonoFont

@Composable
fun PasswordScreen(vm: XPassViewModel) {
    val copy = rememberClipboardCopy()

    LaunchedEffect(vm.pwRevision) {
        val result = vm.pwResult
        if (vm.pwRevision > 0 && vm.settings.autoCopy && result != null) {
            copy(result.value, "คัดลอกรหัสผ่านอัตโนมัติแล้ว")
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        val result = vm.pwResult

        SectionCard(title = "รหัสผ่านที่สร้าง") {
            if (result != null) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    MonoText(
                        text = result.value,
                        modifier = Modifier.weight(1f),
                        style = MaterialTheme.typography.headlineSmall,
                        maxLines = 3,
                    )
                    CopyIconButton(result.value, message = "คัดลอกรหัสผ่านแล้ว")
                }

                val strength = (result.entropyBits / 128.0).toFloat().coerceIn(0.04f, 1f)
                LinearProgressIndicator(
                    progress = { strength },
                    modifier = Modifier.fillMaxWidth(),
                    color = strengthColor(result.entropyBits),
                    trackColor = MaterialTheme.colorScheme.surfaceVariant,
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = Crypto.entropyLabel(result.entropyBits),
                        style = MaterialTheme.typography.bodySmall,
                        color = strengthColor(result.entropyBits),
                        modifier = Modifier.weight(1f),
                    )
                    Text(
                        text = "${result.poolSize} ตัวอักษรให้เลือก",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            Button(
                onClick = { vm.generatePassword() },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Filled.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
                Text("  สร้างใหม่", fontWeight = FontWeight.SemiBold)
            }
        }

        SectionCard(title = "ตัวเลือก") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("ความยาว", modifier = Modifier.weight(1f))
                Text(
                    text = "${vm.pwLength}",
                    style = MaterialTheme.typography.titleMedium.copy(fontFamily = LocalMonoFont.current),
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                )
            }
            Slider(
                value = vm.pwLength.toFloat(),
                onValueChange = {
                    vm.pwLength = it.roundToInt()
                },
                onValueChangeFinished = { vm.generatePassword() },
                valueRange = 8f..128f,
                steps = 119,
            )

            SwitchRow(
                title = "ใส่สัญลักษณ์ (!@#\$…)",
                checked = vm.pwSymbols,
            ) {
                vm.pwSymbols = it
                vm.generatePassword()
            }

            SwitchRow(
                title = "ตัดตัวที่อ่านสับสน (Il1O0o)",
                checked = vm.pwNoAmbiguous,
            ) {
                vm.pwNoAmbiguous = it
                vm.generatePassword()
            }
        }

        Text(
            text = "สร้างในเครื่องด้วย SecureRandom ของ Android — ไม่ส่งข้อมูลออกไปไหน",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
fun SwitchRow(
    title: String,
    checked: Boolean,
    subtitle: String? = null,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyMedium)
            if (subtitle != null) {
                Text(
                    subtitle,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

fun strengthColor(bits: Double): Color = when {
    bits >= 100 -> Color(0xFF3FCF7F)
    bits >= 80 -> Color(0xFF9BD85C)
    bits >= 60 -> Color(0xFFFFC46B)
    else -> Color(0xFFFF6B7D)
}
