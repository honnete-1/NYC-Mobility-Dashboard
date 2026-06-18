// Javascript file for fetching backend data and for displaying charts

// Base API address 
const API_BASE = window.location.origin;

// References to our ApexChart instances so we can update them on filter change
let hourlyChart = null;
let zonesChart = null;
let tippingChart = null;

// Run initial configurations when the page loads
document.addEventListener('DOMContentLoaded', () => {
    populateHourDropdowns();
    setupEventListeners();
    
    // Load initial unfiltered data
    fetchDashboardData();
});

// Populates hour drop boxes from 0 to 23
function populateHourDropdowns() {
    const minSelect = document.getElementById('filter-hour-min');
    const maxSelect = document.getElementById('filter-hour-max');
    
    for (let h = 0; h < 24; h++) {
        const hString = h < 10 ? '0' + h : '' + h;
        
        // Start hour select options
        const optMin = document.createElement('option');
        optMin.value = h;
        optMin.textContent = hString + ':00';
        minSelect.appendChild(optMin);
        
        // End hour select options
        const optMax = document.createElement('option');
        optMax.value = h;
        optMax.textContent = hString + ':00';
        
        // Default end hour to 23:00
        if (h === 23) {
            optMax.selected = true;
        }
        maxSelect.appendChild(optMax);
    }
}

// Bind controls to apply filters and switch theme modes
function setupEventListeners() {
    const applyBtn = document.getElementById('apply-filters-btn');
    const dropdownMenu = document.getElementById('apply-dropdown-menu');

    // Toggle dropdown visibility
    applyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownMenu.classList.toggle('show');
        applyBtn.classList.toggle('active');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown-button-container')) {
            dropdownMenu.classList.remove('show');
            applyBtn.classList.remove('active');
        }
    });

    // Handle dropdown action clicks
    const boroughSelect = document.getElementById('filter-borough');
    const minHourSelect = document.getElementById('filter-hour-min');
    const maxHourSelect = document.getElementById('filter-hour-max');
    const rateSelect = document.getElementById('filter-ratecode');

    const closeMenu = () => {
        dropdownMenu.classList.remove('show');
        applyBtn.classList.remove('active');
    };

    // Action: Apply current filters
    document.getElementById('action-apply').addEventListener('click', () => {
        closeMenu();
        fetchDashboardData();
    });

    // Action: Reset filters to default
    document.getElementById('action-reset').addEventListener('click', () => {
        boroughSelect.value = 'All';
        minHourSelect.value = '0';
        maxHourSelect.value = '23';
        rateSelect.value = 'All';
        closeMenu();
        fetchDashboardData();
    });

    // Preset: Morning Rush
    document.getElementById('preset-morning').addEventListener('click', () => {
        boroughSelect.value = 'Manhattan';
        minHourSelect.value = '7';
        maxHourSelect.value = '9';
        rateSelect.value = '1';
        closeMenu();
        fetchDashboardData();
    });

    // Preset: Evening Rush
    document.getElementById('preset-evening').addEventListener('click', () => {
        boroughSelect.value = 'Manhattan';
        minHourSelect.value = '16';
        maxHourSelect.value = '18';
        rateSelect.value = '1';
        closeMenu();
        fetchDashboardData();
    });

    // Preset: JFK Airport
    document.getElementById('preset-jfk').addEventListener('click', () => {
        boroughSelect.value = 'All';
        minHourSelect.value = '0';
        maxHourSelect.value = '23';
        rateSelect.value = '2';
        closeMenu();
        fetchDashboardData();
    });

    // Preset: Newark Airport
    document.getElementById('preset-newark').addEventListener('click', () => {
        boroughSelect.value = 'All';
        minHourSelect.value = '0';
        maxHourSelect.value = '23';
        rateSelect.value = '3';
        closeMenu();
        fetchDashboardData();
    });
    
    // Select selectors
    const lightBtn = document.getElementById('theme-light-btn');
    const darkBtn = document.getElementById('theme-dark-btn');
    const modeLabel = document.getElementById('theme-mode-label');
    
    // Event listener for Light Theme Circle
    lightBtn.addEventListener('click', () => {
        const body = document.body;
        body.classList.add('light-theme');
        body.classList.remove('dark-theme');
        
        lightBtn.classList.add('active');
        darkBtn.classList.remove('active');
        modeLabel.textContent = 'Light Mode';
        
        updateChartThemes('light');
    });
    
    // Event listener for Dark Theme Circle
    darkBtn.addEventListener('click', () => {
        const body = document.body;
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
        
        darkBtn.classList.add('active');
        lightBtn.classList.remove('active');
        modeLabel.textContent = 'Dark Mode';
        
        updateChartThemes('dark');
    });
}

