package org.mojoagent.app

import android.os.Bundle
import android.os.Environment
import android.content.Context
import android.net.wifi.WifiManager
import java.net.InetAddress
import java.io.File
import java.net.NetworkInterface
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import kotlinx.coroutines.launch
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
  setContent { MaterialTheme { MojoApp(::apiCall, ::scanLocalServers) } }
 }
 private fun scanLocalServers(done: (List<String>) -> Unit) {
  Thread {
   val found = java.util.Collections.synchronizedSet(mutableSetOf<String>())
   try {
    val wifi = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
    val dhcp = wifi.dhcpInfo
    var rawIp = dhcp.ipAddress
    if (rawIp == 0) {
     val interfaces = NetworkInterface.getNetworkInterfaces()
     while (interfaces.hasMoreElements() && rawIp == 0) {
      val iface = interfaces.nextElement()
      if (iface.name.startsWith("wlan") || iface.name.startsWith("eth")) {
       val local = iface.interfaceAddresses.firstOrNull { it.address is java.net.Inet4Address }
       if (local != null) {
        val bytes = local.address.address
        rawIp = ((bytes[3].toInt() and 255) shl 24) or ((bytes[2].toInt() and 255) shl 16) or ((bytes[1].toInt() and 255) shl 8) or (bytes[0].toInt() and 255)
       }
      }
     }
    }
    val ip = rawIp.toLong() and 0xffffffffL
    val mask = (if (dhcp.netmask != 0) dhcp.netmask else 0x00FFFFFF).toLong() and 0xffffffffL
    if (ip == 0L) throw IllegalStateException("Connect to the same Wi-Fi network as the backend first.")
    val network = ip and mask
    val broadcast = network or (mask.inv() and 0xffffffffL)
    val total = (broadcast - network - 1L).coerceIn(0L, 1022L)
    val pool = Executors.newFixedThreadPool(24)
    val latch = CountDownLatch(total.toInt())
    for (offset in 1..total.toInt()) {
     val host = (network + offset).toInt()
     pool.execute {
      try {
       val address = InetAddress.getByAddress(byteArrayOf(host.toByte(), (host ushr 8).toByte(), (host ushr 16).toByte(), (host ushr 24).toByte())).hostAddress
       if (address != null) {
        val req = Request.Builder().url("http://$address:8766/api/v1/health").get().build()
        client.newCall(req).execute().use { response ->
         if (response.isSuccessful && response.body?.string()?.contains("MOJO AGENT") == true) found.add("http://$address:8766/api/v1")
        }
       }
      } catch (_: Exception) { } finally { latch.countDown() }
     }
    }
    latch.await(8, TimeUnit.SECONDS)
    pool.shutdownNow()
   } catch (_: Exception) { }
   runOnUiThread { done(found.sorted()) }
  }.start()
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
     if (path == "/backup/export" && it.isSuccessful) {
      val bytes = it.body?.bytes() ?: byteArrayOf()
      val directory = getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS) ?: filesDir
      val backupFile = File(directory, "mojo-agent-backup.sqlite3")
      backupFile.writeBytes(bytes)
      runOnUiThread { done("Database backup saved to: " + backupFile.absolutePath + " (" + bytes.size + " bytes)") }
     } else {
      val text = it.body?.string() ?: ""
      runOnUiThread {
done(if (it.isSuccessful) text else "HTTP " + it.code + ": " + text)
      }
     }
    }
   }
  })
 }
}

