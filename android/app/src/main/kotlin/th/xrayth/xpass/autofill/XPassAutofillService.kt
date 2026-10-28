package th.xrayth.xpass.autofill

import android.app.assist.AssistStructure
import android.os.CancellationSignal
import android.service.autofill.AutofillService
import android.service.autofill.Dataset
import android.service.autofill.FillCallback
import android.service.autofill.FillRequest
import android.service.autofill.FillResponse
import android.service.autofill.SaveCallback
import android.service.autofill.SaveRequest
import android.view.autofill.AutofillId
import android.view.autofill.AutofillValue
import android.widget.RemoteViews
import th.xrayth.xpass.data.VaultRepo

class XPassAutofillService : AutofillService() {

    override fun onFillRequest(
        request: FillRequest,
        cancellationSignal: CancellationSignal,
        callback: FillCallback,
    ) {
        val repo = VaultRepo(this)
        if (!repo.isUnlocked) {
            repo.prepare()
        }

        val vault = repo.load()
        val responseBuilder = FillResponse.Builder()

        val structure = request.fillContexts.lastOrNull()?.structure ?: return callback.onSuccess(null)
        val fillableFields = findFillableFields(structure)

        if (fillableFields.usernameId == null && fillableFields.passwordId == null) {
            callback.onSuccess(null)
            return
        }

        for (account in vault.accounts) {
            if (fillableFields.passwordId != null) {
                val presentation = RemoteViews(packageName, android.R.layout.simple_list_item_1).apply {
                    setTextViewText(android.R.id.text1, "xpass: ${account.title}")
                }
                @Suppress("DEPRECATION")
                val datasetBuilder = Dataset.Builder(presentation)
                fillableFields.usernameId?.let { uid ->
                    datasetBuilder.setValue(uid, AutofillValue.forText(account.account.ifBlank { account.issuer }))
                }
                fillableFields.passwordId.let { pid ->
                    datasetBuilder.setValue(pid, AutofillValue.forText(account.secret))
                }
                responseBuilder.addDataset(datasetBuilder.build())
            }
        }

        callback.onSuccess(responseBuilder.build())
    }

    override fun onSaveRequest(request: SaveRequest, callback: SaveCallback) {
        callback.onSuccess()
    }

    private data class FillableFields(
        val usernameId: AutofillId?,
        val passwordId: AutofillId?,
    )

    private fun findFillableFields(structure: AssistStructure): FillableFields {
        var usernameId: AutofillId? = null
        var passwordId: AutofillId? = null

        fun traverse(node: AssistStructure.ViewNode) {
            val hints = node.autofillHints
            if (hints != null) {
                for (hint in hints) {
                    if (hint.contains("username") || hint.contains("email") || hint.contains("name")) {
                        if (usernameId == null) usernameId = node.autofillId
                    }
                    if (hint.contains("password")) {
                        if (passwordId == null) passwordId = node.autofillId
                    }
                }
            }
            if (usernameId == null && (node.className?.contains("EditText") == true || node.idEntry?.contains("user") == true)) {
                usernameId = node.autofillId
            }
            if (passwordId == null && (node.idEntry?.contains("pass") == true || node.className?.contains("EditText") == true)) {
                passwordId = node.autofillId
            }

            for (i in 0 until node.childCount) {
                traverse(node.getChildAt(i))
            }
        }

        for (i in 0 until structure.windowNodeCount) {
            structure.getWindowNodeAt(i).rootViewNode?.let { traverse(it) }
        }

        return FillableFields(usernameId, passwordId)
    }
}
