/* Facial Attendance Management System - Frontend App JS */

let activeVideoStream = null;
let liveStreamInterval = null;

// TOAST NOTIFICATIONS UI
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-circle-info';
    if (type === 'success') icon = 'fa-circle-check';
    if (type === 'danger') icon = 'fa-circle-xmark';
    if (type === 'warning') icon = 'fa-triangle-exclamation';

    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <div style="flex:1;">${message}</div>
        <i class="fa-solid fa-xmark" style="cursor:pointer;" onclick="this.parentElement.remove()"></i>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 4500);
}

// WEBCAM CAMERA UTILITIES
async function startWebcam(videoElemId) {
    const video = document.getElementById(videoElemId);
    if (!video) return false;

    try {
        stopWebcam(); // Close any prior stream
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: 'user' },
            audio: false
        });
        video.srcObject = stream;
        activeVideoStream = stream;
        await video.play();
        return true;
    } catch (err) {
        console.error("Camera Error:", err);
        showToast("Camera Access Error: Please ensure webcam permissions are granted.", "danger");
        return false;
    }
}

function stopWebcam() {
    if (activeVideoStream) {
        activeVideoStream.getTracks().forEach(track => track.stop());
        activeVideoStream = null;
    }
    if (liveStreamInterval) {
        clearInterval(liveStreamInterval);
        liveStreamInterval = null;
    }
}

function captureFrameBase64(videoElemId) {
    const video = document.getElementById(videoElemId);
    if (!video || !video.videoWidth) return null;

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.85);
}

// STUDENT FACIAL REGISTRATION FLOW
async function startFaceRegistration() {
    const statusText = document.getElementById('reg-status-text');
    const startBtn = document.getElementById('btn-start-reg');
    const progressFill = document.getElementById('reg-progress-fill');

    if (startBtn) startBtn.disabled = true;
    if (statusText) statusText.innerText = "Opening webcam...";

    const started = await startWebcam('reg-video');
    if (!started) {
        if (startBtn) startBtn.disabled = false;
        if (statusText) statusText.innerText = "Webcam failed to open.";
        return;
    }

    const capturedFrames = [];
    const totalSamples = 10;

    for (let i = 1; i <= totalSamples; i++) {
        if (statusText) statusText.innerText = `Capturing face sample ${i} of ${totalSamples}... (Adjust angle/expression)`;
        if (progressFill) progressFill.style.width = `${(i / totalSamples) * 100}%`;

        await new Promise(r => setTimeout(r, 600)); // Delay between captures
        const frame = captureFrameBase64('reg-video');
        if (frame) {
            capturedFrames.push(frame);
        }
    }

    stopWebcam();
    if (statusText) statusText.innerText = "Processing & registering facial embeddings...";

    try {
        const resp = await fetch('/api/register-face', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ images: capturedFrames })
        });
        const res = await resp.json();

        if (res.success) {
            showToast(res.message, "success");
            if (statusText) statusText.innerText = "Facial Registration Complete!";
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showToast(res.message, "danger");
            if (statusText) statusText.innerText = `Registration Failed: ${res.message}`;
            if (startBtn) startBtn.disabled = false;
        }
    } catch (e) {
        showToast("Network/Server Error during registration.", "danger");
        if (startBtn) startBtn.disabled = false;
    }
}

// STUDENT SELF ATTENDANCE MARKING
async function markSelfAttendance(sessionId) {
    const markBtn = document.getElementById(`btn-mark-${sessionId}`);
    if (markBtn) markBtn.disabled = true;

    showToast("Starting facial verification...", "info");

    const started = await startWebcam('self-att-video');
    if (!started) {
        if (markBtn) markBtn.disabled = false;
        return;
    }

    // Wait 1 second for camera focus
    await new Promise(r => setTimeout(r, 1000));
    const frame = captureFrameBase64('self-att-video');
    stopWebcam();

    if (!frame) {
        showToast("Failed to capture frame from webcam.", "danger");
        if (markBtn) markBtn.disabled = false;
        return;
    }

    try {
        const resp = await fetch('/api/mark-self-attendance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, image: frame })
        });
        const res = await resp.json();

        if (res.success) {
            showToast(res.message, "success");
            setTimeout(() => window.location.reload(), 1200);
        } else {
            showToast(res.message, "danger");
            if (markBtn) markBtn.disabled = false;
        }
    } catch (e) {
        showToast("Server error during facial verification.", "danger");
        if (markBtn) markBtn.disabled = false;
    }
}

