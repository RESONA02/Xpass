package th.xrayth.xpass.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ContentPaste
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import kotlinx.coroutines.delay
import th.xrayth.xpass.XPassViewModel
import th.xrayth.xpass.core.Crypto
import th.xrayth.xpass.data.TotpAccount
import th.xrayth.xpass.ui.components.MonoText
import th.xrayth.xpass.ui.components.QrCodeDialog
import th.xrayth.xpass.ui.components.SectionCard
import th.xrayth.xpass.ui.components.rememberClipboardCopy
import th.xrayth.xpass.ui.theme.LocalMonoFont
import th.xrayth.xpass.util.scanQrCode

@Composable
fun TotpScreen(vm: XPassViewModel) {
    val activity = LocalContext.current as? FragmentActivity

    var showAdd by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf<TotpAccount?>(null) }
    var prefill by remember { mutableStateOf<Crypto.OtpAuth?>(null) }
    var qrTarget by remember { mutableStateOf<TotpAccount?>(null) }
    var deleteTarget by remember { mutableStateOf<TotpAccount?>(null) }

    var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(Unit) {
        while (true) {
            now = System.currentTimeMillis()
            delay(250)
        }
    }

    fun openScanner() {
        if (activity == null) return
        scanQrCode(
            activity = activity,
            onResult = { raw ->
                val parsed = Crypto.parseOtpInput(raw)
                if (parsed == null) {
                    vm.showToast("QR นี้ไม่ใช่ otpauth:// ของ TOTP")
                } else {
                    prefill = parsed
                    showAdd = true
                }
            },
            onError = { vm.showToast(it) },
        )
    }

    Column(Modifier.fillMaxSize()) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Button(
                onClick = { prefill = null; showAdd = true },
                modifier = Modifier.weight(1f),
            ) {
                Icon(Icons.Filled.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                Text("  เพิ่มบัญชี", fontWeight = FontWeight.SemiBold)
            }
            OutlinedButton(onClick = { openScanner() }) {
                Icon(Icons.Filled.QrCodeScanner, contentDescription = null, modifier = Modifier.size(18.dp))
                Text("  สแกน")
            }
        }

        if (vm.accounts.isEmpty()) {
            EmptyTotp()
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(
                    start = 16.dp, end = 16.dp, top = 4.dp, bottom = 24.dp,
                ),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                items(vm.accounts, key = { it.id }) { acc ->
                    TotpCard(
                        account = acc,
                        now = now,
                        onOpenQr = { qrTarget = acc },
                        onEdit = { editing = acc },
                        onDelete = { deleteTarget = acc },
                    )
                }
            }
        }
    }

    if (showAdd || editing != null) {
        AccountDialog(
            initial = editing,
            prefill = prefill,
            onDismiss = { showAdd = false; editing = null; prefill = null },
            onSave = { acc ->
                if (editing != null) vm.updateAccount(acc) else vm.addAccount(acc)
                showAdd = false
                editing = null
                prefill = null
            },
        )
    }

    qrTarget?.let { acc ->
        val uri = Crypto.otpauthUri(acc.secret, acc.issuer.ifBlank { acc.title }, acc.account)
        QrCodeDialog(
            title = acc.title,
            uri = uri,
            onDismiss = { qrTarget = null },
        )
    }

    deleteTarget?.let { acc ->
        AlertDialog(
            onDismissRequest = { deleteTarget = null },
            title = { Text("ลบบัญชี?") },
            text = { Text("“${acc.title}” จะถูกลบออกจาก vault อย่างถาวร") },
            confirmButton = {
                TextButton(onClick = {
                    vm.deleteAccount(acc.id)
                    deleteTarget = null
                }) { Text("ลบ", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = {
                TextButton(onClick = { deleteTarget = null }) { Text("ยกเลิก") }
            },
        )
    }
}

@Composable
private fun EmptyTotp() {
    Box(Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(
                imageVector = Icons.Filled.Timer,
                contentDescription = null,
                modifier = Modifier.size(48.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(12.dp))
            Text(
                text = "ยังไม่มีบัญชี 2FA",
                style = MaterialTheme.typography.titleMedium,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = "กด “เพิ่มบัญชี” แล้ววาง secret หรือสแกน QR จากเว็บ/แอปอื่น",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun TotpCard(
    account: TotpAccount,
    now: Long,
    onOpenQr: () -> Unit,
    onEdit: () -> Unit,
    onDelete: () -> Unit,
) {
    val copy = rememberClipboardCopy()
    var menu by remember { mutableStateOf(false) }

    val period = account.period.coerceAtLeast(5)
    val step = now / 1000L / period
    val remaining = (period - (now / 1000L % period)).toInt().coerceIn(0, period)
    val code = remember(account.secret, account.digits, period, account.algorithm, step) {
        Crypto.currentTotp(account.secret, account.digits, period, account.algorithm)
    } ?: "------"

    val urgent = remaining <= 5

    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(
                    text = account.title,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                )
                if (account.subtitle.isNotBlank()) {
                    Text(
                        text = account.subtitle,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            Box(contentAlignment = Alignment.Center, modifier = Modifier.size(38.dp)) {
                CircularProgressIndicator(
                    progress = { remaining.toFloat() / period.toFloat() },
                    modifier = Modifier.size(38.dp),
                    strokeWidth = 3.dp,
                    color = if (urgent) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                    trackColor = MaterialTheme.colorScheme.surfaceVariant,
                )
                Text(
                    text = "$remaining",
                    style = MaterialTheme.typography.labelSmall.copy(fontFamily = LocalMonoFont.current),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Box {
                IconButton(onClick = { menu = true }) {
                    Icon(Icons.Filled.MoreVert, contentDescription = "ตัวเลือก")
                }
                DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                    DropdownMenuItem(
                        text = { Text("แก้ไข") },
                        leadingIcon = { Icon(Icons.Filled.Edit, contentDescription = null) },
                        onClick = { menu = false; onEdit() },
                    )
                    DropdownMenuItem(
                        text = { Text("แสดง QR") },
                        leadingIcon = { Icon(Icons.Filled.QrCode, contentDescription = null) },
                        onClick = { menu = false; onOpenQr() },
                    )
                    DropdownMenuItem(
                        text = { Text("ลบ") },
                        leadingIcon = { Icon(Icons.Filled.Delete, contentDescription = null) },
                        onClick = { menu = false; onDelete() },
                    )
                }
            }
        }

        val formatted = code.chunked(3).joinToString(" ")
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f),
                    shape = RoundedCornerShape(12.dp),
                )
                .clickable { if (code != "------") copy(code, "คัดลอกรหัส 2FA แล้ว") }
                .padding(horizontal = 14.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            MonoText(
                text = formatted,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.headlineSmall,
                color = if (urgent) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface,
            )
            Icon(
                imageVector = Icons.Filled.ContentPaste,
                contentDescription = "คัดลอก",
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(18.dp),
            )
        }
    }
}

@Composable
private fun AccountDialog(
    initial: TotpAccount?,
    prefill: Crypto.OtpAuth?,
    onDismiss: () -> Unit,
    onSave: (TotpAccount) -> Unit,
) {
    var issuer by remember { mutableStateOf(initial?.issuer ?: prefill?.issuer ?: "") }
    var account by remember { mutableStateOf(initial?.account ?: prefill?.account ?: "") }
    var secret by remember { mutableStateOf(initial?.secret ?: prefill?.secret ?: "") }
    var note by remember { mutableStateOf(initial?.note ?: "") }
    var error by remember { mutableStateOf<String?>(null) }
    val clipboard = LocalClipboardManager.current

    fun pasteFromClipboard() {
        val text = clipboard.getText()?.text?.trim().orEmpty()
        if (text.isBlank()) {
            error = "คลิปบอร์ดว่าง"
            return
        }
        val parsed = Crypto.parseOtpInput(text)
        if (parsed == null) {
            error = "ไม่พบ secret ที่ถูกต้องในคลิปบอร์ด"
            return
        }
        secret = parsed.secret
        if (parsed.issuer.isNotBlank()) issuer = parsed.issuer
        if (parsed.account.isNotBlank()) account = parsed.account
        error = null
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (initial == null) "เพิ่มบัญชี 2FA" else "แก้ไขบัญชี") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = issuer,
                    onValueChange = { issuer = it },
                    label = { Text("ผู้ให้บริการ (issuer)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = account,
                    onValueChange = { account = it },
                    label = { Text("บัญชี / อีเมล") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = secret,
                    onValueChange = { secret = it },
                    label = { Text("Secret (base32) หรือลิงก์ otpauth") },
                    modifier = Modifier.fillMaxWidth(),
                    textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = LocalMonoFont.current),
                )
                OutlinedTextField(
                    value = note,
                    onValueChange = { note = it },
                    label = { Text("โน้ต (ไม่บังคับ)") },
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedButton(onClick = { pasteFromClipboard() }, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Filled.ContentPaste, contentDescription = null, modifier = Modifier.size(18.dp))
                    Text("  วางจากคลิปบอร์ด")
                }
                if (error != null) {
                    Text(
                        text = error!!,
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.labelMedium,
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                val parsed = Crypto.parseOtpInput(secret)
                if (parsed == null) {
                    error = "secret ไม่ถูกต้อง (ต้องเป็น A-Z กับเลข 2-7)"
                    return@TextButton
                }
                val base = initial ?: TotpAccount()
                onSave(
                    base.copy(
                        issuer = issuer.trim(),
                        account = account.trim(),
                        secret = parsed.secret,
                        digits = parsed.digits,
                        period = parsed.period,
                        algorithm = parsed.algorithm,
                        note = note.trim(),
                    ),
                )
            }) { Text("บันทึก") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("ยกเลิก") }
        },
    )
}
