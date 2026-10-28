package th.xrayth.xpass.ai

import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
import java.net.URLEncoder
import java.util.Locale

/**
 * ไคลเอนต์ AI (พอร์ตจาก xpass_ai.py)
 * รองรับ OpenAI Chat Completions และ Google Gemini generateContent
 * ใช้ HttpURLConnection ของ Android — ไม่ต้องมี SDK
 *
 * API key อยู่ในหน่วยความจำเท่านั้น ไม่ถูกเขียนลงดิสก์
 */
object AiClient {

    const val OPENAI = "openai"
    const val GEMINI = "gemini"

    const val OPENAI_BASE = "https://api.openai.com/v1"
    const val GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
    const val DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
    const val DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
    const val TIMEOUT_MS = 60_000

    val MODEL_CHOICES = listOf(
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.1-flash-lite",
        "gemini-4-argon",
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
    )

    const val SYSTEM_PROMPT =
        "คุณคือ AI Agent ผู้ช่วยอัจฉริยะภายในแอป xpass ที่สามารถควบคุมและสั่งการแอปแทนผู้ใช้ได้ " +
            "ตอบเป็นภาษาไทย กระชับ ตรงประเด็น และใช้ข้อความธรรมดา " +
            "หากผู้ใช้ต้องการให้คุณทำรายการในแอป ให้คุณตอบกลับโดยแนบ JSON block ในรูปแบบนี้:\n" +
            "1. สร้างรหัสผ่าน: {\"action\": \"generate_password\", \"length\": 16, \"symbols\": true, \"noAmbiguous\": false}\n" +
            "2. เพิ่มบัญชี 2FA: {\"action\": \"add_account\", \"issuer\": \"GitHub\", \"account\": \"user@gmail.com\", \"secret\": \"JBSWY3DPEHPK3PXP\"}\n" +
            "3. ดูรายการบัญชี 2FA: {\"action\": \"list_accounts\"}\n" +
            "ห้ามขอให้ผู้ใช้ส่งรหัสผ่าน TOTP secret จริง หรือ API key ในแชท " +
            "ถ้าผู้ใช้ส่งข้อมูลที่ดูเหมือนความลับ ให้เตือนให้ลบทันทีและไม่ทวนซ้ำ"

    class AiException(message: String) : Exception(message)

    data class ChatMessage(val role: String, val content: String)

    fun providerForModel(model: String): String {
        val name = model.trim().lowercase(Locale.ROOT)
        return if (name.startsWith("gemini") || name.startsWith("models/gemini")) GEMINI else OPENAI
    }

    fun providerLabel(provider: String): String = when (provider) {
        GEMINI -> "Google Gemini"
        else -> "OpenAI"
    }

    fun defaultModel(provider: String): String = when (provider) {
        GEMINI -> DEFAULT_GEMINI_MODEL
        else -> DEFAULT_OPENAI_MODEL
    }

    fun baseUrl(provider: String): String = when (provider) {
        GEMINI -> GEMINI_BASE
        else -> OPENAI_BASE
    }

    // ---------- HTTP ----------
    private fun requestJson(
        url: String,
        method: String,
        body: String?,
        headers: Map<String, String>,
        provider: String,
        model: String,
        timeoutMs: Int = TIMEOUT_MS,
    ): JSONObject {
        val conn = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = timeoutMs
            readTimeout = timeoutMs
            instanceFollowRedirects = true
            setRequestProperty("User-Agent", "xpass-android/1.0")
            if (body != null) setRequestProperty("Content-Type", "application/json; charset=utf-8")
            headers.forEach { (k, v) -> setRequestProperty(k, v) }
            if (body != null) doOutput = true
        }

