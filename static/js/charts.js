// Dashboard Charts - InterviewForge AI

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardCharts();
});

function loadDashboardCharts() {
    const resumeChartCanvas = document.getElementById('resumeGrowthChart');
    const interviewChartCanvas = document.getElementById('interviewPerformanceChart');
    const skillChartCanvas = document.getElementById('skillsRadarChart');
    
    if (!resumeChartCanvas && !interviewChartCanvas && !skillChartCanvas) return;
    
    fetch('/analytics/api/dashboard/')
        .then(response => response.json())
        .then(data => {
            // Render Resume Growth Line Chart
            if (resumeChartCanvas) {
                const resumeData = data.chart_datasets.resume_growth;
                new Chart(resumeChartCanvas, {
                    type: 'line',
                    data: {
                        labels: resumeData.map(r => r.version),
                        datasets: [{
                            label: 'ATS Audit Grade',
                            data: resumeData.map(r => r.score),
                            borderColor: '#6366f1',
                            backgroundColor: 'rgba(99, 102, 241, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.3
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
                            x: { grid: { color: 'rgba(255,255,255,0.05)' } }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            }
            
            // Render Interview Score Line Chart
            if (interviewChartCanvas) {
                const interviewData = data.chart_datasets.interview_accuracy;
                new Chart(interviewChartCanvas, {
                    type: 'bar',
                    data: {
                        labels: interviewData.map(i => i.date),
                        datasets: [{
                            label: 'Interview Score',
                            data: interviewData.map(i => i.score),
                            backgroundColor: '#a855f7',
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { min: 0, max: 10, grid: { color: 'rgba(255,255,255,0.05)' } },
                            x: { grid: { color: 'rgba(255,255,255,0.05)' } }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            }
            
            // Render Skill Strengths Radar/Horizontal Bar Chart
            if (skillChartCanvas) {
                const skills = Object.keys(data.skill_progress);
                const scores = Object.values(data.skill_progress);
                
                new Chart(skillChartCanvas, {
                    type: 'bar',
                    data: {
                        labels: skills,
                        datasets: [{
                            label: 'Skill Proficiency (%)',
                            data: scores,
                            backgroundColor: ['#6366f1', '#a855f7', '#34d399', '#f87171', '#fbbf24'],
                            borderRadius: 6
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        scales: {
                            x: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
                            y: { grid: { display: false } }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error drawing analytics charts:', error);
        });
}
