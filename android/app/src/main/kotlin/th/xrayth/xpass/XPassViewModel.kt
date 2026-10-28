package th.xrayth.xpass

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import th.xrayth.xpass.ai.AiClient
import th.xrayth.xpass.core.Crypto
import th.xrayth.xpass.data.AppSettings
import th.xrayth.xpass.data.SettingsRepo
import th.xrayth.xpass.data.TotpAccount
import th.xrayth.xpass.data.VaultData
import th.xrayth.xpass.data.VaultRepo
import javax.crypto.Cipher
import org.json.JSONObject

class XPassViewModel(app: Application) : AndroidViewModel(app) {

    private val repo = VaultRepo(app)
    private val settingsRepo = SettingsRepo(app)

    enum class LockState { Checking, Locked, Unlocked }

    var lockState by mutableStateOf(LockState.Checking)
        private set

    var settings by mutableStateOf(settingsRepo.load())
        private set

    var accounts by mutableStateOf<List<TotpAccount>>(emptyList())
        private set

    var pinEnabled by mutableStateOf(repo.hasPin)
        private set

    var biometricEnabled by mutableStateOf(repo.biometricEnabled)
        private set

    var toast by mutableStateOf<String?>(null)
        private set

    // ---------- ตัวสร้างรหัสผ่าน ----------
    var pwLength by mutableIntStateOf(20)
    var pwSymbols by mutableStateOf(true)
    var pwNoAmbiguous by mutableStateOf(false)
    var pwResult by mutableStateOf<Crypto.Generated?>(null)
    var pwRevision by mutableIntStateOf(0)
        private set

    // ---------- ชื่อหน้า / admin ----------
    var adminResult by mutableStateOf<Crypto.AdminValues?>(null)

    // ---------- AI ----------
    var aiMessages by mutableStateOf<List<AiClient.ChatMessage>>(emptyList())
    var aiInput by mutableStateOf("")
    var aiModel by mutableStateOf(settings.lastModel.ifBlank { AiClient.DEFAULT_GEMINI_MODEL })
    var aiProvider by mutableStateOf(AiClient.providerForModel(settings.lastModel.ifBlank { AiClient.DEFAULT_GEMINI_MODEL }))
    var aiApiKey by mutableStateOf("")          // หน่วยความจำเท่านั้น ไม่ลงดิสก์
    var aiModelList by mutableStateOf(AiClient.MODEL_CHOICES)
    var aiBusy by mutableStateOf(false)
    var aiError by mutableStateOf<String?>(null)

    init {
        val unlocked = runCatching { repo.prepare() }.getOrDefault(false)
        if (unlocked) {
            accounts = repo.load().accounts
            lockState = LockState.Unlocked
        } else {
            lockState = LockState.Locked
        }
        pwResult = Crypto.password(pwLength, pwSymbols, pwNoAmbiguous)
    }

    // ---------- lock / unlock ----------
    fun unlockWithPin(pin: String): Boolean {
        val ok = runCatching { repo.unlockWithPin(pin) }.getOrDefault(false)
        if (ok) onUnlocked() else toast = "PIN ไม่ถูกต้อง"
        return ok
    }

    fun prepareBiometricUnlock(): Cipher? = repo.prepareBiometricUnlock()

    fun unlockWithCipher(cipher: Cipher): Boolean {
        val ok = repo.completeBiometricUnlock(cipher)
        if (ok) onUnlocked() else toast = "ปลดล็อกด้วยไบโอเมตริกไม่สำเร็จ"
        return ok
    }

    private fun onUnlocked() {
        accounts = repo.load().accounts
        pinEnabled = repo.hasPin
        biometricEnabled = repo.biometricEnabled
        lockState = LockState.Unlocked
    }

    fun lockNow() {
        repo.lock()
        lockState = LockState.Locked
    }

    // ---------- vault ----------
    private fun persist(list: List<TotpAccount>) {
        val sorted = list.sortedBy { it.title.lowercase() }
        accounts = sorted
        if (!repo.save(VaultData(sorted))) toast = "บันทึกไม่สำเร็จ"
    }

    fun addAccount(account: TotpAccount) = persist(accounts + account)

    fun updateAccount(account: TotpAccount) =
        persist(accounts.map { if (it.id == account.id) account else it })

    fun deleteAccount(id: String) = persist(accounts.filterNot { it.id == id })

    fun moveAccount(from: Int, to: Int) {
        if (from !in accounts.indices || to !in accounts.indices) return
        val list = accounts.toMutableList()
        val item = list.removeAt(from)
        list.add(to, item)
        persist(list)
    }

    // ---------- PIN / ไบโอเมตริก ----------
    fun setPin(pin: String): Boolean {
        val ok = repo.setPin(pin)
        pinEnabled = repo.hasPin
        toast = if (ok) "ตั้ง PIN แล้ว" else "ตั้ง PIN ไม่สำเร็จ"
        return ok
    }

    fun removePin(pin: String): Boolean {
        val ok = repo.removePin(pin)
        pinEnabled = repo.hasPin
        toast = if (ok) "ปิด PIN แล้ว" else "PIN ไม่ถูกต้อง"
        return ok
    }

    fun prepareBiometricEnable(): Cipher? {
        val cipher = repo.prepareBiometricEnable()
        if (cipher == null) toast = "เครื่องนี้ยังไม่ได้ลงทะเบียนไบโอเมตริก"
        return cipher
    }

    fun completeBiometricEnable(cipher: Cipher): Boolean {
        val ok = repo.completeBiometricEnable(cipher)
        biometricEnabled = repo.biometricEnabled
        toast = if (ok) "เปิดปลดล็อกด้วยไบโอเมตริกแล้ว" else "เปิดไบโอเมตริกไม่สำเร็จ"
        return ok
    }