@Composable
fun MojoApp(call: (String, String, String, String?, (String) -> Unit) -> Unit, discover: ((List<String>) -> Unit) -> Unit) {
 val context = LocalContext.current
 val screenWidthDp = LocalConfiguration.current.screenWidthDp
 var base by remember { mutableStateOf(context.getSharedPreferences("mojo", Context.MODE_PRIVATE).getString("api_base", "http://10.0.2.2:8766/api/v1") ?: "http://10.0.2.2:8766/api/v1") }
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
 var servers by remember { mutableStateOf(listOf<String>()) }
 var scanning by remember { mutableStateOf(false) }
 var output by remember { mutableStateOf("Connect to your local MOJO AGENT service.") }
 var runtimeSummary by remember { mutableStateOf("Runtime metrics not loaded yet.") }
 var compactMode by remember { mutableStateOf(false) }
 var showAdvanced by remember { mutableStateOf(false) }
 var agentMode by remember { mutableStateOf("algorithms") }
 var modelPath by remember { mutableStateOf("") }
 var modelApproval by remember { mutableStateOf(false) }
 var githubRepo by remember { mutableStateOf("") }
 var githubRef by remember { mutableStateOf("main") }
 var manifestPath by remember { mutableStateOf("mojo-extension.json") }
 var extensionPreviewed by remember { mutableStateOf(false) }
 var manifestHash by remember { mutableStateOf("") }
 var runtimeEnabled by remember { mutableStateOf(false) }
 var busy by remember { mutableStateOf(false) }
 val drawerState = rememberDrawerState(DrawerValue.Closed)
 val scope = rememberCoroutineScope()
 val menuItems = listOf("Home", "Planner", "Memory", "Workflows", "Evolution", "Knowledge", "Tools", "Analytics", "Security", "Diagnostics", "Runtime Logs", "Runtime & Models", "Extensions Hub", "Backend Control", "Settings")
 val compactNavigation = screenWidthDp < 600
 val bottomTabs = listOf("Home", "Planner", "Workflows", "Settings")
 fun request(path: String, method: String = "GET", json: String? = null) {
  busy = true
  call(base, path, method, json) { output = it; if (path == "/settings" && method == "GET") { try { val prefs = JSONObject(it); theme = prefs.optString("theme", theme); agentMode = prefs.optString("runtime_mode", agentMode); modelPath = prefs.optString("litertlm_model", modelPath); runtimeEnabled = prefs.optBoolean("litertlm_enabled", false) } catch (_: Exception) { } }; if (path == "/extensions/github/preview") { extensionPreviewed = !it.startsWith("HTTP"); try { manifestHash = JSONObject(it).optString("manifest_sha256", "") } catch (_: Exception) { manifestHash = "" } }; if (path == "/runtime/status") { try { val parsed = JSONObject(it); val db = parsed.optJSONObject("database"); runtimeSummary = "PID " + parsed.optInt("pid") + " · uptime " + parsed.optDouble("uptime_seconds") + "s · " + parsed.optInt("threads") + " threads · database " + (db?.optLong("size_bytes") ?: 0) + " bytes · integrity " + (db?.optString("integrity") ?: "unknown") } catch (_: Exception) { } }; busy = false }
 }
 val darkMode = !(theme == "light" || (theme == "system" && !isSystemInDarkTheme()))
 val palette = if (darkMode) darkColorScheme(
  primary = androidx.compose.ui.graphics.Color(0xFF72E2C2),
  onPrimary = androidx.compose.ui.graphics.Color(0xFF06251D),
  secondary = androidx.compose.ui.graphics.Color(0xFF91BFFF),
  background = androidx.compose.ui.graphics.Color(0xFF080F1B),
  surface = androidx.compose.ui.graphics.Color(0xFF111D2D),
  surfaceVariant = androidx.compose.ui.graphics.Color(0xFF1A2A40)
 ) else lightColorScheme(
  primary = androidx.compose.ui.graphics.Color(0xFF176B58),
  secondary = androidx.compose.ui.graphics.Color(0xFF315F91),
  background = androidx.compose.ui.graphics.Color(0xFFF3F6FA),
  surface = androidx.compose.ui.graphics.Color(0xFFFFFFFF),
  surfaceVariant = androidx.compose.ui.graphics.Color(0xFFE8EEF5)
 )
 MaterialTheme(colorScheme = palette) {
 Scaffold(
  containerColor = MaterialTheme.colorScheme.background,
  bottomBar = {
   if (compactNavigation) NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
    bottomTabs.forEach { item ->
     NavigationBarItem(
      selected = tab == item,
      onClick = { tab = item },
      icon = { },
      label = { Text(item, maxLines = 1, style = MaterialTheme.typography.labelSmall) }
     )
    }
   }
  }
 ) { scaffoldPadding ->
 ModalNavigationDrawer(drawerState = drawerState, drawerContent = { ModalDrawerSheet {
  Text("MOJO AGENT", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(20.dp))
  Text("NAVIGATION", style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(horizontal = 20.dp, vertical = 8.dp))
  menuItems.forEach { item -> NavigationDrawerItem(label = { Text(item) }, selected = tab == item, onClick = { tab = item; scope.launch { drawerState.close() } }, modifier = Modifier.padding(horizontal = 10.dp)) }
  Divider(modifier = Modifier.padding(12.dp))
  Text("Local-first · protected core", style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(20.dp))
 } }) {
 Column(Modifier.fillMaxSize().widthIn(max = 1120.dp).padding(scaffoldPadding).verticalScroll(rememberScrollState()).padding(horizontal = if (compactMode) 12.dp else if (compactNavigation) 14.dp else 28.dp, vertical = if (compactMode) 10.dp else 22.dp), verticalArrangement = Arrangement.spacedBy(if (compactMode) 8.dp else 14.dp)) {
  Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
   TextButton(onClick = { scope.launch { drawerState.open() } }) { Text("☰ Menu") }
   Column(Modifier.weight(1f)) { Text("MOJO AGENT", style = MaterialTheme.typography.headlineMedium); Text("Algorithmic intelligence · local-first") }
   Surface(color = MaterialTheme.colorScheme.secondaryContainer, shape = MaterialTheme.shapes.small) { Text("v0.9", modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp), style = MaterialTheme.typography.labelSmall) }
  }
  OutlinedTextField(base, { base = it }, label = { Text("Backend API base URL") }, modifier = Modifier.fillMaxWidth(), singleLine = true, supportingText = { Text("Saved locally on this device") })
  Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
   OutlinedButton(onClick = { scanning = true; discover { servers = it; scanning = false } }, enabled = !busy && !scanning) { Text(if (scanning) "Scanning LAN…" else "Find backend on Wi-Fi") }
   OutlinedButton(onClick = { request("/discovery") }, enabled = !busy) { Text("Server info") }
   OutlinedButton(onClick = { context.getSharedPreferences("mojo", Context.MODE_PRIVATE).edit().putString("api_base", base.trimEnd('/')).apply(); output = "Backend address saved on this device." }, enabled = base.startsWith("http")) { Text("Save URL") }
  }
  servers.forEach { server -> OutlinedButton(onClick = { base = server; request("/health") }, modifier = Modifier.fillMaxWidth()) { Text("Use $server") } }
  when (tab) {
   "Backend Control" -> {
    Text("Backend control centre", style = MaterialTheme.typography.titleLarge)
    Text("Inspect the API, discover LAN interfaces, and review runtime configuration. Process start/stop is managed by the host operating system.")
    ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
     Text("Runtime monitor", style = MaterialTheme.typography.titleMedium)
     Text(runtimeSummary, style = MaterialTheme.typography.bodySmall)
     Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
      OutlinedButton(onClick = { request("/runtime/status") }, enabled = !busy) { Text("Refresh metrics") }
      OutlinedButton(onClick = { request("/diagnostics") }, enabled = !busy) { Text("Diagnostics") }
     }
    } }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     OutlinedButton(onClick = { request("/settings/validate", "POST", JSONObject().put("theme", theme).put("tool_approval_required", true).toString()) }, enabled = !busy) { Text("Validate settings") }
     OutlinedButton(onClick = { request("/backup/export") }, enabled = !busy) { Text("Export backup (local / USB)") }
    }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { Button(onClick = { request("/health") }, enabled = !busy) { Text("Health check") }; OutlinedButton(onClick = { request("/diagnostics") }, enabled = !busy) { Text("Diagnostics") } }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { OutlinedButton(onClick = { request("/discovery") }, enabled = !busy) { Text("Server discovery") }; OutlinedButton(onClick = { request("/settings") }, enabled = !busy) { Text("Load settings") } }
    Text("Database backup is limited to loopback connections. For Android, use USB port forwarding (adb reverse) to reach the local backend securely.", style = MaterialTheme.typography.bodySmall)
    Text("Connection address", style = MaterialTheme.typography.titleMedium)
    OutlinedTextField(base, { base = it }, label = { Text("API base URL") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
    Button(onClick = { context.getSharedPreferences("mojo", Context.MODE_PRIVATE).edit().putString("api_base", base.trimEnd('/')).apply(); request("/health") }, enabled = !busy && base.startsWith("http")) { Text("Save and test connection") }
    Text("LAN mode requires the backend to be explicitly started with --host 0.0.0.0 on a trusted private network. Do not expose port 8766 to the internet.")
   }
   "Home" -> {
    Text("Runtime", style = MaterialTheme.typography.titleLarge)
    Button(onClick = { request("/health") }, enabled = !busy) { Text("Check backend") }
    Text("Automatic discovery scans the connected Wi-Fi subnet for MOJO AGENT on port 8766. Start the backend with --host 0.0.0.0 on a trusted private LAN. For USB use adb reverse tcp:8766 tcp:8766 and 127.0.0.1.")
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
   "Runtime & Models" -> {
    Text("Agent runtime", style = MaterialTheme.typography.titleLarge)
    Text("Algorithms are always available. Local LiteRT-LM is optional and disabled until configured.")
    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) { Text("Enable LiteRT-LM", Modifier.weight(1f)); Switch(checked = runtimeEnabled, onCheckedChange = { runtimeEnabled = it }) }
    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
     listOf("algorithms", "hybrid", "litertlm").forEach { mode -> FilterChip(selected = agentMode == mode, onClick = { agentMode = mode }, label = { Text(mode) }) }
    }
    OutlinedTextField(modelPath, { modelPath = it }, label = { Text("Local .litertlm path or Hugging Face owner/model") }, modifier = Modifier.fillMaxWidth())
    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) { Text("Approve local inference", Modifier.weight(1f)); Switch(checked = modelApproval, onCheckedChange = { modelApproval = it }) }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     Button(onClick = { request("/settings", "PATCH", JSONObject().put("runtime_mode", agentMode).put("litertlm_enabled", runtimeEnabled).put("litertlm_model", modelPath).put("litertlm_backend", "cpu").put("litertlm_timeout_seconds", 120).toString()) }, enabled = !busy) { Text("Save runtime config") }
     OutlinedButton(onClick = { request("/agent/runtime") }, enabled = !busy) { Text("Runtime status") }
    }
    Button(onClick = { request("/agent/run", "POST", JSONObject().put("goal", goal).put("mode", agentMode).put("model", modelPath).put("backend", "cpu").put("approved", modelApproval).toString()) }, enabled = !busy && goal.isNotBlank() && (agentMode == "algorithms" || (runtimeEnabled && modelPath.isNotBlank() && modelApproval)), modifier = Modifier.fillMaxWidth()) { Text("Run agent") }
    Text("Hybrid mode uses the deterministic plan as authority. Model output is advisory and cannot execute tools. Model inference requires explicit approval.", style = MaterialTheme.typography.bodySmall)
    OutlinedButton(onClick = { request("/litertlm/status") }, enabled = !busy) { Text("LiteRT-LM runtime status") }
   }
   "Extensions Hub" -> {
    Text("GitHub skills and tools", style = MaterialTheme.typography.titleLarge)
    Text("Only declarative JSON manifests are installed. Repository code and shell scripts are never executed.")
    OutlinedTextField(githubRepo, { githubRepo = it }, label = { Text("GitHub repository owner/name") }, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(githubRef, { githubRef = it }, label = { Text("Branch or tag") }, modifier = Modifier.fillMaxWidth())
    OutlinedTextField(manifestPath, { manifestPath = it; extensionPreviewed = false; manifestHash = "" }, label = { Text("Manifest path") }, modifier = Modifier.fillMaxWidth())
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     OutlinedButton(onClick = { extensionPreviewed = false; manifestHash = ""; request("/extensions/github/preview", "POST", JSONObject().put("repository", githubRepo).put("ref", githubRef).put("manifest_path", manifestPath).toString()) }, enabled = !busy && githubRepo.contains("/")) { Text("Preview") }
     Button(onClick = { request("/extensions/github/install", "POST", JSONObject().put("repository", githubRepo).put("ref", githubRef).put("manifest_path", manifestPath).put("expected_sha256", manifestHash).toString()); extensionPreviewed = false }, enabled = !busy && extensionPreviewed) { Text("Install") }
    }
    OutlinedButton(onClick = { request("/extensions") }, enabled = !busy) { Text("List installed extensions") }
   }
   "Runtime Logs" -> {
    Text("Runtime event log", style = MaterialTheme.typography.titleLarge)
    Text("Bounded in-memory events. Request bodies and credentials are not recorded.", style = MaterialTheme.typography.bodySmall)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
     Button(onClick = { request("/runtime/logs?limit=200") }, enabled = !busy) { Text("Refresh logs") }
     OutlinedButton(onClick = { request("/runtime/logs/clear", "POST", "{}") }, enabled = !busy) { Text("Clear logs") }
    }
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
    ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
     Text("Interface preferences", style = MaterialTheme.typography.titleMedium)
     Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) { Text("Compact spacing", Modifier.weight(1f)); Switch(checked = compactMode, onCheckedChange = { compactMode = it }) }
     Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) { Text("Advanced controls", Modifier.weight(1f)); Switch(checked = showAdvanced, onCheckedChange = { showAdvanced = it }) }
     if (showAdvanced) Text("Advanced mode exposes diagnostic and configuration validation actions. Protected safety settings remain locked.", style = MaterialTheme.typography.bodySmall)
    } }
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
    if (showAdvanced) OutlinedButton(onClick = { request("/settings/validate", "POST", JSONObject().put("theme", theme).put("tool_approval_required", true).toString()) }, enabled = !busy) { Text("Validate current configuration") }
    Text("Security: local API only. Tools require explicit approval. Shell execution and source self-modification remain disabled.")
   }
  }
  if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
  Text("RESPONSE", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
  Surface(color = MaterialTheme.colorScheme.surfaceVariant, shape = MaterialTheme.shapes.medium, modifier = Modifier.fillMaxWidth()) {
   Text(output, modifier = Modifier.padding(12.dp), style = MaterialTheme.typography.bodySmall)
  }
  }
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
