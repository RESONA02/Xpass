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
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlin.math.roundToInt
import th.xrayth.xpass.XPassViewModel
import th.xrayth.xpass.core.Crypto
import th.xrayth.xpass.ui.components.CopyIconButton
import th.xrayth.xpass.ui.components.LabeledValue
import th.xrayth.xpass.ui.components.MonoText
import th.xrayth.xpass.ui.components.QrCodeDialog
import th.xrayth.xpass.ui.components.SectionCard
import th.xrayth.xpass.ui.theme.LocalMonoFont

@Composable
fun NamesScreen(vm: XPassViewModel) {
    var prefix by rememberSaveable { mutableStateOf("a-") }
    var length by rememberSaveable { mutableStateOf(24) }
    var slug by rememberSaveable { mutableStateOf(Crypto.slug(24)) }
    var showAdminQr by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard(title = "ชื่อหน้า / ไฟล์ลับ") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                MonoText(
                    text = "$prefix$slug.html",
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.titleMedium,
                    maxLines = 2,
                )
                CopyIconButton("$prefix$slug.html", message = "คัดลอกชื่อหน้าแล้ว")
            }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("ความยาว", modifier = Modifier.weight(1f))
                Text(
                    text = "$length",
                    style = MaterialTheme.typography.titleMedium.copy(fontFamily = LocalMonoFont.current),
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold,
                )
            }
            Slider(
                value = length.toFloat(),
                onValueChange = { length = it.roundToInt() },
                valueRange = 8f..64f,
                steps = 55,
            )

            OutlinedTextField(
                value = prefix,
                onValueChange = { prefix = it.take(12) },
                label = { Text("คำนำหน้า") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )

            Button(
                onClick = { slug = Crypto.slug(length) },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Filled.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
                Text("  สร้างชื่อใหม่", fontWeight = FontWeight.SemiBold)
            }

            Text(
                text = "ประมาณ ${(length * kotlin.math.log2(36.0)).toInt()} บิต — ใช้ตั้งชื่อหน้า admin หรือไฟล์ที่ไม่อยากให้เดาได้",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        SectionCard(
            title = "ชุดค่า admin (Cloudflare Worker)",
            trailing = {
                if (vm.adminResult != null) {
                    IconButtonSmall(onClick = { showAdminQr = true }) {
                        Icon(Icons.Filled.QrCode, contentDescription = "QR")
                    }
                }
            },
        ) {
            val admin = vm.adminResult
            if (admin == null) {
                Text(
                    text = "สร้าง ADMIN_TOKEN + TOTP secret + ชื่อหน้าลับ พร้อม QR สำหรับเพิ่มในแอป Authenticator",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            } else {
                LabeledValue("ADMIN_TOKEN", admin.token, onCopied = "คัดลอก ADMIN_TOKEN แล้ว")
                LabeledValue("ADMIN_TOTP_SECRET", admin.secret, onCopied = "คัดลอก secret แล้ว")
                LabeledValue("ชื่อหน้า admin", admin.page, onCopied = "คัดลอกชื่อหน้าแล้ว")
                Text(
                    text = "รหัสตอนนี้: ${admin.code.chunked(3).joinToString(" ")}",
                    style = MaterialTheme.typography.bodyMedium.copy(fontFamily = LocalMonoFont.current),
                    color = MaterialTheme.colorScheme.secondary,
                )
                OutlinedButton(onClick = { showAdminQr = true }, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Filled.QrCode, contentDescription = null, modifier = Modifier.size(18.dp))
                    Text("  แสดง QR")
                }
                Text(
                    text = "ค่าเหล่านี้แสดงเฉพาะรอบนี้และไม่ถูกบันทึก — คัดลอกไปตั้งใน Cloudflare ก่อนปิด",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            Button(
                onClick = { vm.generateAdmin() },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Filled.Refresh, contentDescription = null, modifier = Modifier.size(18.dp))
                Text("  สร้างชุดใหม่", fontWeight = FontWeight.SemiBold)
            }
        }
    }

    if (showAdminQr) {
        val admin = vm.adminResult
        if (admin != null) {
            QrCodeDialog(
                title = "เพิ่มใน Authenticator",
                uri = admin.uri,
                onDismiss = { showAdminQr = false },
            )
        }
    }
}

@Composable
private fun IconButtonSmall(onClick: () -> Unit, content: @Composable () -> Unit) {
    TextButton(onClick = onClick) { content() }
}
