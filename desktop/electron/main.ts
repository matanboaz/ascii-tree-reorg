import {app,BrowserWindow,dialog,ipcMain} from 'electron'
import {spawn, type ChildProcessWithoutNullStreams} from 'node:child_process'
import {fileURLToPath} from 'node:url'
import path from 'node:path'

const here=path.dirname(fileURLToPath(import.meta.url))
let worker:ChildProcessWithoutNullStreams|undefined
function createWindow(){
 const win=new BrowserWindow({width:1240,height:850,minWidth:1000,minHeight:720,backgroundColor:'#f7f6f1',titleBarStyle:'hiddenInset',webPreferences:{preload:path.join(here,'preload.js'),contextIsolation:true,nodeIntegration:false}})
 if(process.env.VITE_DEV_SERVER_URL) win.loadURL(process.env.VITE_DEV_SERVER_URL)
 else win.loadFile(path.join(here,'../dist/index.html'))
}
app.whenReady().then(()=>{createWindow();app.on('activate',()=>{if(BrowserWindow.getAllWindows().length===0)createWindow()})})
app.on('window-all-closed',()=>{worker?.kill();if(process.platform!=='darwin')app.quit()})
ipcMain.handle('dialog:directory',async()=>{const result=await dialog.showOpenDialog({properties:['openDirectory']});return result.canceled?null:result.filePaths[0]})
ipcMain.handle('job:start',(event,request)=>{
 worker?.kill(); const packaged=path.join(process.resourcesPath,'desktop-sidecar',process.platform==='win32'?'ascii-tree-reorg-sidecar.exe':'ascii-tree-reorg-sidecar')
 const command=process.env.ASCII_TREE_REORG_PYTHON||(app.isPackaged?packaged:'python3'); const args=app.isPackaged?[]:['-m','ascii_tree_reorg.desktop.bridge']; worker=spawn(command,args,{stdio:['pipe','pipe','pipe']})
 let buffer=''; worker.stdout.on('data',chunk=>{buffer+=chunk.toString();const lines=buffer.split('\n');buffer=lines.pop()||'';for(const line of lines){if(line.trim())event.sender.send('job:event',JSON.parse(line))}})
 worker.stderr.on('data',chunk=>event.sender.send('job:event',{kind:'error',message:chunk.toString(),level:'error',current:0,total:0,data:{}}))
 worker.stdin.write(JSON.stringify(request)+'\n')
})
ipcMain.handle('job:cancel',()=>{worker?.kill();worker=undefined})
ipcMain.handle('job:resolve',(_event,choice)=>worker?.stdin.write(JSON.stringify({type:'resolve_conflict',choice})+'\n'))
