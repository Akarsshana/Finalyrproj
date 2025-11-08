import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ExZero from "./ExZero";
import ExOne from "./ExOne";
import ExTwo from "./ExTwo";
import SpeechTest from "./SpeechTest";

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Default entry page */}
          <Route path="/" element={<ExZero />} />

          {/* Exercise routes */}
          <Route path="/exzero" element={<ExZero />} />
          <Route path="/exone" element={<ExOne />} />
          <Route path="/extwo" element={<ExTwo />} />

          {/* Optional Speech Test */}
          <Route path="/speech" element={<SpeechTest />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
