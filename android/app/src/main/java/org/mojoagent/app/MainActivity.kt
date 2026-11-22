package org.mojoagent.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException

class MainActivity : ComponentActivity() {
 private val client = OkHttpClient()
 override fun onCreate(savedInstanceState: Bundle?) {
  super.onCreate(savedInstanceState)
  setContent { MaterialTheme { MojoApp(::apiCall) } }
 }
 private fun apiCall(base: String, path: String, method: String, payload: String?, done: (String) -> Unit) {
  val body = payload?.toRequestBody("application/json".toMediaType())
  val builder = Request.Builder().url(base.trimEnd('/') + path)
  when (method) {
   "POST" -> builder.post(body ?: "{}".toRequestBody("application/json".toMediaType()))
   "PATCH" -> builder.patch(body ?: "{}".toRequestBody("application/json".toMediaType()))
   "DELETE" -> builder.delete()
   else -> builder.get()
  }
  client.newCall(builder.build()).enqueue(object : Callback {
   override fun onFailure(call: Call, e: IOException) { runOnUiThread { done("Connection failed: " + (e.message ?: "unknown error")) } }
   override fun onResponse(call: Call, response: Response) {
    response.use {
     val text = it.body?.string() ?: ""
     runOnUiThread { done(if (it.isSuccessful) text else "HTTP ${it.code}: $text") }
    }
   }
  })
 }
}