    fun disableBiometric() {
        repo.disableBiometric()
        biometricEnabled = false
        toast = "ปิดไบโอเมตริกแล้ว"
    }

    // ---------- ตัวสร้าง ----------
    fun generatePassword() {
        pwResult = Crypto.password(pwLength, pwSymbols, pwNoAmbiguous)
        pwRevision++
    }

    fun generateAdmin() {
        adminResult = Crypto.adminValues()
    }

    // ---------- ค่าตั้ง ----------
    fun updateSettings(block: (AppSettings) -> AppSettings) {
        val next = AppSettings.clean(block(settings))
        settings = next
        settingsRepo.save(next)
    }

    // ---------- AI ----------
    fun updateAiModel(model: String) {
        aiModel = model
        aiProvider = AiClient.providerForModel(model)
        if (settings.rememberModel) updateSettings { it.copy(lastModel = model) }
    }

    fun refreshModels() {
        if (aiBusy) return
        aiBusy = true
        aiError = null
        viewModelScope.launch {
            try {
                val list = withContext(Dispatchers.IO) { AiClient.listModels(aiProvider, aiApiKey) }
                aiModelList = if (list.isEmpty()) AiClient.MODEL_CHOICES else list
                toast = "พบ ${aiModelList.size} โมเดล"
            } catch (e: Exception) {
                aiError = e.message ?: "ดึงรายการโมเดลไม่สำเร็จ"
            } finally {
                aiBusy = false
            }
        }
    }

    fun sendAi() {
        val text = aiInput.trim()
        if (text.isEmpty() || aiBusy) return
        aiInput = ""
        aiError = null
        aiMessages = aiMessages + AiClient.ChatMessage("user", text)
        aiBusy = true
        val history = listOf(AiClient.ChatMessage("system", AiClient.SYSTEM_PROMPT)) + aiMessages
        val model = aiModel
        val provider = aiProvider
        val key = aiApiKey
        viewModelScope.launch {
            try {
                val reply = withContext(Dispatchers.IO) { AiClient.chat(history, key, model, provider) }
                val processedReply = processAiAgentAction(reply)
                aiMessages = aiMessages + AiClient.ChatMessage("assistant", processedReply)
            } catch (e: Exception) {
                aiError = e.message ?: "เชื่อมต่อ AI ไม่สำเร็จ"
            } finally {
                aiBusy = false
            }
        }
    }

    private fun processAiAgentAction(reply: String): String {
        val start = reply.indexOf("{\"action\"")
        if (start == -1) return reply
        val end = reply.lastIndexOf("}")
        if (end <= start) return reply
        val jsonStr = reply.substring(start, end + 1)

        return runCatching {
            val obj = JSONObject(jsonStr)
            val action = obj.optString("action")
            when (action) {
                "generate_password" -> {
                    val len = obj.optInt("length", 20).coerceIn(8, 128)
                    val symbols = obj.optBoolean("symbols", true)
                    val noAmbiguous = obj.optBoolean("noAmbiguous", false)
                    val generated = Crypto.password(len, symbols, noAmbiguous)
                    pwLength = len
                    pwSymbols = symbols
                    pwNoAmbiguous = noAmbiguous
                    pwResult = generated
                    pwRevision++
                    reply.replace(jsonStr, "").trim() + "\n\n[AI Agent ได้สร้างรหัสผ่านให้แล้ว: ${generated.value} (${generated.entropyBits.toInt()} บิต)]"
                }
                "add_account" -> {
                    val issuer = obj.optString("issuer", "Unknown")
                    val accountName = obj.optString("account", "")
                    val secret = obj.optString("secret", "").replace(" ", "").uppercase()
                    if (secret.isBlank()) {
                        reply + "\n\n[ไม่สามารถเพิ่มบัญชีได้ เนื่องจาก Secret ว่างเปล่า]"
                    } else {
                        val newAcc = TotpAccount(issuer = issuer, account = accountName, secret = secret)
                        addAccount(newAcc)
                        reply.replace(jsonStr, "").trim() + "\n\n[AI Agent ได้เพิ่มบัญชี 2FA '$issuer ($accountName)' ลงใน Vault สำเร็จ]"
                    }
                }
                "list_accounts" -> {
                    val accList = accounts.joinToString("\n") { "- ${it.title} (${it.account})" }
                    val summary = if (accList.isEmpty()) "ไม่มีบัญชีใน Vault" else accList
                    reply.replace(jsonStr, "").trim() + "\n\n[บัญชี 2FA ใน Vault ของคุณ:]\n$summary"
                }
                else -> reply
            }
        }.getOrDefault(reply)
    }

    fun clearChat() {
        aiMessages = emptyList()
        aiError = null
    }

    // ---------- อื่น ๆ ----------
    fun showToast(text: String) {
        toast = text
    }

    fun consumeToast() {
        toast = null
    }

    fun wipeEverything() {
        runCatching { repo.wipeAll() }
        runCatching { repo.prepare() }
        accounts = emptyList()
        pinEnabled = false
        biometricEnabled = false
        aiMessages = emptyList()
        adminResult = null
        lockState = LockState.Unlocked
        toast = "ล้างข้อมูลทั้งหมดแล้ว"
    }

    fun exportVault(passphrase: String): ByteArray? = repo.exportEncryptedVault(passphrase)

    fun importVault(bytes: ByteArray, passphrase: String): Boolean {
        val ok = repo.importEncryptedVault(bytes, passphrase)
        if (ok) {
            accounts = repo.load().accounts
            toast = "กู้คืนข้อมูล Vault สำเร็จ"
        } else {
            toast = "รหัสผ่านไม่ถูกต้องหรือไฟล์ไม่ถูกต้อง"
        }
        return ok
    }
}
