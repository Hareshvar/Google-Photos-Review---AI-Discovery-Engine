/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "google-blue": "#4285F4",
        "google-blue-tint": "#E8F0FE",
        "google-red": "#EA4335",
        "google-red-tint": "#FCE8E6",
        "google-yellow": "#FBBC04",
        "google-yellow-tint": "#FEF7E0",
        "google-green": "#34A853",
        "google-green-tint": "#E6F4EA",
        "surface-bg": "#F8F9FA",
        "surface-card": "#FFFFFF",
        "surface-container": "#EFEDF1",
        "surface-container-low": "#F4F3F7",
        "surface-container-lowest": "#FFFFFF",
        "on-surface": "#202124",
        "on-surface-variant": "#5F6368",
        "on-secondary-container": "#5F6368",
        "border-subtle": "#DADCE0",
        "primary-container": "#1A73E8",
        "on-primary-container": "#FFFFFF",
        "tertiary": "#006D2C",
      },
      fontFamily: {
        sans: ["Inter", "Roboto Flex", "Google Sans", "sans-serif"],
        headline: ["Roboto Flex", "Google Sans", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      }
    },
  },
  plugins: [],
};
