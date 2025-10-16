// static/js/recorder.js
let mediaRecorder;
let chunks = [];

const recordBtn = document.getElementById('recordBtn');
const status = document.getElementById('status');

recordBtn.onclick = async () => {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') {
    await startRecording();
  } else {
    stopRecording();
  }
};

async function startRecording(){
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  chunks = [];
  mediaRecorder.ondataavailable = e => chunks.push(e.data);
  mediaRecorder.onstop = onStop;
  mediaRecorder.start();
  recordBtn.innerText = 'Stop';
  status.innerText = 'Recording...';
  // auto stop after 8s (micro-stress sample)
  setTimeout(()=> {
    if(mediaRecorder && mediaRecorder.state === 'recording') stopRecording();
  }, 8000);
}

function stopRecording(){
  mediaRecorder.stop();
  recordBtn.innerText = 'Start Session 🎤';
  status.innerText = 'Processing...';
}

async function onStop(){
  const webmBlob = new Blob(chunks, { type: 'audio/webm' });

  // Decode the recorded WebM into an AudioBuffer, encode as WAV client-side,
  // and upload the WAV so the server doesn't need ffmpeg.
  try {
    const arrayBuffer = await webmBlob.arrayBuffer();
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    let audioBuffer;
    try {
      audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    } catch (decodeErr) {
      // Fallback: if decoding fails in the browser, upload the original WebM and let server handle conversion
      console.warn('decodeAudioData failed, falling back to upload WebM:', decodeErr);
      const form = new FormData();
      form.append('audio', webmBlob, 'sample.webm');
      status.innerText = 'Uploading...';
      const resp = await fetch('/analyze', { method: 'POST', body: form });
      if (!resp.ok) throw new Error('Upload failed: ' + resp.status + ' ' + resp.statusText);
      const data = await resp.json();
      status.innerText = 'Done';
      if (window.onAnalyzeResult) {
        try { window.onAnalyzeResult(data); } catch (e) { console.error(e); }
      }
      return;
    }

    const wavBlob = encodeWAV(audioBuffer);

    const form = new FormData();
    form.append('audio', wavBlob, 'sample.wav');

    status.innerText = 'Uploading...';
    const resp = await fetch('/analyze', { method: 'POST', body: form });
    if (!resp.ok) throw new Error('Upload failed: ' + resp.status + ' ' + resp.statusText);
    const data = await resp.json();
    // set status to Done before invoking UI callback
    status.innerText = 'Done';
    if (window.onAnalyzeResult) {
      try { window.onAnalyzeResult(data); } catch (e) { console.error(e); status.innerText = 'Error'; }
    }
  } catch (err) {
    console.error(err);
    status.innerText = 'Error';
  }
}

// Encode an AudioBuffer as a WAV Blob (16-bit PCM)
function encodeWAV(audioBuffer) {
  const numChannels = Math.min(2, audioBuffer.numberOfChannels);
  const sampleRate = audioBuffer.sampleRate;
  const samples = audioBuffer.length * numChannels;

  // Interleave channels
  let interleaved;
  if (numChannels === 2) {
    const ch0 = audioBuffer.getChannelData(0);
    const ch1 = audioBuffer.getChannelData(1);
    interleaved = new Float32Array(ch0.length + ch1.length);
    let idx = 0;
    for (let i = 0; i < ch0.length; i++) {
      interleaved[idx++] = ch0[i];
      interleaved[idx++] = ch1[i];
    }
  } else {
    interleaved = audioBuffer.getChannelData(0).slice(0);
  }

  // Convert float audio data to 16-bit PCM
  const buffer = new ArrayBuffer(44 + interleaved.length * 2);
  const view = new DataView(buffer);

  /* RIFF identifier */ writeString(view, 0, 'RIFF');
  /* file length */ view.setUint32(4, 36 + interleaved.length * 2, true);
  /* RIFF type */ writeString(view, 8, 'WAVE');
  /* format chunk identifier */ writeString(view, 12, 'fmt ');
  /* format chunk length */ view.setUint32(16, 16, true);
  /* sample format (raw) */ view.setUint16(20, 1, true);
  /* channel count */ view.setUint16(22, numChannels, true);
  /* sample rate */ view.setUint32(24, sampleRate, true);
  /* byte rate (sampleRate * blockAlign) */ view.setUint32(28, sampleRate * numChannels * 2, true);
  /* block align (channel count * bytes per sample) */ view.setUint16(32, numChannels * 2, true);
  /* bits per sample */ view.setUint16(34, 16, true);
  /* data chunk identifier */ writeString(view, 36, 'data');
  /* data chunk length */ view.setUint32(40, interleaved.length * 2, true);

  // Write PCM samples
  let offset = 44;
  for (let i = 0; i < interleaved.length; i++, offset += 2) {
    // clamp
    let s = Math.max(-1, Math.min(1, interleaved[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new Blob([view], { type: 'audio/wav' });
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}
