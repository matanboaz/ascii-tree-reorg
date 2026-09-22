import {stat} from 'node:fs/promises'
import path from 'node:path'
const artifact=path.resolve(process.argv[2]||'dist/linux-unpacked/resources/app.asar')
const maximum=Number(process.env.MAX_APP_ASAR_MB||50)*1024*1024
const {size}=await stat(artifact)
if(size>maximum)throw new Error(`${artifact} is ${(size/1024/1024).toFixed(1)} MB; limit is ${(maximum/1024/1024).toFixed(1)} MB`)
console.log(`Packaged app size: ${(size/1024/1024).toFixed(1)} MB (limit ${(maximum/1024/1024).toFixed(1)} MB)`)
