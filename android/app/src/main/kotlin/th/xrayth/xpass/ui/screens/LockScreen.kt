package th.xrayth.xpass.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Backspace
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import th.xrayth.xpass.XPassViewModel
import th.xrayth.xpass.ui.canUseBiometric
import th.xrayth.xpass.ui.showBiometricPrompt
import th.xrayth.xpass.ui.theme.LocalMonoFont

@Composable
fun LockScreen(vm: XPassViewModel) {
    val context = LocalContext.current
    val activity = context as? FragmentActivity

    var pin by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }

    fun submit() {
        if (pin.isEmpty() || busy) return
        busy = true
        if (!vm.unlockWithPin(pin)) {
            error = "PIN ไม่ถูกต้อง"
            pin = ""
        }
        busy = false
    }

    fun biometric() {
        if (activity == null) return
        val cipher = vm.prepareBiometricUnlock() ?: run {
            error = "ยังไม่ได้เปิดไบโอเมตริก"
            return
        }
        showBiometricPrompt(
            activity = activity,
            cipher = cipher,
            title = "ปลดล็อก xpass",
            subtitle = "ยืนยันตัวตนเพื่อเปิด vault",
            onSuccess = { c -> vm.unlockWithCipher(c) },
            onError = { error = it },
        )
    }

    LaunchedEffect(Unit) {
        if (vm.biometricEnabled && activity != null && canUseBiometric(activity)) biometric()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Icon(
            imageVector = Icons.Filled.Lock,
            contentDescription = null,
            modifier = Modifier.size(44.dp),
            tint = MaterialTheme.colorScheme.primary,
        )
        Spacer(Modifier.height(12.dp))
        Text(
            text = "xpass",
            style = MaterialTheme.typography.headlineMedium.copy(fontFamily = LocalMonoFont.current),
            fontWeight = FontWeight.Bold,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            text = "ใส่ PIN เพื่อปลดล็อก vault",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(Modifier.height(28.dp))

        // จุดแทนจำนวนหลัก
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            repeat(pin.length.coerceAtLeast(1)) { index ->
                val filled = index < pin.length
                Box(
                    modifier = Modifier
                        .size(14.dp)
                        .background(
                            color = if (filled) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.outlineVariant,
                            shape = CircleShape,
                        ),
                )
            }
        }

        if (error != null) {
            Spacer(Modifier.height(12.dp))
            Text(
                text = error!!,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
            )
        }

        Spacer(Modifier.height(24.dp))

        // แป้นตัวเลข
        val rows = listOf(
            listOf("1", "2", "3"),
            listOf("4", "5", "6"),
            listOf("7", "8", "9"),
        )
        rows.forEach { row ->
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                row.forEach { digit ->
                    PinKey(digit) {
                        if (pin.length < 32) {
                            pin += digit
                            error = null
                        }
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
        }

        Row(horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
            if (vm.biometricEnabled) {
                IconButton(onClick = { biometric() }, modifier = Modifier.size(64.dp)) {
                    Icon(
                        imageVector = Icons.Filled.Fingerprint,
                        contentDescription = "ไบโอเมตริก",
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(30.dp),
                    )
                }
            } else {
                Spacer(Modifier.width(64.dp))
            }

            PinKey("0") { if (pin.length < 32) pin += "0" }

            IconButton(
                onClick = { if (pin.isNotEmpty()) pin = pin.dropLast(1) },
                modifier = Modifier.size(64.dp),
            ) {
                Icon(
                    imageVector = Icons.Filled.Backspace,
                    contentDescription = "ลบ",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        Spacer(Modifier.height(20.dp))

        Button(
            onClick = { submit() },
            enabled = pin.isNotEmpty() && !busy,
            modifier = Modifier.width(200.dp),
        ) {
            Text("ปลดล็อก", fontWeight = FontWeight.SemiBold)
        }

        Spacer(Modifier.height(8.dp))
        Text(
            text = "ข้อมูลทั้งหมดถูกเข้ารหัสไว้ในเครื่องนี้",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
    }
}

@Composable
private fun PinKey(label: String, onClick: () -> Unit) {
    Box(modifier = Modifier.size(64.dp), contentAlignment = Alignment.Center) {
        TextButton(
            onClick = onClick,
            modifier = Modifier.size(64.dp),
            shape = CircleShape,
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.headlineSmall.copy(fontFamily = LocalMonoFont.current),
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}