// Update the theme mode on all charts on-the-fly
function updateChartThemes(mode) {
    if (hourlyChart) {
        hourlyChart.updateOptions({ theme: { mode: mode } });
    }
    if (zonesChart) {
        zonesChart.updateOptions({ theme: { mode: mode } });
    }
    if (tippingChart) {
        tippingChart.updateOptions({ theme: { mode: mode } });
    }
}

// Helper to check what theme is currently active in the DOM
function getCurrentThemeMode() {
    return document.body.classList.contains('dark-theme') ? 'dark' : 'light';
}

// Calls Flask backend to get data and draws updates our dashboard
async function fetchDashboardData() {
    // Get currently selected filter values
    const borough = document.getElementById('filter-borough').value;
    const hourMin = document.getElementById('filter-hour-min').value;
    const hourMax = document.getElementById('filter-hour-max').value;
    const rateCode = document.getElementById('filter-ratecode').value;
    
    // Show loading while we fetch
    document.getElementById('kpi-total-rides').textContent = 'Loading...';
    document.getElementById('kpi-avg-fare').textContent = 'Loading...';
    document.getElementById('kpi-avg-tip-percent').textContent = 'Loading...';
    document.getElementById('kpi-avg-speed').textContent = 'Loading...';
    
    const url = `${API_BASE}/api/dashboard?borough=${borough}&hour_min=${hourMin}&hour_max=${hourMax}&rate_code=${rateCode}`;
    
    try {
        console.log(`Requesting data: ${url}`);
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Feed data to KPIs and ApexCharts
        updateKPIs(data.kpis);
        renderHourlyTrendsChart(data.hourly_trends);
        renderTopZonesChart(data.top_zones);
        renderTippingTrendsChart(data.tipping_trends);
        
    } catch (err) {
        console.error('Failed to get dashboard metrics:', err);
        alert('Could not load dashboard data. Make sure backend flask server is running!');
    }
}

// Updates numeric numbers on the KPI cards
function updateKPIs(kpis) {
    if (!kpis) return;
    
    const totalRides = kpis.total_trips || 0;
    const avgFare = kpis.avg_fare || 0;
    const avgTipPercent = kpis.avg_tip_percent || 0;
    const avgSpeed = kpis.avg_speed || 0;
    
    // Put them in cards with commas/currencies
    document.getElementById('kpi-total-rides').textContent = totalRides.toLocaleString();
    document.getElementById('kpi-avg-fare').textContent = `$${avgFare.toFixed(2)}`;
    document.getElementById('kpi-avg-tip-percent').textContent = `${avgTipPercent.toFixed(2)}%`;
    document.getElementById('kpi-avg-speed').textContent = `${avgSpeed.toFixed(1)} MPH`;
}

