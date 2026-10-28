package th.xrayth.xpass.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.sp
import th.xrayth.xpass.R

val UiFontFamily = FontFamily(
    Font(R.font.ibm_plex_sans_thai_regular, FontWeight.Normal),
    Font(R.font.ibm_plex_sans_thai_medium, FontWeight.Medium),
    Font(R.font.ibm_plex_sans_thai_bold, FontWeight.Bold),
)

val MonoFontFamily = FontFamily(
    Font(R.font.jetbrains_mono_regular, FontWeight.Normal),
    Font(R.font.jetbrains_mono_medium, FontWeight.Medium),
    Font(R.font.jetbrains_mono_bold, FontWeight.Bold),
)

val LocalMonoFont = staticCompositionLocalOf { MonoFontFamily }

// สีตรงกับธีมเดสก์ท็อป (xpass_qt.py)
private val DarkScheme = darkColorScheme(
    primary = Color(0xFF4F7DFF),
    onPrimary = Color.White,
    primaryContainer = Color(0xFF1A2436),
    onPrimaryContainer = Color(0xFFDCE5FF),
    secondary = Color(0xFF3FCF7F),
    onSecondary = Color(0xFF06240F),
    secondaryContainer = Color(0xFF12301F),
    onSecondaryContainer = Color(0xFFBFEFD4),
    tertiary = Color(0xFFFFC46B),
    onTertiary = Color(0xFF2A1C00),
    background = Color(0xFF0B0D10),
    onBackground = Color(0xFFE6E9EF),
    surface = Color(0xFF11151C),
    onSurface = Color(0xFFE6E9EF),
    surfaceVariant = Color(0xFF1A212C),
    onSurfaceVariant = Color(0xFF98A1B0),
    surfaceContainer = Color(0xFF0E1116),
    surfaceContainerHigh = Color(0xFF151B24),
    outline = Color(0xFF26303F),
    outlineVariant = Color(0xFF1D2430),
    error = Color(0xFFFF6B7D),
    onError = Color(0xFF2A0007),
    errorContainer = Color(0xFF3A1119),
    onErrorContainer = Color(0xFFFFC9D0),
    inverseSurface = Color(0xFFE6E9EF),
    inverseOnSurface = Color(0xFF11151C),
)

private val LightScheme = lightColorScheme(
    primary = Color(0xFF2F5BD0),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFDCE5FF),
    onPrimaryContainer = Color(0xFF0B1E4A),
    secondary = Color(0xFF128A4D),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFCDEEDC),
    onSecondaryContainer = Color(0xFF05240F),
    tertiary = Color(0xFF8A5A00),
    onTertiary = Color.White,
    background = Color(0xFFF4F6FA),
    onBackground = Color(0xFF1B2430),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF1B2430),
    surfaceVariant = Color(0xFFEAEEF5),
    onSurfaceVariant = Color(0xFF5C6779),
    surfaceContainer = Color(0xFFF7F9FC),
    surfaceContainerHigh = Color(0xFFEDF1F7),
    outline = Color(0xFFC8D2E2),
    outlineVariant = Color(0xFFDDE4EE),
    error = Color(0xFFD92D4A),
    onError = Color.White,
    errorContainer = Color(0xFFFFDDE2),
    onErrorContainer = Color(0xFF3A0009),
    inverseSurface = Color(0xFF1B2430),
    inverseOnSurface = Color(0xFFF4F6FA),
)

private val XPassTypography = Typography().let { base ->
    base.copy(
        displaySmall = base.displaySmall.copy(fontFamily = UiFontFamily),
        headlineMedium = base.headlineMedium.copy(fontFamily = UiFontFamily),
        headlineSmall = base.headlineSmall.copy(fontFamily = UiFontFamily),
        titleLarge = base.titleLarge.copy(fontFamily = UiFontFamily),
        titleMedium = base.titleMedium.copy(fontFamily = UiFontFamily),
        titleSmall = base.titleSmall.copy(fontFamily = UiFontFamily),
        bodyLarge = base.bodyLarge.copy(fontFamily = UiFontFamily),
        bodyMedium = base.bodyMedium.copy(fontFamily = UiFontFamily),
        bodySmall = base.bodySmall.copy(fontFamily = UiFontFamily),
        labelLarge = base.labelLarge.copy(fontFamily = UiFontFamily),
        labelMedium = base.labelMedium.copy(fontFamily = UiFontFamily),
        labelSmall = base.labelSmall.copy(fontFamily = UiFontFamily, fontSize = 11.sp),
    )
}

@Composable
fun XPassTheme(
    theme: String = "dark",
    fontScale: Float = 1f,
    content: @Composable () -> Unit,
) {
    val dark = when (theme) {
        "light" -> false
        "system" -> isSystemInDarkTheme()
        else -> true
    }
    val density = LocalDensity.current
    val scale = fontScale.coerceIn(0.8f, 1.5f)
    CompositionLocalProvider(
        LocalDensity provides Density(density.density, density.fontScale * scale),
        LocalMonoFont provides MonoFontFamily,
    ) {
        MaterialTheme(
            colorScheme = if (dark) DarkScheme else LightScheme,
            typography = XPassTypography,
            content = content,
        )
    }
}
