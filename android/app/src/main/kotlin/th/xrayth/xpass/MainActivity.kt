package th.xrayth.xpass

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.fragment.app.FragmentActivity
import th.xrayth.xpass.ui.XPassApp

class MainActivity : FragmentActivity() {

    private val vm: XPassViewModel by viewModels()

    private var stoppedAt = 0L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { XPassApp(vm) }
    }

    override fun onStart() {
        super.onStart()
        if (stoppedAt > 0 && vm.pinEnabled && vm.settings.pinLockOnBackground) {
            val away = System.currentTimeMillis() - stoppedAt
            if (away > LOCK_AFTER_MS) vm.lockNow()
        }
        stoppedAt = 0L
    }

    override fun onStop() {
        super.onStop()
        if (!isChangingConfigurations) stoppedAt = System.currentTimeMillis()
    }

    private companion object {
        const val LOCK_AFTER_MS = 2 * 60 * 1000L
    }
}
