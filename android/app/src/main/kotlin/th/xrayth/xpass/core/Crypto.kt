package th.xrayth.xpass.core

import java.net.URI
import java.net.URLDecoder
import java.security.SecureRandom
import java.util.Locale
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import kotlin.math.log2

/**
 * แกนคำนวณของ xpass (พอร์ตจาก xpass.py)
 * ใช้ SecureRandom ของระบบปฏิบัติการ — ไม่ใช้ Random ธรรมดา
 * ไม่มีการเชื่อมต่อเครือข่ายและไม่เขียนไฟล์ในไฟล์นี้
 */
object Crypto {

    const val LOWER = "abcdefghijklmnopqrstuvwxyz"
    const val UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    const val DIGITS = "0123456789"
    const val SYMBOLS = "!@#\$%^&*()-_=+[]{}:,.?"
    const val AMBIGUOUS = "Il1O0o"

    private const val B32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

    private val rng = SecureRandom()

    data class Generated(
        val value: String,
        val entropyBits: Double,
        val poolSize: Int,
    )

    // ---------- รหัสผ่าน ----------
    fun password(
        length: Int = 20,
        symbols: Boolean = true,
        noAmbiguous: Boolean = false,
    ): Generated {
        val len = length.coerceIn(8, 128)
        var classes = buildList {
            add(LOWER)
            add(UPPER)
            add(DIGITS)
            if (symbols) add(SYMBOLS)
        }
        if (noAmbiguous) {
            classes = classes.map { cls -> cls.filterNot { AMBIGUOUS.contains(it) } }
        }
        val pool = classes.joinToString("")
        check(pool.isNotEmpty()) { "pool ว่าง" }
        val entropy = len * log2(pool.length.toDouble())

        repeat(20_000) {
            val sb = StringBuilder(len)
            repeat(len) { sb.append(pool[rng.nextInt(pool.length)]) }
            val s = sb.toString()
            if (classes.all { cls -> s.any { ch -> cls.contains(ch) } }) {
                return Generated(s, entropy, pool.length)
            }
        }
        // แทบไม่เกิด — คืนค่าที่สุ่มได้ล่าสุดเพื่อไม่ให้ UI ค้าง
        val fallback = buildString { repeat(len) { append(pool[rng.nextInt(pool.length)]) } }
        return Generated(fallback, entropy, pool.length)
    }

    fun alnum(n: Int): String {
        val pool = LOWER + UPPER + DIGITS
        return buildString(n) { repeat(n) { append(pool[rng.nextInt(pool.length)]) } }
    }

    fun slug(n: Int = 24): String {
        val pool = LOWER + DIGITS
        return buildString(n) { repeat(n) { append(pool[rng.nextInt(pool.length)]) } }
    }

    fun randomBytes(n: Int): ByteArray = ByteArray(n).also { rng.nextBytes(it) }

    fun entropyLabel(bits: Double): String {
        val rounded = bits.toInt()
        val level = when {
            bits >= 100 -> "แข็งแรงมาก"
            bits >= 80 -> "แข็งแรง"
            bits >= 60 -> "พอใช้"
            else -> "อ่อน"
        }
        return "~$rounded บิต · $level"
    }

    // ---------- Base32 (RFC 4648, ไม่มี padding) ----------
    fun base32Encode(data: ByteArray): String {
        val sb = StringBuilder((data.size * 8 + 4) / 5)
        var buffer = 0
        var bitsLeft = 0
        for (b in data) {
            buffer = (buffer shl 8) or (b.toInt() and 0xFF)
            bitsLeft += 8
            while (bitsLeft >= 5) {
                sb.append(B32[(buffer shr (bitsLeft - 5)) and 0x1F])
                bitsLeft -= 5
            }
        }
        if (bitsLeft > 0) {
            sb.append(B32[(buffer shl (5 - bitsLeft)) and 0x1F])
        }
        return sb.toString()
    }

    fun base32Decode(text: String): ByteArray? {
        val clean = text
            .filterNot { it.isWhitespace() || it == '-' || it == '=' }
            .uppercase(Locale.ROOT)
        if (clean.isEmpty()) return null
        var buffer = 0
        var bitsLeft = 0
        val out = java.io.ByteArrayOutputStream(clean.length * 5 / 8 + 1)
        for (c in clean) {
            val v = B32.indexOf(c)
            if (v < 0) return null
            buffer = (buffer shl 5) or v
            bitsLeft += 5
            if (bitsLeft >= 8) {
                out.write((buffer shr (bitsLeft - 8)) and 0xFF)
                bitsLeft -= 8
            }
        }
        val bytes = out.toByteArray()
        return if (bytes.isEmpty()) null else bytes
    }

