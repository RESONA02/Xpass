package th.xrayth.xpass.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.DeleteSweep
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import th.xrayth.xpass.XPassViewModel
import th.xrayth.xpass.ai.AiClient
import th.xrayth.xpass.ui.components.CopyIconButton
import th.xrayth.xpass.ui.components.SectionCard
import th.xrayth.xpass.ui.components.rememberClipboardCopy

@Composable
fun AiScreen(vm: XPassViewModel) {
    var keyVisible by remember { mutableStateOf(false) }
    // ซ่อนการ์ดตั้งค่าโมเดลเมื่อกำลังพิมพ์ และเปิดกลับได้จากแถบย่อ
    var showSettings by rememberSaveable { mutableStateOf(true) }
    val listState = rememberLazyListState()
    val copy = rememberClipboardCopy()

    LaunchedEffect(vm.aiMessages.size) {
        if (vm.aiMessages.isNotEmpty()) {
            listState.animateScrollToItem(vm.aiMessages.lastIndex)
        }
    }

    Column(Modifier.fillMaxSize().imePadding()) {
        if (showSettings) {
            SectionCard(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                title = "ตั้งค่าโมเดล",
                trailing = {
                    if (vm.aiMessages.isNotEmpty()) {
                        IconButton(onClick = { vm.clearChat() }) {
                            Icon(Icons.Filled.DeleteSweep, contentDescription = "ล้างแชท")
                        }
                    }
                    IconButton(onClick = { showSettings = false }) {
                        Icon(Icons.Filled.ExpandLess, contentDescription = "ซ่อนตั้งค่าโมเดล")
                    }
                },
            ) {
                OutlinedTextField(
                    value = vm.aiApiKey,
                    onValueChange = { vm.aiApiKey = it },
                    label = { Text("API key (อยู่ในหน่วยความจำเท่านั้น)") },
                    singleLine = true,
                    visualTransformation = if (keyVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    trailingIcon = {
                        IconButton(onClick = { keyVisible = !keyVisible }) {
                            Icon(
                                imageVector = if (keyVisible) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                                contentDescription = "แสดง/ซ่อนคีย์",
                            )
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                )

                Row(verticalAlignment = Alignment.CenterVertically) {
                    OutlinedTextField(
                        value = vm.aiModel,
                        onValueChange = { vm.updateAiModel(it) },
                        label = { Text("โมเดล") },
                        singleLine = true,
                        modifier = Modifier.weight(1f),
                    )
                    IconButton(onClick = { vm.refreshModels() }, enabled = !vm.aiBusy) {
                        Icon(Icons.Filled.Refresh, contentDescription = "รีเฟรชรายการโมเดล")
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    vm.aiModelList.take(10).forEach { name ->
                        AssistChip(
                            onClick = { vm.updateAiModel(name) },
                            label = { Text(name, style = MaterialTheme.typography.labelSmall) },
                        )
                    }
                }

                Text(
                    text = "ผู้ให้บริการ: ${AiClient.providerLabel(vm.aiProvider)} · " +
                        "ข้อความในแชทจะถูกส่งออกไปยังผู้ให้บริการ — ห้ามพิมพ์รหัสผ่านจริง",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        } else {
            SettingsBar(model = vm.aiModel, onExpand = { showSettings = true })
        }

        if (vm.aiError != null) {
            Surface(
                color = MaterialTheme.colorScheme.errorContainer,
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
            ) {
                Text(
                    text = vm.aiError!!,
                    color = MaterialTheme.colorScheme.onErrorContainer,
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(12.dp),
                )
            }
        }

        if (vm.aiMessages.isEmpty()) {
            Column(
                modifier = Modifier.weight(1f).fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Icon(
                    imageVector = Icons.Filled.AutoAwesome,
                    contentDescription = null,
                    modifier = Modifier.size(44.dp),
                    tint = MaterialTheme.colorScheme.primary,
                )
                Text("ถามเรื่องรหัสผ่านและ 2FA ได้", style = MaterialTheme.typography.bodyMedium)
                Text(
                    "เช่น “ควรใช้ความยาวรหัสผ่านเท่าไร”",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        } else {
            LazyColumn(
                state = listState,
                modifier = Modifier.weight(1f).fillMaxWidth(),
                contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                itemsIndexed(vm.aiMessages) { index, msg ->
                    ChatBubble(
                        role = msg.role,
                        text = msg.content,
                        onCopy = {
                            if (msg.role == "assistant") copy(msg.content, "คัดลอกคำตอบแล้ว")
                        },
                    )
                    if (index == vm.aiMessages.lastIndex && vm.aiBusy) {
                        CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    }
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            OutlinedTextField(
                value = vm.aiInput,
                onValueChange = { vm.aiInput = it },
                placeholder = { Text("พิมพ์คำถาม…") },
                maxLines = 4,
                // เริ่มพิมพ์เมื่อไรก็เก็บการ์ดตั้งค่าโมเดลลง เพื่อให้เห็นแชทเต็มพื้นที่
                modifier = Modifier
                    .weight(1f)
                    .onFocusChanged { if (it.isFocused) showSettings = false },
            )
            Button(
                onClick = { vm.sendAi() },
                enabled = !vm.aiBusy && vm.aiInput.isNotBlank(),
                modifier = Modifier.padding(bottom = 4.dp),
            ) {
                Icon(Icons.Filled.Send, contentDescription = "ส่ง", modifier = Modifier.size(18.dp))
            }
        }
    }
}

/** แถบย่อแทนการ์ดตั้งค่าโมเดล ขณะที่การ์ดถูกซ่อนอยู่ */
@Composable
private fun SettingsBar(model: String, onExpand: () -> Unit) {
    val shape = RoundedCornerShape(12.dp)
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .clip(shape)
            .clickable(onClick = onExpand),
        shape = shape,
        color = MaterialTheme.colorScheme.surface,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                imageVector = Icons.Filled.Tune,
                contentDescription = null,
                modifier = Modifier.size(18.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text("ตั้งค่าโมเดล", style = MaterialTheme.typography.labelMedium)
                Text(
                    text = model.ifBlank { "ยังไม่ได้เลือกโมเดล" },
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            Icon(
                imageVector = Icons.Filled.ExpandMore,
                contentDescription = "แสดงตั้งค่าโมเดล",
                modifier = Modifier.size(20.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun ChatBubble(role: String, text: String, onCopy: () -> Unit) {
    val isUser = role == "user"
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start,
    ) {
        Surface(
            shape = RoundedCornerShape(
                topStart = 16.dp,
                topEnd = 16.dp,
                bottomStart = if (isUser) 16.dp else 4.dp,
                bottomEnd = if (isUser) 4.dp else 16.dp,
            ),
            color = if (isUser) MaterialTheme.colorScheme.primaryContainer
            else MaterialTheme.colorScheme.surfaceVariant,
            modifier = Modifier.widthIn(max = 320.dp),
        ) {
            Column(Modifier.padding(12.dp)) {
                Text(
                    text = text,
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (isUser) MaterialTheme.colorScheme.onPrimaryContainer
                    else MaterialTheme.colorScheme.onSurface,
                )
                if (!isUser) {
                    Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
                        CopyIconButton(text, message = "คัดลอกคำตอบแล้ว")
                    }
                }
            }
        }
    }
}
