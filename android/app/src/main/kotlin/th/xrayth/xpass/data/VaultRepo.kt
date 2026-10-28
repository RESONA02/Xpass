package th.xrayth.xpass.data

import android.content.Context
import android.util.Base64
import org.json.JSONObject
import java.io.File
import javax.crypto.Cipher

/**
 * ที่เก็บ vault ที่เข้ารหัสแล้ว
 *
 * ไฟล์: filesDir/vault.enc (JSON ที่เข้ารหัส AES-256-GCM ด้วย master key)
 * pref: xpass_vault (เก็บเฉพาะ "กุญแจที่ถูกห่อแล้ว" ไม่มีข้อมูลลับตรง ๆ)
 */
class VaultRepo(context: Context) {

    private val appContext = context.applicationContext
    private val prefs = appContext.getSharedPreferences("xpass_vault", Context.MODE_PRIVATE)
    private val vaultFile = File(appContext.filesDir, "vault.enc")

    private var masterKey: ByteArray? = null

    val isUnlocked: Boolean get() = masterKey != null
    val hasPin: Boolean get() = prefs.contains(KEY_PIN_WRAP)
    val biometricEnabled: Boolean get() = prefs.getBoolean(KEY_BIO_ON, false)
    val biometricReady: Boolean get() = prefs.contains(KEY_BIO_WRAP) && VaultCrypto.hasBiometricKey()

    /**
     * เตรียมกุญแจครั้งแรก แล้วปลดล็อกอัตโนมัติถ้าไม่มี PIN
     * @return true ถ้าปลดล็อกสำเร็จ (ไม่ต้องแสดงหน้า Lock)
     */
    fun prepare(): Boolean {
        if (!prefs.contains(KEY_DEVICE_WRAP)) {
            VaultCrypto.ensureDeviceKey()
            val master = VaultCrypto.randomBytes(32)
            val wrapped = VaultCrypto.encryptWithDeviceKey(master)
            prefs.edit().putString(KEY_DEVICE_WRAP, b64(wrapped)).apply()
        }
        if (hasPin) return false
        return unlockWithDevice()
    }

    fun unlockWithDevice(): Boolean = runCatching {
        val blob = prefs.getString(KEY_DEVICE_WRAP, null) ?: return false
        masterKey = VaultCrypto.decryptWithDeviceKey(unb64(blob))
        true
    }.getOrDefault(false)

    fun unlockWithPin(pin: String): Boolean = runCatching {
        val salt = prefs.getString(KEY_PIN_SALT, null) ?: return false
        val blob = prefs.getString(KEY_PIN_WRAP, null) ?: return false
        val iterations = prefs.getInt(KEY_PIN_ITER, VaultCrypto.PBKDF2_ITERATIONS)
        val key = VaultCrypto.derivePinKey(pin, unb64(salt), iterations)
        masterKey = VaultCrypto.aesDecrypt(key, unb64(blob))
        true
    }.getOrDefault(false)

    fun setPin(pin: String): Boolean {
        val master = masterKey ?: return false
        return runCatching {
            val salt = VaultCrypto.randomBytes(16)
            val key = VaultCrypto.derivePinKey(pin, salt)
            val blob = VaultCrypto.aesEncrypt(key, master)
            prefs.edit()
                .putString(KEY_PIN_SALT, b64(salt))
                .putString(KEY_PIN_WRAP, b64(blob))
                .putInt(KEY_PIN_ITER, VaultCrypto.PBKDF2_ITERATIONS)
                .apply()
            true
        }.getOrDefault(false)
    }

    fun removePin(pin: String): Boolean {
        if (!unlockWithPin(pin)) return false
        prefs.edit().remove(KEY_PIN_SALT).remove(KEY_PIN_WRAP).remove(KEY_PIN_ITER).apply()
        return true
    }

    // ---------- ไบโอเมตริก ----------
    fun prepareBiometricEnable(): Cipher? = runCatching {
        VaultCrypto.createBiometricKey()
        VaultCrypto.biometricEncryptCipher()
    }.getOrNull()

    fun completeBiometricEnable(cipher: Cipher): Boolean {
        val master = masterKey ?: return false
        return runCatching {
            val blob = cipher.iv + cipher.doFinal(master)
            prefs.edit().putString(KEY_BIO_WRAP, b64(blob)).putBoolean(KEY_BIO_ON, true).apply()
            true
        }.getOrDefault(false)
    }

