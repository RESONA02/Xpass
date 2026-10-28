package th.xrayth.xpass.data

import android.content.Context

data class AppSettings(
    val theme: String = "dark",        // "dark" | "light" | "system"
    val fontScale: Float = 1.0f,       // 0.8 – 1.5
    val autoCopy: Boolean = false,
    val rememberModel: Boolean = true,
    val lastModel: String = "",
    val pinLockOnBackground: Boolean = true,
) {
    companion object {
        val THEMES = listOf("dark", "light", "system")
        fun clean(raw: AppSettings): AppSettings = raw.copy(
            theme = if (raw.theme in THEMES) raw.theme else "dark",
            fontScale = raw.fontScale.coerceIn(0.8f, 1.5f),
            lastModel = raw.lastModel.take(120),
        )
    }
}

/** ค่าตั้ง UI — เก็บใน SharedPreferences ไม่มีข้อมูลลับ */
class SettingsRepo(context: Context) {

    private val prefs = context.applicationContext.getSharedPreferences("xpass_settings", Context.MODE_PRIVATE)

    fun load(): AppSettings = AppSettings.clean(
        AppSettings(
            theme = prefs.getString("theme", "dark") ?: "dark",
            fontScale = prefs.getFloat("font_scale", 1.0f),
            autoCopy = prefs.getBoolean("auto_copy", false),
            rememberModel = prefs.getBoolean("remember_model", true),
            lastModel = prefs.getString("last_model", "") ?: "",
            pinLockOnBackground = prefs.getBoolean("lock_on_background", true),
        ),
    )

    fun save(settings: AppSettings) {
        val s = AppSettings.clean(settings)
        prefs.edit()
            .putString("theme", s.theme)
            .putFloat("font_scale", s.fontScale)
            .putBoolean("auto_copy", s.autoCopy)
            .putBoolean("remember_model", s.rememberModel)
            .putString("last_model", s.lastModel)
            .putBoolean("lock_on_background", s.pinLockOnBackground)
            .apply()
    }
}
