// ZenZone Main JavaScript

class ZenZone {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.initializeElements();
        this.initializeEventListeners();
    }

    initializeElements() {
        this.recordButton = document.getElementById('recordButton');
        this.stressLevel = document.getElementById('stressLevel');
        this.emotionDisplay = document.getElementById('emotionDisplay');
        this.activitySuggestion = document.getElementById('activitySuggestion');
        this.trendChart = document.getElementById('trendChart');
    }

    initializeEventListeners() {
        this.recordButton.addEventListener('click', () => this.toggleRecording());
    }

    async toggleRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            await this.stopRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.addEventListener('dataavailable', event => {
                this.audioChunks.push(event.data);
            });

            this.mediaRecorder.addEventListener('stop', () => this.processAudio());

            this.mediaRecorder.start();
            this.isRecording = true;
            this.recordButton.classList.add('recording');
            this.recordButton.textContent = 'Stop Recording';
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Unable to access microphone. Please ensure microphone permissions are granted.');
        }
    }

    async stopRecording() {
        this.mediaRecorder.stop();
        this.isRecording = false;
        this.recordButton.classList.remove('recording');
        this.recordButton.textContent = 'Start Recording';
    }

    async processAudio() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', audioBlob);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const result = await response.json();
            this.updateUI(result);
        } catch (error) {
            console.error('Error processing audio:', error);
            alert('Error processing audio. Please try again.');
        }
    }

    updateUI(result) {
        // Update stress level indicator
        const stressPercentage = result.stress_score;
        this.stressLevel.style.width = `${stressPercentage}%`;
        
        // Update emotion display
        this.emotionDisplay.textContent = result.emotion;
        
        // Update activity suggestion
        this.activitySuggestion.innerHTML = this.getActivityHTML(result.activity);
        
        // Update trend chart if data is provided
        if (result.trend_data) {
            this.updateTrendChart(result.trend_data);
        }
    }

    getActivityHTML(activity) {
        const activityIcons = {
            'meditation': '🧘‍♀️',
            'breathing': '🌬️',
            'music': '🎧',
            'nature': '🌲'
        };

        return `
            <div class="activity-card">
                <h3>${activityIcons[activity.type] || '✨'} ${activity.title}</h3>
                <p>${activity.description}</p>
                ${activity.content ? `<div class="activity-content">${activity.content}</div>` : ''}
            </div>
        `;
    }

    updateTrendChart(trendData) {
        if (!this.chart) {
            this.initializeTrendChart();
        }
        
        // Update chart with new data
        this.chart.data.labels = trendData.labels;
        this.chart.data.datasets[0].data = trendData.values;
        this.chart.update();
    }

    initializeTrendChart() {
        const ctx = this.trendChart.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Stress Level Over Time',
                    data: [],
                    borderColor: '#6F4E37',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

// Initialize ZenZone when the document is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.zenZone = new ZenZone();
});