package th.xrayth.xpass.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** ทดสอบแกนคำนวณด้วยเวกเตอร์เดียวกับ `python xpass.py selftest` */
class CryptoTest {

    private val rfcKey = "12345678901234567890".toByteArray(Charsets.US_ASCII)

    @Test
    fun totpMatchesRfc6238() {
        val vectors = mapOf(
            59L to "287082",
            1111111109L to "081804",
            1111111111L to "050471",
            1234567890L to "005924",
            2000000000L to "279037",
        )
        vectors.forEach { (time, expected) ->
            assertEquals("t=$time", expected, Crypto.totp(rfcKey, time / 30))
        }
    }

    @Test
    fun base32RoundTrip() {
        assertEquals("MZXW6YTBOI", Crypto.base32Encode("foobar".toByteArray()))
        assertEquals("foobar", String(Crypto.base32Decode("MZXW6YTBOI======")!!))
        assertEquals("foobar", String(Crypto.base32Decode("mzxw 6ytb oi")!!))
        assertEquals(null, Crypto.base32Decode("not-base32!"))
    }

    @Test
    fun passwordHasEveryCharacterClass() {
        val result = Crypto.password(16, symbols = true, noAmbiguous = true)
        assertEquals(16, result.value.length)
        assertTrue(result.value.any { it in Crypto.LOWER })
        assertTrue(result.value.any { it in Crypto.UPPER })
        assertTrue(result.value.any { it in Crypto.DIGITS })
        assertTrue(result.value.any { it in Crypto.SYMBOLS })
        assertFalse(result.value.any { it in Crypto.AMBIGUOUS })
        assertTrue(result.entropyBits > 60)
    }

    @Test
    fun passwordClampsLength() {
        assertEquals(8, Crypto.password(1).value.length)
        assertEquals(128, Crypto.password(500).value.length)
    }

    @Test
    fun slugUsesLowerAndDigits() {
        val slug = Crypto.slug(24)
        assertEquals(24, slug.length)
        assertTrue(slug.all { it in Crypto.LOWER || it in Crypto.DIGITS })
    }

    @Test
    fun parseOtpauthUri() {
        val parsed = Crypto.parseOtpInput(
            "otpauth://totp/GitHub:user%40example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub",
        )
        assertNotNull(parsed)
        assertEquals("GitHub", parsed!!.issuer)
        assertEquals("user@example.com", parsed.account)
        assertEquals("JBSWY3DPEHPK3PXP", parsed.secret)
        assertEquals(6, parsed.digits)
        assertEquals(30, parsed.period)
    }

    @Test
    fun parsePlainSecret() {
        val parsed = Crypto.parseOtpInput("JBSWY3DPEHPK3PXP")
        assertNotNull(parsed)
        assertEquals("JBSWY3DPEHPK3PXP", parsed!!.secret)
    }

    @Test
    fun rejectInvalidSecret() {
        assertEquals(null, Crypto.parseOtpInput("hello world!"))
    }

    @Test
    fun adminValuesAreSane() {
        val admin = Crypto.adminValues()
        assertEquals(40, admin.token.length)
        assertTrue(admin.page.startsWith("a-") && admin.page.endsWith(".html"))
        assertEquals(6, admin.code.length)
        assertNotNull(Crypto.base32Decode(admin.secret))
        assertTrue(admin.uri.startsWith("otpauth://totp/"))
    }
}