// STAFF LIVE FACIAL RECOGNITION FEED
async function startStaffLiveStream(sessionId) {
    const started = await startWebcam('staff-live-video');
    if (!started) return;

    showToast("Live attendance scanner active.", "success");
    const statusText = document.getElementById('live-status-badge');
    if (statusText) {
        statusText.innerText = "CAMERA STREAM ACTIVE";
        statusText.className = "badge badge-ongoing";
    }

    liveStreamInterval = setInterval(async () => {
        const frame = captureFrameBase64('staff-live-video');
        if (!frame) return;

        try {
            const resp = await fetch('/api/staff/live-recognize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, image: frame })
            });
            const res = await resp.json();

            if (res.success && res.data) {
                const d = res.data;
                document.getElementById('recognized-student-name').innerText = d.name || "Recognized";
                document.getElementById('recognized-confidence').innerText = `${d.confidence}%`;
                document.getElementById('recognized-status').innerText = d.attendance_message || "PRESENT";
                
                showToast(`Recognized ${d.name} (${d.confidence}%)`, "success");
                refreshStaffSessionAttendance(sessionId);
            } else if (res.data && res.data.name && res.data.name !== "Unknown") {
                document.getElementById('recognized-student-name').innerText = res.data.name;
                document.getElementById('recognized-confidence').innerText = `${res.data.confidence}%`;
                document.getElementById('recognized-status').innerText = res.message;
            }
        } catch (e) {
            console.error("Live recognition stream error:", e);
        }
    }, 2000);
}

async function refreshStaffSessionAttendance(sessionId) {
    try {
        const resp = await fetch(`/api/staff/session-attendance/${sessionId}`);
        const res = await resp.json();
        if (res.success && res.data) {
            const tableBody = document.getElementById('session-att-tbody');
            const countElem = document.getElementById('present-count');
            
            if (countElem) countElem.innerText = res.data.length;

            if (tableBody) {
                if (res.data.length === 0) {
                    tableBody.innerHTML = `<tr><td colspan="4" class="text-center">No attendance recorded yet.</td></tr>`;
                } else {
                    tableBody.innerHTML = res.data.map(item => `
                        <tr>
                            <td><strong>${item.student_id}</strong></td>
                            <td>${item.student_name}</td>
                            <td>${item.attendance_time}</td>
                            <td><span class="badge badge-present">PRESENT</span></td>
                        </tr>
                    `).join('');
                }
            }
        }
    } catch (e) {
        console.error("Error refreshing session attendance:", e);
    }
}

// STAFF START & STOP SESSION HANDLERS
async function handleStartSession(department, year, section, day, subject, hour) {
    try {
        const resp = await fetch('/api/staff/start-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ department, year, section, day, subject, hour })
        });
        const res = await resp.json();

        if (res.success) {
            showToast(res.message, "success");
            const sessionId = res.data.session_id;
            window.location.href = `/staff/attendance?session_id=${sessionId}`;
        } else {
            showToast(res.message, "danger");
        }
    } catch (e) {
        showToast("Server error when starting session.", "danger");
    }
}

async function handleStopSession(sessionId) {
    if (!confirm("Are you sure you want to stop and close this attendance session? Students will no longer be able to mark attendance.")) return;

    try {
        const resp = await fetch('/api/staff/stop-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        const res = await resp.json();

        if (res.success) {
            showToast(res.message, "success");
            stopWebcam();
            setTimeout(() => window.location.href = '/staff/dashboard', 1200);
        } else {
            showToast(res.message, "danger");
        }
    } catch (e) {
        showToast("Server error when closing session.", "danger");
    }
}

// NOTIFICATION READ HANDLER
async function markNotifRead(notifId, elem) {
    try {
        await fetch('/api/notifications/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notification_id: notifId })
        });
        if (elem) elem.style.opacity = '0.5';
    } catch (e) {}
}
