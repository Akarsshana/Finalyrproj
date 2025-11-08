// src/SpeechTest.jsx
import React from "react";
import { speakText } from "./utils/speech";

function SpeechTest() {
  return (
    <button
      onClick={() => speakText("Exercise started!")}
      style={{
        backgroundColor: "#007bff",
        color: "white",
        padding: "0px 0px",
        border: "none",
        borderRadius: "0x",
        cursor: "pointer",
      }}
    >
      
    </button>
  );
}

export default SpeechTest;
