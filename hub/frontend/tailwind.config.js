/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  safelist: ["hidden", "grid", "flex"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#171326",
          900: "#221a39",
          800: "#312352",
          700: "#493071",
          600: "#6946a4",
          500: "#825ee7",
          100: "#eee9ff",
          50: "#f8f5ff"
        }
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Avenir Next", "Helvetica Neue", "Arial"]
      }
    }
  },
  plugins: []
};
