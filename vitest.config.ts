import {defineConfig} from 'vitest/config'
export default defineConfig({test:{include:['desktop/**/*.test.{ts,tsx}'],exclude:['dist/**','dist-electron/**','release/**']}})
