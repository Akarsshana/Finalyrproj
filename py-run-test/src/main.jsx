// index.jsx ✅
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

// ✅ StrictMode removed — this prevents React from mounting twice in dev mode,
// which was causing your camera/socket to lag or show blank.
createRoot(document.getElementById("root")).render(
  <App />  // App already contains BrowserRouter
);
