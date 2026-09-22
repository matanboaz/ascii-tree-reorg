import path from 'node:path'

export type JobRequest={operation:'generate';source:string;include_files?:boolean;max_depth?:number;indent_width?:number}|{operation:'reconstruct';source:string;destination:string;tree:string}
const own=(value:object,key:string)=>Object.prototype.hasOwnProperty.call(value,key)
export function validateJobRequest(value:unknown):JobRequest{
 if(!value||typeof value!=='object'||Array.isArray(value))throw new TypeError('Invalid job request.')
 const request=value as Record<string,unknown>
 if(request.operation!=='generate'&&request.operation!=='reconstruct')throw new TypeError('Unknown operation.')
 if(typeof request.source!=='string'||!request.source.trim())throw new TypeError('A source folder is required.')
 if(request.operation==='reconstruct'){
  if(typeof request.destination!=='string'||!request.destination.trim())throw new TypeError('A destination folder is required.')
  if(typeof request.tree!=='string'||!request.tree.trim())throw new TypeError('A tree is required.')
  return {operation:'reconstruct',source:request.source,destination:request.destination,tree:request.tree}
 }
 if(own(request,'include_files')&&typeof request.include_files!=='boolean')throw new TypeError('include_files must be boolean.')
 if(own(request,'max_depth')&&(!Number.isInteger(request.max_depth)||(request.max_depth as number)<1))throw new TypeError('max_depth must be a positive integer.')
 if(own(request,'indent_width')&&(!Number.isInteger(request.indent_width)||(request.indent_width as number)<2))throw new TypeError('indent_width must be an integer of at least 2.')
 return {operation:'generate',source:request.source,...(typeof request.include_files==='boolean'?{include_files:request.include_files}:{}),...(typeof request.max_depth==='number'?{max_depth:request.max_depth}:{}),...(typeof request.indent_width==='number'?{indent_width:request.indent_width}:{})}
}
export function validateConflictChoice(value:unknown):string|null{
 if(value===null)return null
 if(typeof value!=='string'||!path.isAbsolute(value))throw new TypeError('Conflict choice must be an absolute candidate path or null.')
 return value
}
export function isTrustedRendererUrl(value:string,devServerUrl?:string):boolean{
 try{
  const url=new URL(value)
  if(url.protocol==='file:')return true
  if(!devServerUrl)return false
  const dev=new URL(devServerUrl)
  return url.origin===dev.origin
 }catch{return false}
}
