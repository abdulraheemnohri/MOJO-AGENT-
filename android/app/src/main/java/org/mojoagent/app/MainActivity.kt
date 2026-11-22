package org.mojoagent.app
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
class MainActivity:ComponentActivity(){
 private val client=OkHttpClient()
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);setContent { MaterialTheme { AgentScreen(::getHealth,::plan) } }}
 private fun getHealth(url:String,done:(String)->Unit){val req=Request.Builder().url(url.trimEnd('/')+"/health").build();client.newCall(req).enqueue(object:Callback{override fun onFailure(call:Call,e:IOException){runOnUiThread{done("Connection failed: "+e.message)}};override fun onResponse(call:Call,response:Response){response.use{val body=it.body?.string()?: "";runOnUiThread{done(body)}}}})}
 private fun plan(url:String,goal:String,done:(String)->Unit){val body=JSONObject().put("goal",goal).toString().toRequestBody("application/json".toMediaType());val req=Request.Builder().url(url.trimEnd('/')+"/plan").post(body).build();client.newCall(req).enqueue(object:Callback{override fun onFailure(call:Call,e:IOException){runOnUiThread{done("Request failed: "+e.message)}};override fun onResponse(call:Call,response:Response){response.use{val text=it.body?.string()?: "";runOnUiThread{done(text)}}}})}
}
@Composable fun AgentScreen(health:(String,(String)->Unit)->Unit,plan:(String,String,(String)->Unit)->Unit){
 var base by remember{mutableStateOf("http://10.0.2.2:8766/api/v1")};var goal by remember{mutableStateOf("Create a project plan")};var output by remember{mutableStateOf("Connect to your local MOJO AGENT service.")};var busy by remember{mutableStateOf(false)}
 Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(14.dp)){
  Text("MOJO AGENT",style=MaterialTheme.typography.headlineMedium);Text("Algorithmic intelligence · no LLM required")
  OutlinedTextField(base,{base=it},label={Text("Local API base URL")},modifier=Modifier.fillMaxWidth())
  Button(onClick={busy=true;health(base){output=it;busy=false}},enabled=!busy){Text("Check runtime")}
  OutlinedTextField(goal,{goal=it},label={Text("Goal")},modifier=Modifier.fillMaxWidth(),minLines=3)
  Button(onClick={busy=true;plan(base,goal){output=it;busy=false}},enabled=!busy){Text("Create plan")}
  if(busy)LinearProgressIndicator(Modifier.fillMaxWidth())
  Text("OUTPUT",style=MaterialTheme.typography.labelLarge);Text(output)
 }
}
