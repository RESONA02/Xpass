package th.xrayth.xpass.util

import android.app.Activity
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning

/**
 * สแกน QR ผ่าน Google Code Scanner (Play services)
 * ไม่ต้องขอสิทธิ์กล้องและไม่ต้องมี UI preview เอง
 */
fun scanQrCode(
    activity: Activity,
    onResult: (String) -> Unit,
    onError: (String) -> Unit,
) {
    val options = GmsBarcodeScannerOptions.Builder()
        .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
        .enableAutoZoom()
        .build()

    runCatching {
        GmsBarcodeScanning.getClient(activity, options).startScan()
            .addOnSuccessListener { barcode ->
                val raw = barcode.rawValue
                if (raw.isNullOrBlank()) onError("อ่านข้อมูลจาก QR ไม่ได้") else onResult(raw)
            }
            .addOnFailureListener { e ->
                onError(e.localizedMessage ?: "สแกนไม่สำเร็จ — ต้องมี Google Play services")
            }
    }.onFailure {
        onError("เปิดตัวสแกนไม่ได้: ${it.localizedMessage ?: "ไม่ทราบสาเหตุ"}")
    }
}
