import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import io from "socket.io-client";
import { useSpeechSynthesis } from "react-speech-kit";

const socket = io("http://localhost:5000");

function ExTwo() {
  const [videoFrame, setVideoFrame] = useState(null);
  const [holdTime, setHoldTime] = useState(0);
  const [streaming, setStreaming] = useState(false);
  const [paused, setPaused] = useState(false);
  const [sessionCompleted, setSessionCompleted] = useState(false);
  const [countdown, setCountdown] = useState(30);
  const [resting, setResting] = useState(false);
  const [accuracy, setAccuracy] = useState(0);

  const navigate = useNavigate();
  const { speak, voices } = useSpeechSynthesis();

  const targetHold = 10; // seconds to hold for session completion

  // 🔹 Listen to backend feed
  useEffect(() => {
    socket.on("joinhands_feed", (data) => {
      if (!sessionCompleted && !paused && streaming) {
        setVideoFrame(`data:image/jpeg;base64,${data.frame}`);
        if (data.hold_time !== undefined) setHoldTime(data.hold_time);
        if (data.accuracy !== undefined)
          setAccuracy(data.accuracy.toFixed(1));

        if (data.hold_time >= targetHold && !sessionCompleted) {
          setSessionCompleted(true);
          setStreaming(false);
          setResting(true);
          speak({
            text: "Excellent! You held your position for 10 seconds. Take a short break.",
            voice: voices[0],
          });
        }

        if (data.hold_time >= targetHold / 2 && data.hold_time < targetHold) {
          speak({
            text: "Halfway there! Keep holding your arms up!",
            voice: voices[0],
          });
        }
      }
    });

    return () => socket.off("joinhands_feed");
  }, [sessionCompleted, paused, streaming, speak, voices]);

  // 🔹 Rest timer
  useEffect(() => {
    let timer;
    if (resting && countdown > 0) {
      timer = setInterval(() => setCountdown((prev) => prev - 1), 1000);
    } else if (countdown === 0 && resting) {
      setResting(false);
      setCountdown(30);
    }
    return () => clearInterval(timer);
  }, [resting, countdown]);

  const startVideoFeed = () => {
    setHoldTime(0);
    setAccuracy(0);
    setSessionCompleted(false);
    setResting(false);
    setCountdown(30);
    setStreaming(true);
    setPaused(false);
    speak({
      text: "Let's begin! Raise your hands above your head and hold the position.",
      voice: voices[0],
    });
    socket.emit("start_joinhands");
  };

  const handleRetry = () => startVideoFeed();
  const handleNext = () => navigate("/exthree");
  const handleBack = () => navigate("/exone");
  const togglePausePlay = () => setPaused((prev) => !prev);

  const progress = Math.min((holdTime / targetHold) * 100, 100);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        width: "100vw",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding: "16px",
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "18px",
          padding: "0 12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: "46px",
              height: "46px",
              background: "#4FC3F7",
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "22px",
            }}
          >
            🙌
          </div>
          <h1
            style={{
              fontSize: "24px",
              fontWeight: "bold",
              color: "white",
              margin: 0,
            }}
          >
            MotionAid
          </h1>
        </div>

        <button
          style={{
            padding: "8px 16px",
            background: "#4FC3F7",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "15px",
            fontWeight: "500",
          }}
        >
          Motor Skills
        </button>
      </div>

      <p
        style={{
          textAlign: "center",
          color: "rgba(255,255,255,0.9)",
          fontSize: "14px",
          marginBottom: "18px",
        }}
      >
        Camera-based motion tracking for body hold exercises
      </p>

      <div
        style={{
          flex: 1,
          display: "grid",
          gridTemplateColumns: "1.5fr 1fr",
          gap: "24px",
          width: "100%",
          height: "100%",
          alignItems: "stretch",
        }}
      >
        {/* Left Panel */}
        <div
          style={{
            background: "white",
            borderRadius: "14px",
            padding: "20px",
            boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div
            style={{
              background: "#f0f2f5",
              borderRadius: "12px",
              padding: "16px",
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {videoFrame && streaming ? (
              <img
                src={videoFrame}
                alt="Hold Tracking"
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  borderRadius: "12px",
                }}
              />
            ) : (
              <>
                <div style={{ fontSize: "60px", color: "#8892a6" }}>📷</div>
                <p style={{ color: "#8892a6", fontSize: "14px" }}>
                  Camera feed will appear here
                </p>
              </>
            )}
          </div>

          {/* Controls */}
          <div style={{ marginTop: "10px" }}>
            {!streaming && !resting && (
              <button
                onClick={startVideoFeed}
                style={{
                  width: "100%",
                  padding: "12px",
                  fontSize: "16px",
                  cursor: "pointer",
                  background: "#4FC3F7",
                  color: "white",
                  border: "none",
                  borderRadius: "8px",
                  fontWeight: "600",
                }}
              >
                ▶ Start Exercise
              </button>
            )}

            {streaming && !resting && (
              <div style={{ textAlign: "center" }}>
                <button
                  onClick={togglePausePlay}
                  style={{
                    padding: "10px 24px",
                    background: "#f0f2f5",
                    color: "#667eea",
                    border: "none",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontSize: "18px",
                    marginTop: "10px",
                  }}
                >
                  {paused ? "▶️" : "⏸️"}
                </button>
              </div>
            )}

            {resting && (
              <div style={{ textAlign: "center", marginTop: "10px" }}>
                <div
                  style={{
                    fontSize: "20px",
                    fontWeight: "bold",
                    color: "#667eea",
                    marginBottom: "16px",
                  }}
                >
                  🏖️ Take Rest: {countdown} sec 🏖️
                </div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    gap: "10px",
                    marginBottom: "16px",
                  }}
                >
                  <button
                    onClick={() =>
                      setCountdown((prev) => (prev > 5 ? prev - 5 : prev))
                    }
                    style={{
                      padding: "8px 16px",
                      background: "#ff4d4d",
                      color: "white",
                      border: "none",
                      borderRadius: "6px",
                      cursor: "pointer",
                    }}
                  >
                    ⏪ -5 sec
                  </button>
                  <button
                    onClick={() => setCountdown((prev) => prev + 5)}
                    style={{
                      padding: "8px 16px",
                      background: "#4da6ff",
                      color: "white",
                      border: "none",
                      borderRadius: "6px",
                      cursor: "pointer",
                    }}
                  >
                    ⏩ +5 sec
                  </button>
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: "10px",
                    justifyContent: "center",
                  }}
                >
                  <button
                    onClick={handleRetry}
                    style={{
                      flex: 1,
                      padding: "12px",
                      background: "#f0f2f5",
                      color: "#667eea",
                      border: "2px solid #667eea",
                      borderRadius: "8px",
                      cursor: "pointer",
                      fontWeight: "600",
                    }}
                  >
                    🔄 Retry
                  </button>
                  <button
                    onClick={handleNext}
                    style={{
                      flex: 1,
                      padding: "12px",
                      background: "#4FC3F7",
                      color: "white",
                      border: "none",
                      borderRadius: "8px",
                      cursor: "pointer",
                      fontWeight: "600",
                    }}
                  >
                    ▶ Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div
          style={{
            background: "white",
            borderRadius: "14px",
            padding: "20px",
            boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h2
              style={{
                fontSize: "18px",
                fontWeight: "600",
                color: "#2c3e50",
                marginBottom: "16px",
              }}
            >
              Session Progress
            </h2>

            <div style={{ marginBottom: "12px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "13px",
                  color: "#6c757d",
                  marginBottom: "6px",
                }}
              >
                <span>Hold Duration</span>
                <span style={{ color: "#2c3e50", fontWeight: "bold" }}>
                  {holdTime.toFixed(1)}s / {targetHold}s
                </span>
              </div>
              <div
                style={{
                  background: "#e9ecef",
                  height: "6px",
                  borderRadius: "4px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${progress}%`,
                    background: "#4FC3F7",
                    height: "100%",
                    transition: "width 0.3s",
                  }}
                />
              </div>
            </div>

            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: "13px",
                  color: "#6c757d",
                  marginBottom: "6px",
                }}
              >
                <span>Accuracy</span>
                <span style={{ color: "#2c3e50", fontWeight: "bold" }}>
                  {accuracy}%
                </span>
              </div>
              <div
                style={{
                  background: "#e9ecef",
                  height: "6px",
                  borderRadius: "4px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${accuracy}%`,
                    background: "#4FC3F7",
                    height: "100%",
                    transition: "width 0.3s",
                  }}
                />
              </div>
            </div>
          </div>

          {/* Tips */}
          <div
            style={{
              background: "linear-gradient(135deg, #4FC3F7 0%, #4DD0E1 100%)",
              borderRadius: "14px",
              padding: "20px",
              color: "white",
              boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
            }}
          >
            <h2
              style={{
                fontSize: "18px",
                fontWeight: "600",
                marginBottom: "16px",
              }}
            >
              Exercise Tips
            </h2>
            {[
              "Stand straight facing the camera",
              "Raise both hands above your head",
              "Hold steady for 10 seconds",
              "Keep your arms close together for better accuracy",
            ].map((tip, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  fontSize: "13px",
                  marginBottom: "8px",
                }}
              >
                <span style={{ fontSize: "16px" }}>✓</span>
                {tip}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          textAlign: "center",
          marginTop: "10px",
          color: "white",
          fontSize: "13px",
        }}
      >
        💚 MotionAid — Smarter Recovery for Every Stroke Survivor
        <br />
        <span style={{ opacity: 0.8 }}>
          © 2025 MotionAid. Supporting your journey to recovery.
        </span>
      </div>
    </div>
  );
}

export default ExTwo;
