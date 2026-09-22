import {app,BrowserWindow,dialog,ipcMain} from 'electron'
import {spawn, type ChildProcessWithoutNullStreams} from 'node:child_process'
import {fileURLToPath} from 'node:url'
import path from 'node:path'

const here=path.dirname(fileURLToPath(import.meta.url))
let worker:ChildProcessWithoutNullStreams|undefined
let runId=0
function createWindow(){
 const win=new BrowserWindow({width:1240,height:850,minWidth:820,minHeight:640,backgroundColor:'#f7f6f1',titleBarStyle:'hiddenInset',webPreferences:{preload:path.join(here,'preload.js'),contextIsolation:true,nodeIntegration:false}})
 if(process.env.VITE_DEV_SERVER_URL) win.loadURL(process.env.VITE_DEV_SERVER_URL)
 else win.loadFile(path.join(here,'../dist/index.html'))
}
app.whenReady().then(()=>{createWindow();app.on('activate',()=>{if(BrowserWindow.getAllWindows().length===0)createWindow()})})
app.on('window-all-closed',()=>{worker?.kill();if(process.platform!=='darwin')app.quit()})
ipcMain.handle('dialog:directory',async()=>{const result=await dialog.showOpenDialog({properties:['openDirectory']});return result.canceled?null:result.filePaths[0]})
ipcMain.handle('job:start',(event,request)=>{
 worker?.kill(); const current=++runId
 const send=(payload:unknown)=>{if(current===runId&&!event.sender.isDestroyed())event.sender.send('job:event',payload)}
 const packaged=path.join(process.resourcesPath,'desktop-sidecar',process.platform==='win32'?'ascii-tree-reorg-sidecar.exe':'ascii-tree-reorg-sidecar')
 const command=process.env.ASCII_TREE_REORG_PYTHON||(app.isPackaged?packaged:'python3'); const args=app.isPackaged?[]:['-m','ascii_tree_reorg.desktop.bridge']
 let terminal=false
 try{worker=spawn(command,args,{stdio:['pipe','pipe','pipe']})}catch(error){send({kind:'error',message:String(error),level:'error',current:0,total:0,data:{}});return}
 const processForRun=worker
 let buffer=''
 const handleLine=(line:string)=>{if(!line.trim())return;try{const payload=JSON.parse(line);if(payload.kind==='complete'||payload.kind==='error'||payload.kind==='cancelled')terminal=true;send(payload)}catch{terminal=true;send({kind:'error',message:'The desktop worker returned invalid data.',level:'error',current:0,total:0,data:{}})}}
 processForRun.stdout.on('data',chunk=>{buffer+=chunk.toString();const lines=buffer.split('\n');buffer=lines.pop()||'';for(const line of lines)handleLine(line)})
 processForRun.stderr.on('data',chunk=>send({kind:'diagnostic',message:chunk.toString().trim(),level:'info',current:0,total:0,data:{}}))
 processForRun.on('error',error=>{terminal=true;send({kind:'error',message:`Could not start the desktop worker: ${error.message}`,level:'error',current:0,total:0,data:{}})})
 processForRun.on('close',(code,signal)=>{if(buffer)handleLine(buffer);if(current===runId&&worker===processForRun)worker=undefined;if(!terminal&&current===runId)send({kind:'error',message:`The desktop worker stopped before finishing${signal?` (${signal})`:code===null?'':` (exit ${code})`}.`,level:'error',current:0,total:0,data:{}})})
 processForRun.stdin.on('error',()=>{})
 processForRun.stdin.write(JSON.stringify(request)+'\n')
})
ipcMain.handle('job:cancel',(event)=>{if(!worker)return;worker.kill();worker=undefined;runId++;if(!event.sender.isDestroyed())event.sender.send('job:event',{kind:'cancelled',message:'Operation cancelled. Files already copied remain in the destination.',level:'warning',current:0,total:0,data:{partial_results:true}})})
ipcMain.handle('job:resolve',(_event,choice)=>worker?.stdin.write(JSON.stringify({type:'resolve_conflict',choice})+'\n'))