// Renders line and column chart for hourly speed vs volume
function renderHourlyTrendsChart(trends) {
    if (!trends) return;
    
    const hours = trends.map(t => t.pickup_hour + ':00');
    const speeds = trends.map(t => t.avg_speed_mph);
    const volumes = trends.map(t => t.total_trips);
    
    const options = {
        series: [
            {
                name: 'Total Rides',
                type: 'column',
                data: volumes
            },
            {
                name: 'Average Speed (MPH)',
                type: 'line',
                data: speeds
            }
        ],
        chart: {
            height: 350,
            type: 'line',
            toolbar: { show: false },
            background: 'transparent'
        },
        theme: { mode: getCurrentThemeMode() },
        stroke: {
            width: [0, 4],
            curve: 'smooth'
        },
        colors: ['#00509d', '#fdc500'], // steel azure and school bus yellow
        plotOptions: {
            bar: {
                columnWidth: '50%',
                borderRadius: 4
            }
        },
        fill: {
            opacity: [0.4, 1]
        },
        xaxis: {
            categories: hours,
            title: { text: 'Hour of Day' }
        },
        yaxis: [
            {
                title: { text: 'Total Rides' },
                labels: {
                    formatter: function (val) {
                        return val.toLocaleString();
                    }
                }
            },
            {
                opposite: true,
                title: { text: 'Average Speed (MPH)' },
                min: 0,
                max: 30
            }
        ],
        grid: {
            borderColor: getCurrentThemeMode() === 'dark' ? '#1f2e4d' : '#e2e8f0'
        },
        tooltip: {
            theme: getCurrentThemeMode()
        }
    };
    
    if (hourlyChart) {
        hourlyChart.updateOptions(options);
    } else {
        hourlyChart = new ApexCharts(document.querySelector("#hourly-trends-chart"), options);
        hourlyChart.render();
    }
}

// Renders the horizontal bars for busiest zones
function renderTopZonesChart(zones) {
    if (!zones) return;
    
    const names = zones.map(z => z.zone_name);
    const counts = zones.map(z => z.total_trips);
    
    const options = {
        series: [{
            name: 'Total Pickups',
            data: counts
        }],
        chart: {
            type: 'bar',
            height: 350,
            toolbar: { show: false },
            background: 'transparent'
        },
        theme: { mode: getCurrentThemeMode() },
        plotOptions: {
            bar: {
                horizontal: true,
                barHeight: '65%',
                borderRadius: 4
            }
        },
        colors: ['#ffd500'], // gold accent color
        xaxis: {
            categories: names,
            labels: {
                formatter: function (val) {
                    return val.toLocaleString();
                }
            }
        },
        grid: {
            borderColor: getCurrentThemeMode() === 'dark' ? '#1f2e4d' : '#e2e8f0'
        },
        tooltip: {
            theme: getCurrentThemeMode()
        }
    };
    
    if (zonesChart) {
        zonesChart.updateOptions(options);
    } else {
        zonesChart = new ApexCharts(document.querySelector("#top-zones-chart"), options);
        zonesChart.render();
    }
}

// Renders the tipping percentage comparison chart
function renderTippingTrendsChart(tipping) {
    if (!tipping) return;
    
    const names = tipping.map(t => t.payment_name);
    const tips = tipping.map(t => t.avg_tip_percent);
    
    const options = {
        series: [{
            name: 'Avg Tip Percent',
            data: tips
        }],
        chart: {
            type: 'bar',
            height: 350,
            toolbar: { show: false },
            background: 'transparent'
        },
        theme: { mode: getCurrentThemeMode() },
        plotOptions: {
            bar: {
                columnWidth: '45%',
                borderRadius: 6
            }
        },
        colors: ['#003f88'], // french blue color
        xaxis: {
            categories: names
        },
        yaxis: {
            title: { text: 'Tip Percentage (%)' },
            labels: {
                formatter: function (val) {
                    return val.toFixed(1) + '%';
                }
            }
        },
        grid: {
            borderColor: getCurrentThemeMode() === 'dark' ? '#1f2e4d' : '#e2e8f0'
        },
        tooltip: {
            theme: getCurrentThemeMode()
        }
    };
    
    if (tippingChart) {
        tippingChart.updateOptions(options);
    } else {
        tippingChart = new ApexCharts(document.querySelector("#tipping-trends-chart"), options);
        tippingChart.render();
    }
}