        try {
            if (body != null) {
                conn.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            }
            val code = conn.responseCode
            if (code >= 400) {
                val detail = runCatching {
                    (conn.errorStream ?: conn.inputStream)?.bufferedReader()?.use { it.readText() }
                }.getOrNull().orEmpty()
                throw AiException(httpMessage(code, detail, provider, model))
            }
            val text = conn.inputStream.bufferedReader().use { it.readText() }
            return runCatching { JSONObject(text) }.getOrElse {
                throw AiException("อ่านคำตอบจากเซิร์ฟเวอร์ไม่ได้ (ไม่ใช่ JSON)")
            }
        } catch (e: SocketTimeoutException) {
            throw AiException("หมดเวลาเชื่อมต่อ (${timeoutMs / 1000} วินาที) — ตรวจอินเทอร์เน็ตแล้วลองใหม่")
        } catch (e: AiException) {
            throw e
        } catch (e: IOException) {
            throw AiException("เชื่อมต่ออินเทอร์เน็ตไม่ได้: ${e.message ?: e.javaClass.simpleName}")
        } finally {
            conn.disconnect()
        }
    }

    private fun httpDetail(raw: String): String {
        if (raw.isBlank()) return ""
        return runCatching {
            val obj = JSONObject(raw)
            val err = obj.optJSONObject("error")
            val msg = err?.optString("message").orEmpty().ifBlank { obj.optString("message") }
            (msg.ifBlank { raw }).trim().take(300)
        }.getOrDefault(raw.trim().take(300))
    }

    private fun suggestedModel(detail: String, current: String): String {
        val cur = current.removePrefix("models/")
        val regex = Regex("models/([A-Za-z0-9][A-Za-z0-9._-]*)")
        return regex.findAll(detail).map { it.groupValues[1] }.firstOrNull { it != cur }.orEmpty()
    }

    private fun httpMessage(code: Int, raw: String, provider: String, model: String): String {
        val label = providerLabel(provider)
        var message = when (code) {
            400 -> "$label: คำขอไม่ถูกต้อง — อาจเป็นชื่อโมเดล รูปแบบข้อความ หรือ API key (400)"
            401 -> "API key ไม่ถูกต้องหรือถูกยกเลิกแล้ว (401)"
            403 -> "คีย์นี้ไม่มีสิทธิ์ใช้โมเดลที่เลือก (403)"
            404 -> "$label: ไม่พบ endpoint หรือโมเดลที่เลือก (404)"
            429 -> "ติด rate limit หรือโควตาหมด — ลองใหม่ภายหลัง (429)"
            500, 502, 503 -> "$label ขัดข้องหรือไม่พร้อมให้บริการ — ลองใหม่ภายหลัง ($code)"
            else -> "$label ตอบกลับ HTTP $code"
        }
        val detail = httpDetail(raw)
        if (code == 404) {
            message += " — ตรวจชื่อโมเดล “$model”"
            if (provider == GEMINI) {
                val suggestion = suggestedModel(detail, model)
                if (suggestion.isNotBlank()) message += " — แนะนำ “$suggestion”"
                message += " (โมเดลรุ่นเก่าอาจถูกปิดสำหรับผู้ใช้ใหม่ — กด “รีเฟรช” เพื่อดูรุ่นที่คีย์นี้ใช้ได้)"
            }
        }
        if (detail.isNotBlank()) message += ": $detail"
        return message
    }

    // ---------- chat ----------
    fun chat(
        messages: List<ChatMessage>,
        apiKey: String,
        model: String,
        provider: String = "",
        temperature: Double = 0.7,
    ): String {
        if (apiKey.isBlank()) {
            val p = if (provider.isBlank()) OPENAI else provider
            throw AiException("ยังไม่มี API key ของ ${providerLabel(p)} — ใส่คีย์ในช่องด้านบนก่อน")
        }
        if (messages.isEmpty()) throw AiException("ยังไม่มีข้อความที่จะส่ง")

        val chosenModel = model.trim().ifBlank { DEFAULT_OPENAI_MODEL }
        val p = if (provider in listOf(OPENAI, GEMINI)) provider else providerForModel(chosenModel)
        val temp = temperature.coerceIn(0.0, 2.0)

        val content = if (p == GEMINI) {
            chatGemini(messages, apiKey.trim(), chosenModel, temp)
        } else {
            chatOpenAi(messages, apiKey.trim(), chosenModel, temp)
        }
        if (content.isBlank()) throw AiException("AI ไม่ได้ส่งคำตอบกลับมา — ลองใหม่อีกครั้ง")
        return content
    }

    private fun chatOpenAi(messages: List<ChatMessage>, key: String, model: String, temperature: Double): String {
        val arr = JSONArray()
        messages.forEach { m ->
            arr.put(JSONObject().put("role", m.role).put("content", m.content))
        }
        val payload = JSONObject()
            .put("model", model)
            .put("messages", arr)
            .put("temperature", temperature)

        val data = requestJson(
            "$OPENAI_BASE/chat/completions",
            "POST",
            payload.toString(),
            mapOf("Authorization" to "Bearer $key"),
            OPENAI,
            model,
        )

        val content = runCatching {
            data.getJSONArray("choices").getJSONObject(0).getJSONObject("message").opt("content")
        }.getOrNull() ?: throw AiException("คำตอบจากเซิร์ฟเวอร์ไม่ถูก formato")

        if (content is JSONArray) {
            val sb = StringBuilder()
            for (i in 0 until content.length()) {
                val part = content.optJSONObject(i) ?: continue
                sb.append(part.optString("text").ifBlank { part.optString("content") })
            }
            return sb.toString().trim()
        }
        return content.toString().trim()
    }

    private fun chatGemini(messages: List<ChatMessage>, key: String, model: String, temperature: Double): String {
        val name = model.removePrefix("models/")
        val contents = JSONArray()
        val systemParts = StringBuilder()

        messages.forEach { m ->
            if (m.role == "system") {
                if (systemParts.isNotEmpty()) systemParts.append("\n\n")
                systemParts.append(m.content)
            } else {
                contents.put(
                    JSONObject()
                        .put("role", if (m.role == "assistant") "model" else "user")
                        .put("parts", JSONArray().put(JSONObject().put("text", m.content))),
                )
            }
        }

        val payload = JSONObject()
            .put("contents", contents)
            .put("generationConfig", JSONObject().put("temperature", temperature))
        if (systemParts.isNotEmpty()) {
            payload.put("systemInstruction", JSONObject().put("parts", JSONArray().put(JSONObject().put("text", systemParts.toString()))))
        }

        val url = "$GEMINI_BASE/models/${URLEncoder.encode(name, "UTF-8")}:generateContent"
        val data = requestJson(url, "POST", payload.toString(), mapOf("x-goog-api-key" to key), GEMINI, model)

        val candidates = data.optJSONArray("candidates")
        if (candidates == null || candidates.length() == 0) {
            val blocked = data.optJSONObject("promptFeedback")?.optString("blockReason").orEmpty()
            if (blocked.isNotBlank()) throw AiException("Gemini ปฏิเสธคำขอนี้ด้วยตัวกรองความปลอดภัย ($blocked)")
            val detail = data.optJSONObject("error")?.optString("message").orEmpty()
            throw AiException("Gemini ไม่ได้ส่งคำตอบกลับมา" + if (detail.isNotBlank()) ": $detail" else "")
        }

        val candidate = candidates.optJSONObject(0) ?: JSONObject()
        val parts = candidate.optJSONObject("content")?.optJSONArray("parts")
        val sb = StringBuilder()
        if (parts != null) {
            for (i in 0 until parts.length()) {
                parts.optJSONObject(i)?.optString("text")?.let { sb.append(it) }
            }
        }
        val text = sb.toString().trim()
        if (text.isEmpty()) {
            val reason = candidate.optString("finishReason")
            if (reason.isNotBlank() && reason != "STOP") {
                throw AiException("Gemini หยุดตอบกลางทาง ($reason) — ลองถามใหม่หรือเปลี่ยนโมเดล")
            }
        }
        return text
    }

    // ---------- models ----------
    private val GEMINI_SKIP = listOf(
        "image", "tts", "live", "transcribe", "embedding", "robotics",
        "computer-use", "deep-research", "nano-banana", "omni", "veo", "lyria",
    )
    private val OPENAI_SKIP = listOf(
        "embedding", "tts", "whisper", "dall-e", "moderation", "audio",
        "realtime", "transcribe", "image", "search",
    )

    fun listModels(provider: String, apiKey: String): List<String> {
        if (apiKey.isBlank()) {
            throw AiException("ยังไม่มี API key ของ ${providerLabel(provider)} — ใส่คีย์ก่อนดึงรายการโมเดล")
        }
        val names = mutableListOf<String>()
        if (provider == GEMINI) {
            var pageToken = ""
            var page = 0
            while (page < 10) {
                page++
                var url = "$GEMINI_BASE/models?pageSize=1000"
                if (pageToken.isNotBlank()) url += "&pageToken=" + URLEncoder.encode(pageToken, "UTF-8")
                val data = requestJson(url, "GET", null, mapOf("x-goog-api-key" to apiKey), GEMINI, "")
                val models = data.optJSONArray("models")
                if (models != null) {
                    for (i in 0 until models.length()) {
                        val item = models.optJSONObject(i) ?: continue
                        val raw = item.optString("name").removePrefix("models/")
                        val methods = item.optJSONArray("supportedGenerationMethods")
                        var supports = false
                        if (methods != null) {
                            for (j in 0 until methods.length()) {
                                if (methods.optString(j) == "generateContent") supports = true
                            }
                        }
                        val low = raw.lowercase(Locale.ROOT)
                        if (raw.isNotBlank() && supports && low.startsWith("gemini") &&
                            GEMINI_SKIP.none { low.contains(it) }
                        ) {
                            names.add(raw)
                        }
                    }
                }
                pageToken = data.optString("nextPageToken")
                if (pageToken.isBlank()) break
            }
        } else {
            val data = requestJson("$OPENAI_BASE/models", "GET", null, mapOf("Authorization" to "Bearer $apiKey"), OPENAI, "")
            val arr = data.optJSONArray("data")
            if (arr != null) {
                for (i in 0 until arr.length()) {
                    val id = arr.optJSONObject(i)?.optString("id").orEmpty()
                    if (id.isBlank()) continue
                    val low = id.lowercase(Locale.ROOT)
                    if (OPENAI_SKIP.any { low.contains(it) }) continue
                    if (low.startsWith("gpt-") || low.startsWith("chatgpt") ||
                        low.startsWith("o1") || low.startsWith("o3") || low.startsWith("o4")
                    ) {
                        names.add(id)
                    }
                }
            }
        }
        return names.distinct().sortedByDescending { sortKey(it) }
    }

    /** เรียงรุ่นใหม่ก่อน เช่น gemini-4-argon > gemini-3.8-flash > gemini-3.6-flash */
    private fun sortKey(name: String): String =
        Regex("\\d+").findAll(name.lowercase(Locale.ROOT))
            .take(3)
            .joinToString(".") { it.value.padStart(4, '0') }
}
