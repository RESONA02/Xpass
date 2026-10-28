package th.xrayth.xpass.data

import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyStore
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec

/**
 * ชั้นเข้ารหัสของ vault
 *
 * - กุญแจหลัก (master) 32 ไบต์ สุ่มด้วย SecureRandom เก็บในหน่วยความจำเท่านั้น
 * - master ถูก "ห่อ" (wrap) ด้วย Android Keystore (AES-256-GCM) เสมอ → เปิดแอปได้ทันที
 * - ถ้าผู้ใช้ตั้ง PIN: master ถูกห่ออีกชั้นด้วย PBKDF2-HMAC-SHA256 → ต้องใส่ PIN
 * - ถ้าเปิดไบโอเมตริก: master ถูกห่ออีกชั้นด้วย Keystore key ที่บังคับยืนยันตัวตน
 *
 * ไฟล์ vault.enc เก็บ JSON ที่เข้ารหัสด้วย master (AES-256-GCM) — อ่านออกได้เฉพาะเครื่องนี้
 */
object VaultCrypto {

    private const val KEYSTORE = "AndroidKeyStore"
    const val DEVICE_ALIAS = "xpass_device_key"
    const val BIO_ALIAS = "xpass_bio_key"

    const val PBKDF2_ITERATIONS = 120_000
    private const val GCM_TAG_BITS = 128
    private const val IV_LEN = 12

    private val rng = SecureRandom()

    // ---------- Keystore ----------
    private fun keyStore(): KeyStore =
        KeyStore.getInstance(KEYSTORE).apply { load(null) }

    fun ensureDeviceKey() {
        val ks = keyStore()
        if (ks.containsAlias(DEVICE_ALIAS)) return
        val gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, KEYSTORE)
        gen.init(
            KeyGenParameterSpec.Builder(
                DEVICE_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build(),
        )
        gen.generateKey()
    }

    private fun deviceKey(): SecretKey {
        ensureDeviceKey()
        val entry = keyStore().getEntry(DEVICE_ALIAS, null) as KeyStore.SecretKeyEntry
        return entry.secretKey
    }

    fun encryptWithDeviceKey(plain: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, deviceKey())
        return cipher.iv + cipher.doFinal(plain)
    }

    fun decryptWithDeviceKey(blob: ByteArray): ByteArray {
        val iv = blob.copyOfRange(0, IV_LEN)
        val body = blob.copyOfRange(IV_LEN, blob.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, deviceKey(), GCMParameterSpec(GCM_TAG_BITS, iv))
        return cipher.doFinal(body)
    }

    fun hasBiometricKey(): Boolean = runCatching { keyStore().containsAlias(BIO_ALIAS) }.getOrDefault(false)

    fun deleteBiometricKey() {
        runCatching {
            val ks = keyStore()
            if (ks.containsAlias(BIO_ALIAS)) ks.deleteEntry(BIO_ALIAS)
        }
    }

    /** สร้างกุญแจไบโอเมตริกใหม่ (ทำให้ blob เดิมใช้ไม่ได้ — ต้อง wrap ใหม่ทุกครั้ง) */
    fun createBiometricKey() {
        deleteBiometricKey()
        val gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, KEYSTORE)
        val builder = KeyGenParameterSpec.Builder(
            BIO_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .setUserAuthenticationRequired(true)
            .setInvalidatedByBiometricEnrollment(false)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            builder.setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG)
        } else {
            @Suppress("DEPRECATION")
            builder.setUserAuthenticationValidityDurationSeconds(-1)
        }
        gen.init(builder.build())
        gen.generateKey()
    }

    private fun biometricKey(): SecretKey {
        val entry = keyStore().getEntry(BIO_ALIAS, null) as KeyStore.SecretKeyEntry
        return entry.secretKey
    }

    /** Cipher สำหรับ "ห่อ" master ด้วยไบโอเมตริก — ต้องผ่าน BiometricPrompt ก่อน doFinal */
    fun biometricEncryptCipher(): Cipher {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, biometricKey())
        return cipher
    }

    /** Cipher สำหรับ "ถอด" master ด้วยไบโอเมตริก */
    fun biometricDecryptCipher(blob: ByteArray): Cipher {
        val iv = blob.copyOfRange(0, IV_LEN)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, biometricKey(), GCMParameterSpec(GCM_TAG_BITS, iv))
        return cipher
    }

    // ---------- PIN ----------
    fun derivePinKey(pin: String, salt: ByteArray, iterations: Int = PBKDF2_ITERATIONS): ByteArray {
        val spec = PBEKeySpec(pin.toCharArray(), salt, iterations, 256)
        return try {
            SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).encoded
        } finally {
            spec.clearPassword()
        }
    }

    // ---------- AES-GCM ด้วยกุญแจดิบ ----------
    fun aesEncrypt(key: ByteArray, plain: ByteArray): ByteArray {
        val iv = ByteArray(IV_LEN).also { rng.nextBytes(it) }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(GCM_TAG_BITS, iv))
        return iv + cipher.doFinal(plain)
    }

    fun aesDecrypt(key: ByteArray, blob: ByteArray): ByteArray {
        require(blob.size > IV_LEN) { "ข้อมูลสั้นเกินไป" }
        val iv = blob.copyOfRange(0, IV_LEN)
        val body = blob.copyOfRange(IV_LEN, blob.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(GCM_TAG_BITS, iv))
        return cipher.doFinal(body)
    }

    fun randomBytes(n: Int): ByteArray = ByteArray(n).also { rng.nextBytes(it) }
}
