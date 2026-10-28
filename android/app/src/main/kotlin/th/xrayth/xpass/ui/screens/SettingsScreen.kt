package th.xrayth.xpass.ui.screens

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material.icons.filled.DeleteForever
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FilterChip
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
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.platform.LocalContext
import androidx.fragment.app.FragmentActivity
import kotlin.math.roundToInt
import th.xrayth.xpass.BuildConfig
import th.xrayth.xpass.XPassViewModel
import th.xrayth.xpass.ui.canUseBiometric
import th.xrayth.xpass.ui.components.SectionCard
import th.xrayth.xpass.ui.showBiometricPrompt

@Composable
fun SettingsScreen(vm: XPassViewModel) {
    val activity = LocalContext.current as? FragmentActivity

    var showSetPin by remember { mutableStateOf(false) }
    var showRemovePin by remember { mutableStateOf(false) }
    var showWipe by remember { mutableStateOf(false) }
    var showExportPassDialog by remember { mutableStateOf(false) }
    var pendingExportUri by remember { mutableStateOf<android.net.Uri?>(null) }
    var showImportPassDialog by remember { mutableStateOf(false) }
    var pendingImportBytes by remember { mutableStateOf<ByteArray?>(null) }

    val exportLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        if (uri != null) {
            pendingExportUri = uri
            showExportPassDialog = true
        }
    }

    val importLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null && activity != null) {
            runCatching {
                activity.contentResolver.openInputStream(uri)?.use { it.readBytes() }
            }.getOrNull()?.let { bytes ->
                pendingImportBytes = bytes
                showImportPassDialog = true
            } ?: vm.showToast("อ่านไฟล์สำรองไม่สำเร็จ")
        }
    }

    fun toggleBiometric(on: Boolean) {
        if (!on) {
            vm.disableBiometric()
            return
        }
        if (!vm.pinEnabled) {
            vm.showToast("ตั้ง PIN ก่อน แล้วจึงเปิดไบโอเมตริก")
            return
        }
        val act = activity ?: return
        if (!canUseBiometric(act)) {
            vm.showToast("เครื่องนี้ยังไม่ได้ลงทะเบียนลายนิ้วมือหรือใบหน้า")
            return
        }
        val cipher = vm.prepareBiometricEnable() ?: return
        showBiometricPrompt(
            activity = act,
            cipher = cipher,
            title = "เปิดปลดล็อกด้วยไบโอเมตริก",
            subtitle = "ยืนยันตัวตนเพื่อผูกกับ vault นี้",
            onSuccess = { c -> vm.completeBiometricEnable(c) },
            onError = { vm.showToast(it) },
        )
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard(title = "รูปลักษณ์") {
            Text("ธีม", style = MaterialTheme.typography.labelMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(
                    "dark" to "มืด",
                    "light" to "สว่าง",
                    "system" to "ตามระบบ",
                ).forEach { (value, label) ->
                    FilterChip(
                        selected = vm.settings.theme == value,
                        onClick = { vm.updateSettings { it.copy(theme = value) } },
                        label = { Text(label) },
                    )
                }
            }

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("ขนาดตัวอักษร", modifier = Modifier.weight(1f))
                Text(
                    text = "${(vm.settings.fontScale * 100).roundToInt()}%",
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.SemiBold,
                )
            }
            Slider(
                value = vm.settings.fontScale,
                onValueChange = { value -> vm.updateSettings { it.copy(fontScale = value) } },
                valueRange = 0.8f..1.5f,
            )
        }

        SectionCard(title = "พฤติกรรม") {
            SwitchRow(
                title = "คัดลอกรหัสผ่านอัตโนมัติ",
                subtitle = "คัดลอกทันทีหลังกดสร้าง",
                checked = vm.settings.autoCopy,
            ) { on -> vm.updateSettings { s -> s.copy(autoCopy = on) } }

            SwitchRow(
                title = "จำโมเดล AI ล่าสุด",
                checked = vm.settings.rememberModel,
            ) { on -> vm.updateSettings { s -> s.copy(rememberModel = on) } }

            SwitchRow(
                title = "ล็อกเมื่อออกจากแอปเกิน 2 นาที",
                subtitle = "ต้องมี PIN ก่อน",
                checked = vm.settings.pinLockOnBackground,
            ) { on -> vm.updateSettings { s -> s.copy(pinLockOnBackground = on) } }
        }

        SectionCard(title = "ความปลอดภัย") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("PIN ปลดล็อก", style = MaterialTheme.typography.bodyMedium)
                    Text(
                        text = if (vm.pinEnabled) "เปิดอยู่ — ต้องใส่ PIN ทุกครั้งที่เปิดแอป" else "ปิดอยู่ — เปิดแอปได้ทันที",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                TextButton(onClick = {
                    if (vm.pinEnabled) showRemovePin = true else showSetPin = true
                }) {
                    Text(if (vm.pinEnabled) "ปิด/เปลี่ยน" else "ตั้ง PIN")
                }
            }

            SwitchRow(
                title = "ปลดล็อกด้วยไบโอเมตริก",
                subtitle = if (vm.pinEnabled) "ลายนิ้วมือ / ใบหน้า" else "ต้องตั้ง PIN ก่อน",
                checked = vm.biometricEnabled,
            ) { toggleBiometric(it) }

            Row(verticalAlignment = Alignment.Top) {
                Icon(
                    imageVector = Icons.Filled.Shield,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp),
                    tint = MaterialTheme.colorScheme.secondary,
                )
                Text(
                    text = "  vault ถูกเข้ารหัส AES-256-GCM ด้วยกุญแจที่ผูกกับ Keystore ของเครื่องนี้ " +
                        "และไม่ถูกสำรองขึ้นคลาวด์",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        SectionCard(title = "สำรอง / กู้คืนข้อมูล (Vault Backup)") {
            Text(
                text = "ส่งออกหรือนำเข้าข้อมูล Vault ที่เข้ารหัสด้วยรหัสผ่านสำรอง (Passphrase) สำหรับย้ายเครื่อง",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedButton(
                    onClick = { exportLauncher.launch("xpass-vault-backup.json") },
                    modifier = Modifier.weight(1f),
                ) {
                    Text("สำรองข้อมูล (Export)")
                }
                OutlinedButton(
                    onClick = { importLauncher.launch("application/json") },
                    modifier = Modifier.weight(1f),
                ) {
                    Text("กู้คืน (Import)")
                }
            }
        }

        SectionCard(title = "เกี่ยวกับ") {
            Text("xpass เวอร์ชัน ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.bodyMedium)
            Text(
                text = "พอร์ตจาก xpass เวอร์ชันเดสก์ท็อป (Python) — แท็บรหัสผ่าน, 2FA และชื่อหน้า " +
                    "คำนวณในเครื่องทั้งหมด ไม่เชื่อมต่อเครือข่าย ยกเว้นแท็บ AI",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                text = "MIT License · Copyright (c) 2026 XRayTH",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        OutlinedButton(
            onClick = { showWipe = true },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Icon(
                Icons.Filled.DeleteForever,
                contentDescription = null,
                modifier = Modifier.size(18.dp),
                tint = MaterialTheme.colorScheme.error,
            )
            Text("  ล้างข้อมูลทั้งหมด", color = MaterialTheme.colorScheme.error)
        }
    }

    if (showSetPin) {
        SetPinDialog(
            hasExisting = vm.pinEnabled,
            onDismiss = { showSetPin = false },
            onConfirm = { newPin ->
                if (vm.setPin(newPin)) {
                    showSetPin = false
                    true
                } else {
                    false
                }
            },
        )
    }

    if (showRemovePin) {
        RemovePinDialog(
            onDismiss = { showRemovePin = false },
            onConfirm = { pin ->
                val ok = vm.removePin(pin)
                if (ok) {
                    vm.disableBiometric()
                    showRemovePin = false
                }
                ok
            },
        )
    }

    if (showWipe) {
        AlertDialog(
            onDismissRequest = { showWipe = false },
            title = { Text("ล้างข้อมูลทั้งหมด?") },
            text = {
                Text(
                    "บัญชี 2FA, PIN และการตั้งค่าจะถูกลบอย่างถาวร " +
                        "และกู้คืนไม่ได้ (ไม่มีข้อมูลสำรองบนคลาวด์)",
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    vm.wipeEverything()
                    showWipe = false
                }) { Text("ล้างทั้งหมด", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = {
                TextButton(onClick = { showWipe = false }) { Text("ยกเลิก") }
            },
        )
    }

    if (showExportPassDialog && pendingExportUri != null && activity != null) {
        ExportPassphraseDialog(
            onDismiss = {
                showExportPassDialog = false
                pendingExportUri = null
            },
            onConfirm = { passphrase ->
                val bytes = vm.exportVault(passphrase)
                if (bytes != null) {
                    runCatching {
                        activity.contentResolver.openOutputStream(pendingExportUri!!)?.use { it.write(bytes) }
                        vm.showToast("สำรองข้อมูล Vault สำเร็จ")
                    }.onFailure {
                        vm.showToast("บันทึกไฟล์ไม่สำเร็จ: ${it.message}")
                    }
                } else {
                    vm.showToast("สร้างข้อมูลสำรองไม่สำเร็จ")
                }
                showExportPassDialog = false
                pendingExportUri = null
            },
        )
    }

    if (showImportPassDialog && pendingImportBytes != null) {
        ImportPassphraseDialog(
            onDismiss = {
                showImportPassDialog = false
                pendingImportBytes = null
            },
            onConfirm = { passphrase ->
                val ok = vm.importVault(pendingImportBytes!!, passphrase)
                if (ok) {
                    vm.showToast("กู้คืนข้อมูล Vault สำเร็จ")
                } else {
                    vm.showToast("รหัสผ่านไม่ถูกต้องหรือไฟล์เสียหาย")
                }
                showImportPassDialog = false
                pendingImportBytes = null
            },
        )
    }
}

@Composable
private fun SetPinDialog(
    hasExisting: Boolean,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Boolean,
) {
    var pin by remember { mutableStateOf("") }
    var confirm by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (hasExisting) "เปลี่ยน PIN" else "ตั้ง PIN") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = pin,
                    onValueChange = { if (it.length <= 12) pin = it.filter(Char::isDigit) },
                    label = { Text("PIN ใหม่ (4–12 หลัก)") },
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    singleLine = true,
                )
                OutlinedTextField(
                    value = confirm,
                    onValueChange = { if (it.length <= 12) confirm = it.filter(Char::isDigit) },
                    label = { Text("ยืนยัน PIN") },
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    singleLine = true,
                )
                if (error != null) {
                    Text(error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelMedium)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                when {
                    pin.length < 4 -> error = "PIN ต้องมีอย่างน้อย 4 หลัก"
                    pin != confirm -> error = "PIN ทั้งสองช่องไม่ตรงกัน"
                    !onConfirm(pin) -> error = "บันทึก PIN ไม่สำเร็จ"
                }
            }) { Text("บันทึก") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("ยกเลิก") } },
    )
}