    fun prepareBiometricUnlock(): Cipher? = runCatching {
        val blob = prefs.getString(KEY_BIO_WRAP, null) ?: return null
        VaultCrypto.biometricDecryptCipher(unb64(blob))
    }.getOrNull()

    fun completeBiometricUnlock(cipher: Cipher): Boolean = runCatching {
        masterKey = cipher.doFinal()
        true
    }.getOrDefault(false)

    fun disableBiometric() {
        VaultCrypto.deleteBiometricKey()
        prefs.edit().remove(KEY_BIO_WRAP).putBoolean(KEY_BIO_ON, false).apply()
    }

    // ---------- vault ----------
    fun load(): VaultData {
        val key = masterKey ?: return VaultData()
        if (!vaultFile.exists()) return VaultData()
        return runCatching {
            val plain = VaultCrypto.aesDecrypt(key, vaultFile.readBytes())
            VaultData.fromJson(JSONObject(String(plain, Charsets.UTF_8)))
        }.getOrDefault(VaultData())
    }

    fun save(data: VaultData): Boolean {
        val key = masterKey ?: return false
        return runCatching {
            val plain = data.toJson().toString().toByteArray(Charsets.UTF_8)
            val enc = VaultCrypto.aesEncrypt(key, plain)
            val tmp = File(appContext.filesDir, "vault.enc.tmp")
            tmp.writeBytes(enc)
            if (vaultFile.exists()) vaultFile.delete()
            tmp.renameTo(vaultFile)
        }.getOrDefault(false)
    }

    fun lock() {
        masterKey?.fill(0)
        masterKey = null
    }

    fun exportEncryptedVault(passphrase: String): ByteArray? {
        val key = masterKey ?: return null
        if (!vaultFile.exists()) return null
        return runCatching {
            val plain = VaultCrypto.aesDecrypt(key, vaultFile.readBytes())
            val salt = VaultCrypto.randomBytes(16)
            val exportKey = VaultCrypto.derivePinKey(passphrase, salt)
            val encryptedBackup = VaultCrypto.aesEncrypt(exportKey, plain)
            val json = JSONObject().apply {
                put("version", 1)
                put("salt", b64(salt))
                put("payload", b64(encryptedBackup))
            }
            json.toString().toByteArray(Charsets.UTF_8)
        }.getOrNull()
    }

    fun importEncryptedVault(backupBytes: ByteArray, passphrase: String): Boolean {
        val key = masterKey ?: return false
        return runCatching {
            val jsonStr = String(backupBytes, Charsets.UTF_8)
            val json = JSONObject(jsonStr)
            val salt = unb64(json.getString("salt"))
            val payload = unb64(json.getString("payload"))
            val importKey = VaultCrypto.derivePinKey(passphrase, salt)
            val decryptedPlain = VaultCrypto.aesDecrypt(importKey, payload)
            
            // Verify valid VaultData JSON
            VaultData.fromJson(JSONObject(String(decryptedPlain, Charsets.UTF_8)))

            val enc = VaultCrypto.aesEncrypt(key, decryptedPlain)
            val tmp = File(appContext.filesDir, "vault.enc.tmp")
            tmp.writeBytes(enc)
            if (vaultFile.exists()) vaultFile.delete()
            tmp.renameTo(vaultFile)
            true
        }.getOrDefault(false)
    }

    /** ล้างทุกอย่าง (vault + PIN + ไบโอเมตริก) — ใช้ในหน้า "ล้างข้อมูลทั้งหมด" */
    fun wipeAll() {
        lock()
        runCatching { vaultFile.delete() }
        runCatching { File(appContext.filesDir, "vault.enc.tmp").delete() }
        VaultCrypto.deleteBiometricKey()
        prefs.edit().clear().apply()
    }

    private fun b64(bytes: ByteArray): String = Base64.encodeToString(bytes, Base64.NO_WRAP)

    private fun unb64(text: String): ByteArray = Base64.decode(text, Base64.NO_WRAP)

    private companion object {
        const val KEY_DEVICE_WRAP = "device_wrap"
        const val KEY_PIN_SALT = "pin_salt"
        const val KEY_PIN_WRAP = "pin_wrap"
        const val KEY_PIN_ITER = "pin_iter"
        const val KEY_BIO_WRAP = "bio_wrap"
        const val KEY_BIO_ON = "bio_on"
    }
}
