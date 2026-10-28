package th.xrayth.xpass.ui

import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import javax.crypto.Cipher

/** แสดง BiometricPrompt แล้วส่ง Cipher ที่ผ่านการยืนยันตัวตนกลับมา */
fun showBiometricPrompt(
    activity: FragmentActivity,
    cipher: Cipher,
    title: String,
    subtitle: String,
    onSuccess: (Cipher) -> Unit,
    onError: (String) -> Unit,
) {
    val manager = BiometricManager.from(activity)
    if (manager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG) !=
        BiometricManager.BIOMETRIC_SUCCESS
    ) {
        onError("เครื่องนี้ยังไม่ได้ลงทะเบียนลายนิ้วมือหรือใบหน้า")
        return
    }

    val executor = ContextCompat.getMainExecutor(activity)
    val prompt = BiometricPrompt(
        activity,
        executor,
        object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                val c = result.cryptoObject?.cipher
                if (c != null) onSuccess(c) else onError("ไม่ได้รับกุญแจจากไบโอเมตริก")
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                if (errorCode != BiometricPrompt.ERROR_USER_CANCELED &&
                    errorCode != BiometricPrompt.ERROR_NEGATIVE_BUTTON &&
                    errorCode != BiometricPrompt.ERROR_CANCELED
                ) {
                    onError(errString.toString())
                }
            }
        },
    )

    val info = BiometricPrompt.PromptInfo.Builder()
        .setTitle(title)
        .setSubtitle(subtitle)
        .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
        .setNegativeButtonText("ยกเลิก")
        .build()

    prompt.authenticate(info, BiometricPrompt.CryptoObject(cipher))
}

fun canUseBiometric(activity: FragmentActivity): Boolean =
    BiometricManager.from(activity).canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG) ==
        BiometricManager.BIOMETRIC_SUCCESS
