import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        neon: {
          50: '#e0f7ff',
          100: '#b3eeff',
          200: '#80e5ff',
          300: '#4ddbff',
          400: '#26d0ff',
          500: '#00c6ff',
          600: '#00a8d9',
          700: '#008bb3',
          800: '#006d8c',
          900: '#005066',
        },
        dark: {
          50: '#f0f0f0',
          100: '#d9d9d9',
          200: '#b3b3b3',
          300: '#8c8c8c',
          400: '#666666',
          500: '#404040',
          600: '#333333',
          700: '#262626',
          800: '#1a1a1a',
          900: '#0d0d0d',
          950: '#050505',
        },
      },
    },
  },
  plugins: [],
}
export default config
