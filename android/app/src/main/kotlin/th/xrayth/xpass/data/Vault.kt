package th.xrayth.xpass.data

import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

/** บัญชี TOTP หนึ่งรายการ (secret เก็บแบบ base32 ไม่มี padding) */
data class TotpAccount(
    val id: String = UUID.randomUUID().toString(),
    val issuer: String = "",
    val account: String = "",
    val secret: String = "",
    val digits: Int = 6,
    val period: Int = 30,
    val algorithm: String = "SHA1",
    val note: String = "",
    val createdAt: Long = System.currentTimeMillis(),
) {
    val title: String
        get() = issuer.ifBlank { account.ifBlank { "ไม่มีชื่อ" } }

    val subtitle: String
        get() = when {
            issuer.isBlank() && account.isBlank() -> "ไม่มีชื่อบัญชี"
            issuer.isBlank() -> account
            account.isBlank() -> issuer
            account == issuer -> ""
            else -> account
        }

    fun toJson(): JSONObject = JSONObject().apply {
        put("id", id)
        put("issuer", issuer)
        put("account", account)
        put("secret", secret)
        put("digits", digits)
        put("period", period)
        put("algorithm", algorithm)
        put("note", note)
        put("createdAt", createdAt)
    }

    companion object {
        fun fromJson(o: JSONObject): TotpAccount = TotpAccount(
            id = o.optString("id", UUID.randomUUID().toString()).ifBlank { UUID.randomUUID().toString() },
            issuer = o.optString("issuer", ""),
            account = o.optString("account", ""),
            secret = o.optString("secret", ""),
            digits = o.optInt("digits", 6).coerceIn(4, 10),
            period = o.optInt("period", 30).coerceIn(5, 300),
            algorithm = o.optString("algorithm", "SHA1").uppercase(),
            note = o.optString("note", ""),
            createdAt = o.optLong("createdAt", System.currentTimeMillis()),
        )
    }
}

data class VaultData(
    val accounts: List<TotpAccount> = emptyList(),
    val version: Int = 1,
) {
    fun toJson(): JSONObject = JSONObject().apply {
        put("version", version)
        put("accounts", JSONArray().apply { accounts.forEach { put(it.toJson()) } })
    }

    companion object {
        fun fromJson(o: JSONObject): VaultData {
            val arr = o.optJSONArray("accounts") ?: JSONArray()
            val list = ArrayList<TotpAccount>(arr.length())
            for (i in 0 until arr.length()) {
                arr.optJSONObject(i)?.let { list.add(TotpAccount.fromJson(it)) }
            }
            return VaultData(list, o.optInt("version", 1))
        }
    }
}
