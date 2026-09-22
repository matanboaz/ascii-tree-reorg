import {contextBridge,ipcRenderer} from 'electron'
contextBridge.exposeInMainWorld('desktop',{
 chooseDirectory:()=>ipcRenderer.invoke('dialog:directory'),
 startJob:(request:unknown)=>ipcRenderer.invoke('job:start',request),
 cancelJob:()=>ipcRenderer.invoke('job:cancel'),
 resolveConflict:(choice:string|null)=>ipcRenderer.invoke('job:resolve',choice),
 onEvent:(callback:(event:unknown)=>void)=>{const listener=(_event:unknown,payload:unknown)=>callback(payload);ipcRenderer.on('job:event',listener);return()=>ipcRenderer.removeListener('job:event',listener)}
})
