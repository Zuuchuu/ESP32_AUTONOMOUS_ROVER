/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                // Custom GCS color palette
                'gcs': {
                    'primary': '#0ea5e9',    // Sky blue
                    'secondary': '#6366f1',  // Indigo
                    'success': '#22c55e',    // Green
                    'warning': '#f59e0b',    // Amber
                    'danger': '#ef4444',     // Red
                    'dark': '#0f172a',       // Slate 900
                    'darker': '#020617',     // Slate 950
                    'card': '#1e293b',       // Slate 800
                    'border': '#334155',     // Slate 700
                }
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'spin-slow': 'spin 3s linear infinite',
            },
        },
    },
    plugins: [],
}
