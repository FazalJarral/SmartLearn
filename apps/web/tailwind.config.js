/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17202A",
        paper: "#FBFCFE",
        sage: "#4F756A",
        gold: "#B38728",
        mist: "#E7EEF2"
      }
    },
  },
  plugins: [],
};