@Composable
fun MojoApp(call: (String, String, String, String?, (String) -> Unit) -> Unit) {
 var base by remember { mutableStateOf("http://10.0.2.2:8766/api/v1") }
 var tab by remember { mutableStateOf("Home") }
 var goal by remember { mutableStateOf("Create a project plan") }
 var memoryText by remember { mutableStateOf("") }
 var workflowName by remember { mutableStateOf("Mobile workflow") }
 var workflowText by remember { mutableStateOf("Hello from MOJO AGENT") }
 var nodeText by remember { mutableStateOf("New concept") }
 var theme by remember { mutableStateOf("dark") }
 var candidateId by remember { mutableStateOf("") }
 var confirmApproval by remember { mutableStateOf(false) }
 var edgeSource by remember { mutableStateOf("") }
 var edgeTarget by remember { mutableStateOf("") }
 var edgeRelation by remember { mutableStateOf("related_to") }
 var scheduleWorkflowId by remember { mutableStateOf("") }
 var scheduleSeconds by remember { mutableStateOf("3600") }
 var scheduleId by remember { mutableStateOf("") }
 var output by remember { mutableStateOf("Connect to your local MOJO AGENT service.") }
 var busy by remember { mutableStateOf(false) }
 fun request(path: String, method: String = "GET", json: String? = null) {
  busy = true
  call(base, path, method, json) { output = it; if (path == "/settings" && method == "GET") { try { theme = JSONObject(it).optString("theme", theme) } catch (_: Exception) { } }; busy = false }
 }
 MaterialTheme(colorScheme = if (theme == "light") lightColorScheme() else darkColorScheme()) {
 Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
  Text("MOJO AGENT", style = MaterialTheme.typography.headlineMedium)
  Text("Algorithmic intelligence · local-first · no LLM required")
  OutlinedTextField(base, { base = it }, label = { Text("Local API base URL") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
  Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
   listOf("Home", "Planner", "Memory", "Workflows", "Evolution", "Knowledge", "Tools", "Analytics", "Security", "Diagnostics", "Settings").forEach { item ->
    FilterChip(selected = tab == item, onClick = { tab = item }, label = { Text(item) })
   }
  }
  when (tab) {
   "Home" -> {
    Text("Runtime", style = MaterialTheme.typography.titleLarge)
    Button(onClick = { request("/health") }, enabled = !busy) { Text("Check backend") }
    Text("Use the emulator URL above, or on a physical phone connect over USB with adb reverse tcp:8766 tcp:8766.")
   }
   "Planner" -> {
    Text("Goal planner", style = MaterialTheme.typography.titleLarge)
    OutlinedTextField(goal, { goal = it }, label = { Text("Describe your goal") }, modifier = Modifier.fillMaxWidth(), minLines = 3)
    Button(onClick = { request("/plan", "POST", JSONObject().put("goal", goal).toString()) }, enabled = !busy && goal.isNotBlank()) { Text("Create plan") }
   }
   "Memory" -> {
    Text("Persistent memory", style = MaterialTheme.typography.titleLarge)
    OutlinedTextField(memoryText, { memoryText = it }, label = { Text("Memory content") }, modifier = Modifier.fillMaxWidth(), minLines = 3)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     Button(onClick = {
      request("/memory", "POST", JSONObject().put("content", memoryText).put("kind", "episodic").put("importance", .7).toString())
      memoryText = ""
     }, enabled = !busy && memoryText.isNotBlank()) { Text("Save memory") }
     OutlinedButton(onClick = { request("/memory") }, enabled = !busy) { Text("Refresh") }
    }
    OutlinedButton(onClick = { request("/memory/export") }, enabled = !busy) { Text("Export memory JSON") }
   }
   "Workflows" -> {
    Text("Workflow runner", style = MaterialTheme.typography.titleLarge)
    OutlinedTextField(workflowName, { workflowName = it }, label = { Text("Workflow name") }, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(workflowText, { workflowText = it }, label = { Text("Text step") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     Button(onClick = {
      val steps = JSONArray().put(JSONObject().put("type", "text").put("value", workflowText))
      request("/workflows", "POST", JSONObject().put("name", workflowName).put("steps", steps).toString())
     }, enabled = !busy && workflowName.isNotBlank() && workflowText.isNotBlank()) { Text("Create") }
     OutlinedButton(onClick = { request("/workflows") }, enabled = !busy) { Text("List workflows") }
    }
    Text("Persistent scheduler", style = MaterialTheme.typography.titleMedium)
    OutlinedTextField(scheduleWorkflowId, { scheduleWorkflowId = it }, label = { Text("Workflow ID") }, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(scheduleSeconds, { scheduleSeconds = it.filter(Char::isDigit).take(8) }, label = { Text("Interval seconds (60–2592000)") }, modifier = Modifier.fillMaxWidth())
    Button(onClick = { request("/scheduler/schedules", "POST", JSONObject().put("workflow_id", scheduleWorkflowId).put("interval_seconds", scheduleSeconds.toIntOrNull() ?: 60).toString()) }, enabled = !busy && scheduleWorkflowId.isNotBlank() && (scheduleSeconds.toIntOrNull() ?: 0) in 60..2592000) { Text("Create schedule") }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     OutlinedButton(onClick = { request("/scheduler/schedules") }, enabled = !busy) { Text("List schedules") }
     Button(onClick = { request("/scheduler/tick", "POST", "{}") }, enabled = !busy) { Text("Run due now") }
    }
    OutlinedTextField(scheduleId, { scheduleId = it }, label = { Text("Schedule ID for controls") }, modifier = Modifier.fillMaxWidth())
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     OutlinedButton(onClick = { request("/scheduler/schedules/$scheduleId", "PATCH", JSONObject().put("enabled", false).toString()) }, enabled = !busy && scheduleId.isNotBlank()) { Text("Pause") }
     OutlinedButton(onClick = { request("/scheduler/schedules/$scheduleId", "PATCH", JSONObject().put("enabled", true).toString()) }, enabled = !busy && scheduleId.isNotBlank()) { Text("Resume") }
     OutlinedButton(onClick = { request("/scheduler/schedules/$scheduleId", "DELETE") }, enabled = !busy && scheduleId.isNotBlank()) { Text("Delete") }
    }
   }
   "Evolution" -> {
    Text("Evolution laboratory", style = MaterialTheme.typography.titleLarge)
    Text("Bounded strategy optimization. Candidate activation requires validation and explicit approval.")
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     Button(onClick = { request("/evolution/status") }, enabled = !busy) { Text("Status") }
     OutlinedButton(onClick = { request("/evolution/experiment", "POST", "{}") }, enabled = !busy) { Text("Run experiment") }
    }
    OutlinedButton(onClick = { request("/evolution/status") }, enabled = !busy) { Text("Refresh candidates") }
    OutlinedTextField(candidateId, { candidateId = it }, label = { Text("Candidate ID from response") }, modifier = Modifier.fillMaxWidth())
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     Button(onClick = { request("/evolution/candidates/$candidateId/validate", "POST", "{}") }, enabled = !busy && candidateId.isNotBlank()) { Text("Validate") }
     OutlinedButton(onClick = { confirmApproval = true }, enabled = !busy && candidateId.isNotBlank()) { Text("Approve…") }
    }
   }
   "Knowledge" -> {
    Text("Knowledge graph", style = MaterialTheme.typography.titleLarge)
    OutlinedTextField(nodeText, { nodeText = it }, label = { Text("Concept label") }, modifier = Modifier.fillMaxWidth())
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     Button(onClick = { request("/knowledge/nodes", "POST", JSONObject().put("label", nodeText).put("kind", "concept").toString()) }, enabled = !busy && nodeText.isNotBlank()) { Text("Add concept") }
     OutlinedButton(onClick = { request("/knowledge") }, enabled = !busy) { Text("Refresh graph") }
    }
    OutlinedTextField(edgeSource, { edgeSource = it }, label = { Text("Source node ID") }, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(edgeTarget, { edgeTarget = it }, label = { Text("Target node ID") }, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(edgeRelation, { edgeRelation = it }, label = { Text("Relationship") }, modifier = Modifier.fillMaxWidth())
    Button(onClick = { request("/knowledge/edges", "POST", JSONObject().put("source", edgeSource).put("target", edgeTarget).put("relation", edgeRelation).put("weight", 1).toString()) }, enabled = !busy && edgeSource.isNotBlank() && edgeTarget.isNotBlank() && edgeSource != edgeTarget && edgeRelation.isNotBlank()) { Text("Connect concepts") }
   }
   "Tools" -> {
    Text("Allowlisted tools", style = MaterialTheme.typography.titleLarge)
    Button(onClick = { request("/tools") }, enabled = !busy) { Text("Load available tools") }
    Text("Tool execution requires explicit approval. Shell commands are not available.")
   }
   "Diagnostics" -> {
    Text("Runtime diagnostics", style = MaterialTheme.typography.titleLarge)
    Button(onClick = { request("/diagnostics") }, enabled = !busy) { Text("Run diagnostics") }
    Text("Only runtime metadata and aggregate counts are returned; personal content is not collected.")
   }
   "Analytics" -> {
    Text("Runtime analytics", style = MaterialTheme.typography.titleLarge)
    Button(onClick = { request("/analytics?limit=50") }, enabled = !busy) { Text("Refresh analytics") }
   }
   "Security" -> {
    Text("Security status", style = MaterialTheme.typography.titleLarge)
    Button(onClick = { request("/security/status") }, enabled = !busy) { Text("Inspect security controls") }
    Text("The server remains loopback-only. Remote access is not configured.")
   }
   "Settings" -> {
    Text("Runtime settings", style = MaterialTheme.typography.titleLarge)
    Text("Theme preference")
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     listOf("dark", "light", "system").forEach { value ->
      FilterChip(selected = theme == value, onClick = { theme = value }, label = { Text(value) })
     }
    }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     Button(onClick = { request("/settings", "PATCH", JSONObject().put("theme", theme).toString()) }, enabled = !busy) { Text("Save settings") }
     OutlinedButton(onClick = { request("/settings") }, enabled = !busy) { Text("Load settings") }
    }
    Text("Security: local API only. Tools require explicit approval. Shell execution and source self-modification remain disabled.")
   }
  }
  if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
  Text("RESPONSE", style = MaterialTheme.typography.labelLarge)
  Surface(color = MaterialTheme.colorScheme.surfaceVariant, shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth()) {
   Text(output, modifier = Modifier.padding(12.dp), style = MaterialTheme.typography.bodySmall)
  }
  }
 }
 if (confirmApproval) AlertDialog(
  onDismissRequest = { confirmApproval = false },
  title = { Text("Approve strategy?") },
  text = { Text("This activates the validated candidate as champion. Protected control code and source files are not modified.") },
  confirmButton = { TextButton(onClick = { confirmApproval = false; request("/evolution/candidates/$candidateId/approve", "POST", JSONObject().put("approved", true).toString()) }) { Text("Approve candidate") } },
  dismissButton = { TextButton(onClick = { confirmApproval = false }) { Text("Cancel") } }
 )
}