    // ---------- TOTP (RFC 6238) ----------
    fun totp(
        key: ByteArray,
        step: Long,
        digits: Int = 6,
        algorithm: String = "SHA1",
    ): String {
        val macName = when (algorithm.uppercase(Locale.ROOT)) {
            "SHA256" -> "HmacSHA256"
            "SHA512" -> "HmacSHA512"
            else -> "HmacSHA1"
        }
        val counter = java.nio.ByteBuffer.allocate(8).putLong(step).array()
        val mac = Mac.getInstance(macName).apply { init(SecretKeySpec(key, macName)) }
        val hash = mac.doFinal(counter)
        val offset = hash[hash.size - 1].toInt() and 0x0F
        val binary =
            ((hash[offset].toInt() and 0x7F) shl 24) or
                ((hash[offset + 1].toInt() and 0xFF) shl 16) or
                ((hash[offset + 2].toInt() and 0xFF) shl 8) or
                (hash[offset + 3].toInt() and 0xFF)
        val mod = pow10(digits.coerceIn(4, 10))
        return (binary.toLong() % mod).toString().padStart(digits, '0')
    }

    fun currentTotp(secret: String, digits: Int = 6, period: Int = 30, algorithm: String = "SHA1"): String? {
        val key = base32Decode(secret) ?: return null
        val step = System.currentTimeMillis() / 1000L / period.coerceAtLeast(1)
        return runCatching { totp(key, step, digits, algorithm) }.getOrNull()
    }

    fun secondsRemaining(period: Int = 30): Int {
        val p = period.coerceAtLeast(1)
        return (p - (System.currentTimeMillis() / 1000L % p)).toInt()
    }

    private fun pow10(n: Int): Long {
        var v = 1L
        repeat(n) { v *= 10 }
        return v
    }

    // ---------- otpauth:// ----------
    fun otpauthUri(secret: String, issuer: String, account: String): String {
        val enc = { s: String -> java.net.URLEncoder.encode(s, "UTF-8").replace("+", "%20") }
        return "otpauth://totp/${enc(issuer)}:${enc(account)}" +
            "?secret=$secret&issuer=${enc(issuer)}&algorithm=SHA1&digits=6&period=30"
    }

    data class OtpAuth(
        val secret: String,
        val issuer: String,
        val account: String,
        val digits: Int = 6,
        val period: Int = 30,
        val algorithm: String = "SHA1",
    )

    /** รองรับทั้งลิงก์ otpauth:// และ secret base32 เปล่า ๆ */
    fun parseOtpInput(raw: String): OtpAuth? {
        val text = raw.trim()
        if (text.isEmpty()) return null
        if (!text.startsWith("otpauth://", ignoreCase = true)) {
            val secret = base32Decode(text)?.let { base32Encode(it) } ?: return null
            return OtpAuth(secret = secret, issuer = "", account = "")
        }
        return runCatching {
            val uri = URI(text)
            if (!uri.host.equals("totp", ignoreCase = true)) return null
            val params = HashMap<String, String>()
            uri.rawQuery?.split('&')?.forEach { pair ->
                val idx = pair.indexOf('=')
                if (idx > 0) {
                    val k = pair.substring(0, idx)
                    val v = URLDecoder.decode(pair.substring(idx + 1).replace("+", "%2B"), "UTF-8")
                    params[k.lowercase(Locale.ROOT)] = v
                }
            }
            val secretRaw = params["secret"] ?: return null
            val secret = base32Decode(secretRaw)?.let { base32Encode(it) } ?: return null

            var label = uri.path.orEmpty().trimStart('/')
            label = URLDecoder.decode(label.replace("+", "%2B"), "UTF-8")
            var issuer = params["issuer"].orEmpty()
            var account = label
            if (label.contains(':')) {
                val parts = label.split(':', limit = 2)
                if (issuer.isBlank()) issuer = parts[0].trim()
                account = parts[1].trim()
            }
            OtpAuth(
                secret = secret,
                issuer = issuer.trim(),
                account = account.trim(),
                digits = params["digits"]?.toIntOrNull()?.coerceIn(4, 10) ?: 6,
                period = params["period"]?.toIntOrNull()?.coerceIn(5, 300) ?: 30,
                algorithm = params["algorithm"]?.uppercase(Locale.ROOT) ?: "SHA1",
            )
        }.getOrNull()
    }

    /** ค่าที่ใช้ตั้ง Cloudflare Worker (เหมือน `xpass.py admin`) */
    data class AdminValues(
        val token: String,
        val secret: String,
        val page: String,
        val uri: String,
        val code: String,
    )

    fun adminValues(issuer: String = "XRay Admin", account: String = "admin"): AdminValues {
        val token = alnum(40)
        val secret = base32Encode(randomBytes(20))
        val page = "a-${slug(24)}.html"
        val uri = otpauthUri(secret, issuer, account)
        val code = runCatching {
            val key = base32Decode(secret)!!
            val step = System.currentTimeMillis() / 1000L / 30
            totp(key, step)
        }.getOrDefault("")
        return AdminValues(token, secret, page, uri, code)
    }
}