@Composable
private fun RemovePinDialog(
    onDismiss: () -> Unit,
    onConfirm: (String) -> Boolean,
) {
    var pin by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("ปิด PIN") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("ใส่ PIN ปัจจุบันเพื่อยืนยัน")
                OutlinedTextField(
                    value = pin,
                    onValueChange = { if (it.length <= 12) pin = it.filter(Char::isDigit) },
                    label = { Text("PIN ปัจจุบัน") },
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    singleLine = true,
                )
                if (error != null) {
                    Text(error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelMedium)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                if (!onConfirm(pin)) error = "PIN ไม่ถูกต้อง" else error = null
            }) { Text("ยืนยัน") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("ยกเลิก") } },
    )
}

@Composable
private fun ExportPassphraseDialog(
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    var passphrase by remember { mutableStateOf("") }
    var confirm by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("กำหนดรหัสผ่านสำหรับสำรองข้อมูล") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("รหัสผ่านนี้ใช้เข้ารหัสไฟล์สำรอง ป้องกันผู้อื่นเปิดอ่านข้อมูล Vault ของคุณ")
                OutlinedTextField(
                    value = passphrase,
                    onValueChange = { passphrase = it },
                    label = { Text("รหัสผ่านสำรอง") },
                    visualTransformation = PasswordVisualTransformation(),
                    singleLine = true,
                )
                OutlinedTextField(
                    value = confirm,
                    onValueChange = { confirm = it },
                    label = { Text("ยืนยันรหัสผ่านสำรอง") },
                    visualTransformation = PasswordVisualTransformation(),
                    singleLine = true,
                )
                if (error != null) {
                    Text(error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelMedium)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                when {
                    passphrase.length < 6 -> error = "รหัสผ่านต้องมีอย่างน้อย 6 ตัว"
                    passphrase != confirm -> error = "รหัสผ่านทั้งสองช่องไม่ตรงกัน"
                    else -> onConfirm(passphrase)
                }
            }) { Text("ส่งออก") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("ยกเลิก") } },
    )
}

@Composable
private fun ImportPassphraseDialog(
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    var passphrase by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("ใส่รหัสผ่านไฟล์สำรอง") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("ใส่รหัสผ่านที่ใช้ตอนสำรองข้อมูลเพื่อกู้คืน Vault")
                OutlinedTextField(
                    value = passphrase,
                    onValueChange = { passphrase = it },
                    label = { Text("รหัสผ่านสำรอง") },
                    visualTransformation = PasswordVisualTransformation(),
                    singleLine = true,
                )
                if (error != null) {
                    Text(error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelMedium)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                if (passphrase.isBlank()) error = "กรุณากรอกรหัสผ่าน" else onConfirm(passphrase)
            }) { Text("กู้คืน") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("ยกเลิก") } },
    )
}
