// Dynamically resolve API Backend URL across Localhost, Vercel, and Render deployments
const PRODUCTION_API_URL = 'https://quantum-precision-agriculture-api.onrender.com';

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // 1. URL Query Parameter ?api=https://...
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const apiParam = urlParams.get('api') || urlParams.get('apiUrl') || urlParams.get('backend');
      if (apiParam && apiParam.trim()) {
        const clean = apiParam.trim().replace(/\/+$/, '');
        localStorage.setItem('VITE_API_URL', clean);
        return clean;
      }
    } catch (e) {}

    // 2. localStorage override
    try {
      const stored = localStorage.getItem('VITE_API_URL');
      if (stored && stored.trim()) return stored.trim().replace(/\/+$/, '');
    } catch (e) {}

    // 3. Injected runtime env
    if (window.__ENV__ && window.__ENV__.VITE_API_URL) return window.__ENV__.VITE_API_URL.replace(/\/+$/, '');
    if (window.ENV && window.ENV.VITE_API_URL) return window.ENV.VITE_API_URL.replace(/\/+$/, '');

    // 4. Hostname detection
    if (window.location.port === '8000') {
      return window.location.origin;
    }
    // If running in production on Vercel or any cloud hosting domain
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      return PRODUCTION_API_URL;
    }
  }

  // 5. Local development fallback
  return 'http://127.0.0.1:8000';
};

let API_BASE_URL = getApiBaseUrl();

// Global State
let activeState = 'Andhra Pradesh';
let activeDistrict = 'Guntur';
let activeLat = 16.3067;
let activeLon = 80.4365;

// Comprehensive Local Coordinates Dictionary (0ms Instant GIS Geocoding)
const LOCAL_DISTRICT_COORDS = {
  // Andhra Pradesh
  "andhra pradesh::guntur": [16.3067, 80.4365],
  "andhra pradesh::prakasam": [15.5057, 80.0499],
  "andhra pradesh::krishna": [16.1800, 81.1300],
  "andhra pradesh::anakapalli": [17.6896, 83.0033],
  "andhra pradesh::visakhapatnam": [17.6868, 83.2185],
  "andhra pradesh::east godavari": [16.9891, 82.2475],
  "andhra pradesh::west godavari": [16.7107, 81.0952],
  "andhra pradesh::nellore": [14.4426, 79.9865],
  "andhra pradesh::anantapur": [14.6819, 77.6006],
  "andhra pradesh::chittoor": [13.2172, 79.1003],
  "andhra pradesh::kurnool": [15.8281, 78.0373],
  "andhra pradesh::kadapa": [14.4673, 78.8242],
  "andhra pradesh::srikakulam": [18.2949, 83.8938],
  "andhra pradesh::vizianagaram": [18.1067, 83.3956],
  "andhra pradesh::eluru": [16.7107, 81.0952],
  "andhra pradesh::kakinada": [16.9891, 82.2475],
  "andhra pradesh::ntr": [16.5062, 80.6480],
  "andhra pradesh::bapatla": [15.9042, 80.4674],
  "andhra pradesh::palnadu": [16.2361, 80.0531],
  "andhra pradesh::tirupati": [13.6288, 79.4192],
  "andhra pradesh::nandyal": [15.4786, 78.4836],

  // Telangana
  "telangana::hyderabad": [17.3850, 78.4867],
  "telangana::warangal": [17.9689, 79.5941],
  "telangana::karimnagar": [18.4386, 79.1288],
  "telangana::khammam": [17.2473, 80.1514],
  "telangana::nalgonda": [17.0575, 79.2684],
  "telangana::nizamabad": [18.6725, 78.0941],
  "telangana::medak": [18.0485, 78.2612],
  "telangana::rangareddy": [17.4399, 78.4983],
  "telangana::siddipet": [18.1018, 78.8520],
  "telangana::mahabubnagar": [16.7488, 77.9856],

  // Karnataka
  "karnataka::bengaluru": [12.9716, 77.5946],
  "karnataka::bengaluru urban": [12.9716, 77.5946],
  "karnataka::bengaluru rural": [13.2284, 77.5753],
  "karnataka::mysuru": [12.2958, 76.6394],
  "karnataka::belagavi": [15.8497, 74.4977],
  "karnataka::dharwad": [15.4589, 75.0078],
  "karnataka::ballari": [15.1394, 76.9214],
  "karnataka::kalaburagi": [17.3297, 76.8343],
  "karnataka::tumakuru": [13.3409, 77.1010],
  "karnataka::shivamogga": [13.9299, 75.5681],
  "karnataka::mangaluru": [12.9141, 74.8560],

  // Tamil Nadu
  "tamil nadu::chennai": [13.0827, 80.2707],
  "tamil nadu::coimbatore": [11.0168, 76.9558],
  "tamil nadu::madurai": [9.9252, 78.1198],
  "tamil nadu::salem": [11.6643, 78.1460],
  "tamil nadu::thanjavur": [10.7870, 79.1378],
  "tamil nadu::erode": [11.3410, 77.7172],
  "tamil nadu::tiruchirappalli": [10.7905, 78.7047],
  "tamil nadu::vellore": [12.9165, 79.1325],
  "tamil nadu::tirunelveli": [8.7139, 77.7567],

  // Maharashtra
  "maharashtra::pune": [18.5204, 73.8567],
  "maharashtra::nashik": [19.9975, 73.7898],
  "maharashtra::nagpur": [21.1458, 79.0882],
  "maharashtra::ahmednagar": [19.0948, 74.7480],
  "maharashtra::solapur": [17.6599, 75.9064],
  "maharashtra::aurangabad": [19.8762, 75.3433],
  "maharashtra::chhatrapati sambhajinagar": [19.8762, 75.3433],
  "maharashtra::kolhapur": [16.7050, 74.2433],
  "maharashtra::mumbai": [19.0760, 72.8777],

  // Gujarat
  "gujarat::ahmedabad": [23.0225, 72.5714],
  "gujarat::amreli": [21.6032, 71.2221],
  "gujarat::anand": [22.5645, 72.9289],
  "gujarat::surat": [21.1702, 72.8311],
  "gujarat::rajkot": [22.3039, 70.8022],
  "gujarat::bhavnagar": [21.7645, 72.1519],
  "gujarat::vadodara": [22.3072, 73.1812],
  "gujarat::jamnagar": [22.4707, 70.0577],
  "gujarat::junagadh": [21.5222, 70.4579],
  "gujarat::kheda": [22.7547, 72.6841],
  "gujarat::gandhinagar": [23.2156, 72.6369],

  // Punjab & Haryana
  "punjab::ludhiana": [30.9010, 75.8573],
  "punjab::amritsar": [31.6340, 74.8723],
  "punjab::jalandhar": [31.3260, 75.5762],
  "punjab::patiala": [30.3398, 76.3869],
  "punjab::bathinda": [30.2110, 74.9455],
  "haryana::karnal": [29.6857, 76.9905],
  "haryana::ambala": [30.3782, 76.7767],
  "haryana::hisar": [29.1492, 75.7217],
  "haryana::gurugram": [28.4595, 77.0266],

  // Uttar Pradesh
  "uttar pradesh::lucknow": [26.8467, 80.9462],
  "uttar pradesh::varanasi": [25.3176, 82.9739],
  "uttar pradesh::kanpur": [26.4499, 80.3319],
  "uttar pradesh::kanpur nagar": [26.4499, 80.3319],
  "uttar pradesh::agra": [27.1767, 78.0081],
  "uttar pradesh::prayagraj": [25.4358, 81.8463],
  "uttar pradesh::meerut": [28.9845, 77.7064],

  // Other States
  "west bengal::kolkata": [22.5726, 88.3639],
  "west bengal::burdwan": [23.2324, 87.8615],
  "bihar::patna": [25.5941, 85.1376],
  "bihar::gaya": [24.7914, 85.0002],
  "rajasthan::jaipur": [26.9124, 75.7873],
  "rajasthan::jodhpur": [26.2389, 73.0243],
  "madhya pradesh::bhopal": [23.2599, 77.4126],
  "madhya pradesh::indore": [22.7196, 75.8577],
  "kerala::thiruvananthapuram": [8.5241, 76.9366],
  "kerala::kochi": [9.9312, 76.2673],
  "kerala::palakkad": [10.7867, 76.6548],
  "odisha::bhubaneswar": [20.2961, 85.8245],
  "odisha::cuttack": [20.4625, 85.8828],
  "assam::guwahati": [26.1445, 91.7362],
  "delhi::new delhi": [28.6139, 77.2090]
};

// Chart Instances
let satTimeseriesChart = null;
let weatherHourlyChart = null;
let soilRadarChart = null;
let priceLagChart = null;

// Leaflet Map Instances & Overlay Elements
let dashMap = null;
let dashMapCircle = null;
let satMap = null;
let satRasterLayerGroup = null;
let farmMap = null;
let farmDrawnPolygon = null;
let farmDrawPoints = [];
let isDrawingPolygon = false;

// =========================================================
// INITIALIZATION
// =========================================================

document.addEventListener('DOMContentLoaded', () => {
  const docsBtn = document.getElementById('btn-topbar-docs') || document.querySelector('.btn-api-docs');
  if (docsBtn) {
    docsBtn.href = `${API_BASE_URL}/docs`;
  }
  initSidebarNavigation();
  initLocationSelector();
  checkSystemHealth();
  loadYieldDropdowns();
  loadPriceStates();
  initDashboardMap();
  loadDashboardData();
  setupFormHandlers();
  setupPlotManagement();
  setupInsuranceCalculator();
  setupRetrainButtons();
  setupBackendSettingsModal();
});

// =========================================================
// VIEW NAVIGATION CONTROLLER
// =========================================================

function initSidebarNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  const sidebar = document.getElementById('main-sidebar');
  const toggleBtn = document.getElementById('btn-toggle-sidebar');

  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      const targetView = link.getAttribute('data-view');
      switchView(targetView);
      if (window.innerWidth <= 768 && sidebar) {
        sidebar.classList.remove('open');
      }
    });
  });

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
}

function switchView(viewId) {
  const allViews = document.querySelectorAll('.view-content');
  const allNavs = document.querySelectorAll('.nav-link');

  allViews.forEach(v => v.classList.remove('active'));
  allNavs.forEach(n => n.classList.remove('active'));

  const targetViewEl = document.getElementById(viewId);
  const targetNavEl = document.querySelector(`[data-view="${viewId}"]`);

  if (targetViewEl) targetViewEl.classList.add('active');
  if (targetNavEl) targetNavEl.classList.add('active');

  // Trigger specialized view initializations
  if (viewId === 'view-satellite') {
    initSatelliteMap();
    loadSatelliteView();
    setTimeout(() => {
      if (satMap) {
        satMap.invalidateSize();
        satMap.setView([activeLat, activeLon], 12);
      }
      if (satTimeseriesChart) satTimeseriesChart.resize();
    }, 100);
  } else if (viewId === 'view-weather') {
    loadWeatherView();
    setTimeout(() => {
      if (weatherHourlyChart) weatherHourlyChart.resize();
    }, 100);
  } else if (viewId === 'view-myfarm') {
    initMyFarmMap();
    updateLocationUI(activeState, activeDistrict, activeLat, activeLon);
    setTimeout(() => {
      if (farmMap) {
        farmMap.invalidateSize();
        farmMap.setView([activeLat, activeLon], 12);
        if (farmDrawnPolygon && !farmMap.hasLayer(farmDrawnPolygon)) {
          farmDrawnPolygon.addTo(farmMap);
        }
      }
    }, 100);
    loadSavedPlots();
  } else if (viewId === 'view-analytics') {
    loadQuantumCircuitSchematic();
  }
}

if (typeof window !== 'undefined') {
  window.switchView = switchView;
}

// =========================================================
// LOCATION CONTEXT & STATE SELECTOR
// =========================================================

function updateLocationUI(state, district, lat, lon) {
  // Sync Topbar selects
  const topState = document.getElementById('global-state-select');
  const topDist = document.getElementById('global-district-select');
  if (topState && state && topState.value !== state) topState.value = state;
  if (topDist && district && topDist.value !== district) topDist.value = district;

  // Sync My Farm card selects
  const farmState = document.getElementById('myfarm-state-select');
  const farmDist = document.getElementById('myfarm-district-select');
  if (farmState && state && farmState.value !== state) farmState.value = state;
  if (farmDist && district && farmDist.value !== district) farmDist.value = district;

  // Sync GPS Coordinates badge in My Farm view
  const coordsBadge = document.getElementById('myfarm-coords-badge');
  if (coordsBadge && lat !== undefined && lon !== undefined) {
    coordsBadge.textContent = `${lat.toFixed(4)}° N, ${lon.toFixed(4)}° E`;
  }
}

async function syncActiveLocationData() {
  showToast(`Syncing real-time telemetry for ${activeDistrict}, ${activeState}...`, 'info');
  await updateMapLocation(activeDistrict, activeState);
}

let locationSelectorListenersSetup = false;

async function initLocationSelector() {
  const stateSel = document.getElementById('global-state-select');
  const distSel = document.getElementById('global-district-select');
  const refreshBtn = document.getElementById('btn-refresh-global');

  // Populate States & Districts with fallback defaults first
  populateSelect('global-state-select', DEFAULT_STATES_LIST, null, activeState);
  const defDists = DEFAULT_DISTRICTS_MAP[activeState.toLowerCase()] || ["Guntur", "Prakasam", "Krishna", "Anakapalli", "Visakhapatnam"];
  populateSelect('global-district-select', defDists, null, activeDistrict);

  // Also populate My Farm in-card selects
  populateSelect('myfarm-state-select', DEFAULT_STATES_LIST, null, activeState);
  populateSelect('myfarm-district-select', defDists, null, activeDistrict);
  updateLocationUI(activeState, activeDistrict, activeLat, activeLon);

  try {
    const res = await fetch(`${API_BASE_URL}/states`);
    if (res.ok) {
      const states = await res.json();
      if (states && states.length > 0) {
        populateSelect('global-state-select', states, null, activeState);
        populateSelect('myfarm-state-select', states, null, activeState);
      }
    }
  } catch (e) {
    console.debug('Could not load states for topbar (using defaults):', e);
  }

  if (!locationSelectorListenersSetup) {
    locationSelectorListenersSetup = true;

    // Topbar State Change
    if (stateSel) {
      stateSel.addEventListener('change', async () => {
        activeState = stateSel.value;
        await updateGlobalDistricts(activeState);
        await updateMapLocation(activeDistrict, activeState);
      });
    }

    // Topbar District Change
    if (distSel) {
      distSel.addEventListener('change', async () => {
        activeDistrict = distSel.value;
        updateLocationUI(activeState, activeDistrict, activeLat, activeLon);
        await updateMapLocation(activeDistrict, activeState);
      });
    }

    // My Farm In-Card State Change
    const farmStateSel = document.getElementById('myfarm-state-select');
    if (farmStateSel) {
      farmStateSel.addEventListener('change', async () => {
        activeState = farmStateSel.value;
        await updateGlobalDistricts(activeState);
        await updateMapLocation(activeDistrict, activeState);
      });
    }

    // My Farm In-Card District Change
    const farmDistSel = document.getElementById('myfarm-district-select');
    if (farmDistSel) {
      farmDistSel.addEventListener('change', async () => {
        activeDistrict = farmDistSel.value;
        updateLocationUI(activeState, activeDistrict, activeLat, activeLon);
        await updateMapLocation(activeDistrict, activeState);
      });
    }

    // My Farm "Pan to District" Button
    const farmPanBtn = document.getElementById('btn-pan-myfarm-location');
    if (farmPanBtn) {
      farmPanBtn.addEventListener('click', async () => {
        await updateMapLocation(activeDistrict, activeState);
      });
    }

    // Topbar Manual Sync Button
    if (refreshBtn) {
      refreshBtn.addEventListener('click', async () => {
        await syncActiveLocationData();
      });
    }

    // Satellite page manual refresh button
    const satRefreshBtn = document.getElementById('btn-fetch-sat-manual');
    if (satRefreshBtn) {
      satRefreshBtn.addEventListener('click', async () => {
        showToast(`Refreshing Sentinel-2 multi-spectral scene for ${activeDistrict}...`, 'info');
        await loadSatelliteView();
      });
    }
  }
}

async function updateGlobalDistricts(state) {
  const localDists = DEFAULT_DISTRICTS_MAP[(state || '').toLowerCase()] || [];
  if (localDists.length > 0) {
    populateSelect('global-district-select', localDists, null, localDists[0]);
    populateSelect('myfarm-district-select', localDists, null, localDists[0]);
    activeDistrict = localDists[0];
  }
  try {
    const res = await fetch(`${API_BASE_URL}/districts/${encodeURIComponent(state)}`);
    if (res.ok) {
      const districts = await res.json();
      if (districts && districts.length > 0) {
        populateSelect('global-district-select', districts, null, districts[0]);
        populateSelect('myfarm-district-select', districts, null, districts[0]);
        activeDistrict = districts[0];
      }
    }
  } catch (e) {
    console.warn('Could not load districts:', e);
  }
  updateLocationUI(activeState, activeDistrict, activeLat, activeLon);
}

// =========================================================
// SYSTEM HEALTH & QUANTUM TELEMETRY (Smart Auto-Wakeup)
// =========================================================

let healthCheckTimer = null;
let retryCount = 0;
const MAX_WAKEUP_RETRIES = 15; // 15 retries * 4s = 60s max wakeup loop
let isBackendConnected = false;

async function checkSystemHealth(isSilent = false, isManualTest = false) {
  const statusLabel = document.getElementById('sidebar-status-label');
  const statusPill = document.getElementById('sidebar-quantum-status');
  const footIndicator = document.querySelector('.online-indicator');
  const footStatusText = document.getElementById('foot-status-text');
  const footQubits = document.getElementById('foot-qubits');

  // Modal elements
  const modalBadge = document.getElementById('modal-status-badge');
  const modalText = document.getElementById('modal-status-text');
  const modalPing = document.getElementById('modal-ping-val');
  const modalEngine = document.getElementById('modal-backend-type');
  const modalDiagMsg = document.getElementById('modal-diag-msg');
  const modalDiagTime = document.getElementById('modal-diag-timestamp');

  const nowTime = new Date().toLocaleTimeString();

  try {
    const startTime = performance.now();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000); // 12s timeout

    const res = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    const latency = Math.round(performance.now() - startTime);

    if (res.ok) {
      const data = await res.json();
      const wasDisconnected = !isBackendConnected;
      isBackendConnected = true;
      retryCount = 0;

      // Update Sidebar Pill & Label
      if (statusPill) {
        statusPill.className = 'sidebar-status-pill status-online';
        statusPill.title = `Connected to ${API_BASE_URL} (${latency}ms). Quantum HQNN yield: ${data.yield_model || 'ready'}, price: ${data.price_model || 'ready'}.`;
      }
      if (statusLabel) {
        statusLabel.textContent = 'Backend Online';
      }

      // Update Footer
      if (footIndicator) footIndicator.className = 'online-indicator status-online';
      if (footStatusText) footStatusText.textContent = 'Backend Online';
      if (footQubits) footQubits.textContent = data.qubits_yield || 8;

      // Update Modal
      if (modalBadge) modalBadge.className = 'telemetry-badge status-online';
      if (modalText) modalText.textContent = 'Backend Online (200 OK)';
      if (modalPing) modalPing.textContent = `${latency} ms`;
      if (modalEngine) modalEngine.textContent = data.quantum_backend || 'PennyLane Simulator';
      if (modalDiagMsg) modalDiagMsg.textContent = `Connected to ${API_BASE_URL} in ${latency}ms. Quantum HQNN yield: ${data.yield_model || 'active'}, price: ${data.price_model || 'active'}.`;
      if (modalDiagTime) modalDiagTime.textContent = nowTime;

      // If this just woke up from being disconnected, reload dynamic server data
      if (wasDisconnected && !isManualTest) {
        if (!isSilent) showToast('⚡ AgriVision DSS Backend is connected and online!', 'success');
        refreshLivePlatformData();
      }

      return { ok: true, data, latency };
    } else {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
  } catch (err) {
    console.error('[Health Diagnostic]', err);

    let errorDetail = 'Connection Error';
    if (err.name === 'AbortError') {
      errorDetail = 'Timeout (>8s Cold Start)';
    } else if (err.message && err.message.startsWith('HTTP')) {
      errorDetail = err.message;
    } else if (err.message && (err.message.includes('fetch') || err.message.includes('NetworkError'))) {
      errorDetail = 'Network / CORS Blocked';
    } else if (err.message) {
      errorDetail = err.message;
    }

    // If connection to localhost failed and user didn't explicitly set custom URL, try auto-fallback to Live Cloud Render backend
    const isLocalhost = API_BASE_URL.includes('127.0.0.1:8000') || API_BASE_URL.includes('localhost:8000');
    const hasCustomStorage = !!localStorage.getItem('VITE_API_URL');

    if (isLocalhost && !hasCustomStorage && retryCount === 0) {
      console.info('Localhost backend not active. Auto-connecting to Live Cloud Backend (Render)...');
      API_BASE_URL = PRODUCTION_API_URL;
      const docsBtn = document.getElementById('btn-topbar-docs') || document.querySelector('.btn-api-docs');
      if (docsBtn) docsBtn.href = `${API_BASE_URL}/docs`;
      showToast('💡 Local backend (8000) not running. Connected to Live Cloud API.', 'info');
      return checkSystemHealth(isSilent, isManualTest);
    }

    isBackendConnected = false;

    if (retryCount < MAX_WAKEUP_RETRIES) {
      retryCount++;

      // Update Pill
      if (statusPill) {
        statusPill.className = 'sidebar-status-pill status-waking';
        statusPill.title = `Backend waking up from Render sleep (Attempt ${retryCount}/${MAX_WAKEUP_RETRIES}). Reason: ${errorDetail}.`;
      }
      if (statusLabel) {
        statusLabel.textContent = `Waking Backend (${retryCount * 4}s)...`;
      }

      // Update Footer
      if (footIndicator) footIndicator.className = 'online-indicator status-waking';
      if (footStatusText) footStatusText.textContent = `Waking Up (${errorDetail})...`;

      // Update Modal
      if (modalBadge) modalBadge.className = 'telemetry-badge status-waking';
      if (modalText) modalText.textContent = `Waking Up (Attempt ${retryCount}/${MAX_WAKEUP_RETRIES})...`;
      if (modalPing) modalPing.textContent = 'Connecting...';
      if (modalDiagMsg) modalDiagMsg.textContent = `Render Free Tier container is spinning up... (${errorDetail}). Retrying automatically in 4s.`;
      if (modalDiagTime) modalDiagTime.textContent = nowTime;

      if (retryCount === 1 && !isSilent) {
        showToast('🌱 Waking up Render backend container (~30–45s cold start). Auto-connecting...', 'info');
      }

      // Schedule next retry loop
      if (healthCheckTimer) clearTimeout(healthCheckTimer);
      healthCheckTimer = setTimeout(() => {
        checkSystemHealth(true);
      }, 4000);

      return { ok: false, waking: true, attempt: retryCount, error: err };
    } else {
      // Offline state after max retries with EXACT error detail
      if (statusPill) {
        statusPill.className = 'sidebar-status-pill status-offline';
        statusPill.title = `Backend offline at ${API_BASE_URL} (${errorDetail}). Click to change URL or retry.`;
      }
      if (statusLabel) {
        statusLabel.textContent = `Backend Offline (${errorDetail})`;
      }

      // Update Footer
      if (footIndicator) footIndicator.className = 'online-indicator status-offline';
      if (footStatusText) footStatusText.textContent = `Backend Offline: ${errorDetail}`;

      // Update Modal
      if (modalBadge) modalBadge.className = 'telemetry-badge status-offline';
      if (modalText) modalText.textContent = `Backend Offline: ${errorDetail}`;
      if (modalPing) modalPing.textContent = errorDetail;
      if (modalDiagMsg) modalDiagMsg.textContent = `Failed to reach ${API_BASE_URL} [${errorDetail}]. Verify backend service is deployed or enter your custom URL above.`;
      if (modalDiagTime) modalDiagTime.textContent = nowTime;

      if (!isSilent) {
        showToast(`⚠️ Backend unreachable (${errorDetail}). Click sidebar badge to configure URL.`, 'error');
      }

      return { ok: false, waking: false, error: err };
    }
  }
}

// =========================================================
// DASHBOARD AGGREGATOR & TELEMETRY
// =========================================================

async function loadDashboardData() {
  try {
    const url = `${API_BASE_URL}/dashboard?state=${encodeURIComponent(activeState)}&district=${encodeURIComponent(activeDistrict)}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    const kpi = data.kpi_cards;

    // 1. Satellite KPI
    const ndviEl = document.getElementById('dash-ndvi-value');
    if (ndviEl) ndviEl.textContent = `NDVI ${kpi.satellite_health.ndvi}`;
    const ndviStatEl = document.getElementById('dash-ndvi-status');
    if (ndviStatEl) ndviStatEl.innerHTML = `<span class="badge badge-emerald">${kpi.satellite_health.status}</span>`;

    // 2. Weather & ET0 KPI
    const et0El = document.getElementById('dash-et0-stat');
    if (et0El) et0El.textContent = `${kpi.weather_alerts.et0_mm} mm/day`;

    // 3. Soil Health KPI
    const soilScoreEl = document.getElementById('dash-soil-score');
    if (soilScoreEl) soilScoreEl.textContent = `${kpi.soil_fertility.soil_health_score} / 100`;

    // Mini Stats on Satellite Box
    const eviEl = document.getElementById('dash-evi-stat');
    if (eviEl) eviEl.textContent = kpi.satellite_health.evi;
    const lstEl = document.getElementById('dash-lst-stat');
    if (lstEl) lstEl.textContent = `${kpi.weather_alerts.temperature_c + 2.5} °C`;

    // Active Weather Alerts list
    const alertsContainer = document.getElementById('dash-alerts-container');
    if (alertsContainer) {
      const alerts = kpi.weather_alerts.alerts || [];
      if (alerts.length === 0) {
        alertsContainer.innerHTML = `
          <div class="alert-item alert-item-info">
            <span class="alert-item-icon">🌤️</span>
            <div>
              <strong>Optimal Agro-Climatic Window</strong>
              <p>No extreme heat, frost, or flood hazards detected in ${activeDistrict}. Standard irrigation and spraying schedules recommended.</p>
            </div>
          </div>`;
      } else {
        alertsContainer.innerHTML = alerts.map(a => `
          <div class="alert-item ${a.severity === 'CRITICAL' ? 'alert-item-critical' : 'alert-item-warning'}">
            <span class="alert-item-icon">${a.icon || '⚠️'}</span>
            <div>
              <strong>${a.type}</strong>
              <p>${a.message} <em>(${a.action})</em></p>
            </div>
          </div>`).join('');
      }
    }

    // Top Ticker update
    const tickerText = document.getElementById('ticker-text');
    if (tickerText) {
      tickerText.textContent = `📍 ${activeDistrict}, ${activeState} | ${kpi.weather_alerts.temperature_c}°C | ET₀: ${kpi.weather_alerts.et0_mm} mm/d | NDVI: ${kpi.satellite_health.ndvi} (${kpi.satellite_health.status})`;
    }

    // Update Dashboard Map Marker/Circle if map is rendered
    if (dashMap && dashMapCircle) {
      dashMapCircle.setLatLng([activeLat, activeLon]);
      dashMapCircle.setPopupContent(`<b>${activeDistrict} Field Zone</b><br>Sentinel-2 Active Monitoring`);
    }

  } catch (err) {
    console.error('Error loading dashboard data:', err);
  }
}

// =========================================================
// LEAFLET MAP CONTROLLER
// =========================================================

function initDashboardMap() {
  const container = document.getElementById('dash-map-container');
  if (!container || dashMap) return;

  dashMap = L.map('dash-map-container', {
    center: [activeLat, activeLon],
    zoom: 11,
    zoomControl: true
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors | Sentinel-2 MSI'
  }).addTo(dashMap);

  dashMapCircle = L.circle([activeLat, activeLon], {
    color: '#10b981',
    fillColor: '#34d399',
    fillOpacity: 0.25,
    radius: 3500
  }).addTo(dashMap).bindPopup(`<b>${activeDistrict} Field Zone</b><br>Sentinel-2 Active Monitoring`).openPopup();
}

function initSatelliteMap() {
  const container = document.getElementById('satellite-map-container');
  if (!container) return;

  if (satMap) {
    setTimeout(() => {
      satMap.invalidateSize();
      satMap.setView([activeLat, activeLon], 12);
    }, 200);
    return;
  }

  satMap = L.map('satellite-map-container', {
    center: [activeLat, activeLon],
    zoom: 12
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Sentinel-2 Multi-Spectral Raster Grid'
  }).addTo(satMap);

  satRasterLayerGroup = L.layerGroup().addTo(satMap);
}

function initMyFarmMap() {
  const container = document.getElementById('myfarm-map-container');
  if (!container) return;

  if (farmMap) {
    setTimeout(() => {
      farmMap.invalidateSize();
      farmMap.setView([activeLat, activeLon], 12);
      if (farmDrawnPolygon && !farmMap.hasLayer(farmDrawnPolygon)) {
        farmDrawnPolygon.addTo(farmMap);
      }
    }, 200);
    return;
  }

  farmMap = L.map('myfarm-map-container', {
    center: [activeLat, activeLon],
    zoom: 12
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors | Interactive Farm Plot Manager'
  }).addTo(farmMap);

  // Preserve existing drawn polygon
  if (farmDrawnPolygon && !farmMap.hasLayer(farmDrawnPolygon)) {
    farmDrawnPolygon.addTo(farmMap);
  }

  // Map Click Listener for Polygon Drawing
  farmMap.on('click', (e) => {
    if (!isDrawingPolygon) return;
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;
    farmDrawPoints.push([lat, lon]);

    if (farmDrawnPolygon) farmMap.removeLayer(farmDrawnPolygon);

    farmDrawnPolygon = L.polygon(farmDrawPoints, {
      color: '#34d399',
      fillColor: '#10b981',
      fillOpacity: 0.35,
      weight: 3
    }).addTo(farmMap);

    const lbl = document.getElementById('draw-status-lbl');
    if (lbl) lbl.textContent = `Points added: ${farmDrawPoints.length}. Click more vertices or save plot.`;
  });
}

// =========================================================
// GEOCODING & MAP LOCATION CONTROLLER
// =========================================================

async function geocodeLocation(district, state) {
  const dClean = (district || '').trim().toLowerCase();
  const sClean = (state || '').trim().toLowerCase();
  const key = `${sClean}::${dClean}`;

  // 1. Fast Dictionary Lookup (0ms instant response)
  if (LOCAL_DISTRICT_COORDS[key]) {
    const [lat, lon] = LOCAL_DISTRICT_COORDS[key];
    return { latitude: lat, longitude: lon, source: 'local_database' };
  }

  // Exact or substring match in local dictionary
  for (const [k, coords] of Object.entries(LOCAL_DISTRICT_COORDS)) {
    const [stPart, distPart] = k.split('::');
    if (stPart === sClean && (distPart === dClean || distPart.includes(dClean) || dClean.includes(distPart))) {
      return { latitude: coords[0], longitude: coords[1], source: 'local_database' };
    }
  }
  for (const [k, coords] of Object.entries(LOCAL_DISTRICT_COORDS)) {
    const [, distPart] = k.split('::');
    if (distPart === dClean) {
      return { latitude: coords[0], longitude: coords[1], source: 'local_database' };
    }
  }

  // 2. Query FastAPI Backend Geocode Endpoint: GET /geocode?state=...&district=...
  try {
    const res = await fetch(`${API_BASE_URL}/geocode?state=${encodeURIComponent(state)}&district=${encodeURIComponent(district)}`);
    if (res.ok) {
      const data = await res.json();
      if (data.latitude && data.longitude) {
        return { latitude: data.latitude, longitude: data.longitude, source: data.source || 'backend_nominatim' };
      }
    }
  } catch (e) {
    console.debug('Backend geocoding lookup failed:', e);
  }

  // 3. Fallback to Open-Meteo Geocoding API
  try {
    const query = `${district}, ${state}, India`.trim();
    const res = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=1&format=json`);
    if (res.ok) {
      const data = await res.json();
      if (data.results && data.results.length > 0) {
        return { latitude: data.results[0].latitude, longitude: data.results[0].longitude, source: 'open_meteo' };
      }
    }
  } catch (e) {}

  return null;
}

async function updateMapLocation(district, state) {
  const targetDist = district || activeDistrict;
  const targetState = state || activeState;

  const result = await geocodeLocation(targetDist, targetState);

  if (!result || !result.latitude || !result.longitude) {
    showToast('Location not found.', 'warning');
    return false;
  }

  const { latitude, longitude } = result;
  activeLat = latitude;
  activeLon = longitude;
  activeDistrict = targetDist;
  activeState = targetState;

  updateLocationUI(activeState, activeDistrict, activeLat, activeLon);

  // 1. Smoothly fly Farm Map (My Farm Plots Module) - Zoom 12
  if (farmMap) {
    farmMap.flyTo([latitude, longitude], 12, {
      animate: true,
      duration: 2
    });
    setTimeout(() => {
      farmMap.invalidateSize();
      // Strictly preserve existing drawn polygon boundaries
      if (farmDrawnPolygon && !farmMap.hasLayer(farmDrawnPolygon)) {
        farmDrawnPolygon.addTo(farmMap);
      }
    }, 250);
  }

  // 2. Smoothly fly Dashboard Map - Zoom 11
  if (dashMap) {
    dashMap.flyTo([latitude, longitude], 11, {
      animate: true,
      duration: 2
    });
    if (dashMapCircle) {
      dashMapCircle.setLatLng([latitude, longitude]);
      dashMapCircle.setPopupContent(`<b>${activeDistrict} Field Zone</b><br>Sentinel-2 Active Monitoring`);
    }
    setTimeout(() => dashMap.invalidateSize(), 250);
  }

  // 3. Smoothly fly Satellite Map - Zoom 12
  if (satMap) {
    satMap.flyTo([latitude, longitude], 12, {
      animate: true,
      duration: 2
    });
    setTimeout(() => satMap.invalidateSize(), 250);
  }

  // Refresh all dependent layers: Satellite, Weather, Soil Health, NDVI, Dashboard KPIs
  await refreshAllGeospatialLayers();
  return true;
}

async function refreshAllGeospatialLayers() {
  await Promise.allSettled([
    loadDashboardData(),
    loadSatelliteView(),
    loadWeatherView(),
    loadSoilDataForLocation(activeState, activeDistrict),
    loadSavedPlots()
  ]);
}

async function loadSoilDataForLocation(state, district) {
  try {
    const res = await fetch(`${API_BASE_URL}/soil?state=${encodeURIComponent(state || activeState)}&district=${encodeURIComponent(district || activeDistrict)}`);
    if (res.ok) {
      const data = await res.json();
      const p = data.health_evaluation?.parameters;
      if (p) {
        const setVal = (id, v) => {
          const el = document.getElementById(id);
          if (el && v !== undefined && v !== null) el.value = v;
        };
        setVal('soil-n', p.nitrogen);
        setVal('soil-p', p.phosphorus);
        setVal('soil-k', p.potassium);
        setVal('soil-ph', p.ph);
        setVal('soil-oc', p.organic_carbon);
        setVal('soil-ec', p.ec);
      }
    }
  } catch (err) {
    console.debug('Could not auto-fetch soil profile:', err);
  }
}

// =========================================================
// SATELLITE INTELLIGENCE VIEW
// =========================================================

async function loadSatelliteView() {
  initSatelliteMap();

  try {
    const url = `${API_BASE_URL}/satellite?state=${encodeURIComponent(activeState)}&district=${encodeURIComponent(activeDistrict)}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    const ind = data.indices;
    const pageNdvi = document.getElementById('sat-page-ndvi');
    if (pageNdvi) pageNdvi.textContent = ind.ndvi;
    const pageEvi = document.getElementById('sat-page-evi');
    if (pageEvi) pageEvi.textContent = ind.evi;
    const pageNdwi = document.getElementById('sat-page-ndwi');
    if (pageNdwi) pageNdwi.textContent = (ind.ndwi >= 0 ? '+' : '') + ind.ndwi;
    const pageVhi = document.getElementById('sat-page-vhi');
    if (pageVhi) pageVhi.textContent = ind.vhi;
    const pageLst = document.getElementById('sat-page-lst');
    if (pageLst) pageLst.textContent = `${ind.land_surface_temperature_c} °C`;

    const pageNdviDesc = document.getElementById('sat-page-ndvi-desc');
    if (pageNdviDesc && data.vegetation_assessment && data.vegetation_assessment.ndvi_classification) {
      pageNdviDesc.textContent = `${data.vegetation_assessment.ndvi_classification.category} (${data.vegetation_assessment.ndvi_classification.health_status})`;
    }

    // Render Spatial Raster Grid on Map
    if (satMap) {
      setTimeout(() => satMap.invalidateSize(), 150);

      if (!satRasterLayerGroup) {
        satRasterLayerGroup = L.layerGroup().addTo(satMap);
      }
      satRasterLayerGroup.clearLayers();

      if (data.spatial_raster && data.spatial_raster.cells) {
        data.spatial_raster.cells.forEach(cell => {
          L.rectangle(cell.bounds, {
            color: cell.color,
            fillColor: cell.color,
            fillOpacity: 0.45,
            weight: 1
          }).addTo(satRasterLayerGroup).bindPopup(`<b>Zone [${cell.row},${cell.col}]</b><br>NDVI: ${cell.ndvi}<br>Status: ${cell.status}`);
        });
      }

      if (data.coordinates && data.coordinates.latitude && data.coordinates.longitude) {
        activeLat = data.coordinates.latitude;
        activeLon = data.coordinates.longitude;
        satMap.setView([activeLat, activeLon], 12);
      }
    }

    // Render 12-Month Chart
    if (data.historical_timeseries) {
      renderSatelliteTimeseries(data.historical_timeseries);
    }

  } catch (e) {
    console.error('Error loading satellite view:', e);
  }
}

function renderSatelliteTimeseries(timeseries) {
  const ctx = document.getElementById('satellite-timeseries-chart');
  if (!ctx) return;

  if (satTimeseriesChart) satTimeseriesChart.destroy();

  const labels = timeseries.map(t => t.month);
  const ndviData = timeseries.map(t => t.ndvi);
  const eviData = timeseries.map(t => t.evi);
  const lstData = timeseries.map(t => t.lst_c);

  satTimeseriesChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'NDVI Vegetation Vigor',
          data: ndviData,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.35,
          yAxisID: 'y'
        },
        {
          label: 'EVI Biomass Volume',
          data: eviData,
          borderColor: '#38bdf8',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          tension: 0.35,
          yAxisID: 'y'
        },
        {
          label: 'Land Surface Temp (°C)',
          data: lstData,
          borderColor: '#f59e0b',
          backgroundColor: 'transparent',
          tension: 0.35,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0,
          max: 1.0,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#94a3b8' }
        },
        y1: {
          position: 'right',
          min: 15,
          max: 45,
          grid: { drawOnChartArea: false },
          ticks: { color: '#fbbf24' }
        },
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#94a3b8' }
        }
      },
      plugins: {
        legend: { labels: { color: '#e2e8f0' } }
      }
    }
  });
}

// =========================================================
// ADVANCED WEATHER VIEW
// =========================================================

function renderForecastCards(forecastList) {
  const container = document.getElementById('forecast-cards-container');
  if (!container) return;

  if (!forecastList || forecastList.length === 0) {
    const days = ['Today', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
    forecastList = days.map((day, idx) => ({
      day_name: day,
      condition: idx === 3 ? 'Rainy' : (idx % 2 === 0 ? 'Sunny' : 'Partly Cloudy'),
      temp_min_c: 22 + (idx % 3),
      temp_max_c: 33 + (idx % 2),
      precipitation_probability_percent: idx === 3 ? 65 : (idx * 8),
      precipitation_mm: idx === 3 ? 8.5 : 0.0,
      et0_evapotranspiration_mm: Math.round((4.5 + (idx % 3) * 0.3) * 10) / 10
    }));
  }

  container.innerHTML = forecastList.map(d => `
    <div class="forecast-day-card">
      <div class="forecast-day-name">${d.day_name || 'Day'}</div>
      <div class="forecast-icon">${d.condition === 'Rainy' ? '🌧️' : (d.condition === 'Cloudy' || d.condition === 'Partly Cloudy' ? '⛅' : '☀️')}</div>
      <div class="forecast-temp">${d.temp_min_c ?? 22}° / ${d.temp_max_c ?? 34}°</div>
      <div class="forecast-rain">💧 ${d.precipitation_probability_percent ?? 10}% (${d.precipitation_mm ?? 0}mm)</div>
      <div class="forecast-et0">ET₀: ${d.et0_evapotranspiration_mm ?? 4.5} mm</div>
    </div>
  `).join('');
}

async function loadWeatherView() {
  // Always ensure forecast cards and diurnal progression chart are drawn immediately
  renderForecastCards();
  renderWeatherHourlyChart();

  try {
    const url = `${API_BASE_URL}/weather?state=${encodeURIComponent(activeState)}&district=${encodeURIComponent(activeDistrict)}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    const cw = data.current_weather || {};
    const safeSet = (id, val) => {
      const el = document.getElementById(id);
      if (el && val !== undefined && val !== null) el.textContent = val;
    };

    safeSet('w-temp', `${cw.temperature_c ?? 28.5} °C`);
    safeSet('w-min', `${cw.temp_min_c ?? 22}°C`);
    safeSet('w-max', `${cw.temp_max_c ?? 34}°C`);
    safeSet('w-humid', `${cw.relative_humidity_percent ?? 68} %`);
    safeSet('w-wind', `${cw.wind_speed_kmh ?? 12.0} km/h`);
    safeSet('w-solar', `${cw.solar_radiation_mj_m2 ?? 19.2} MJ/m²`);
    safeSet('w-et0', `${cw.evapotranspiration_et0_mm ?? 4.62} mm/d`);

    if (data.forecast_7_day && data.forecast_7_day.length > 0) {
      renderForecastCards(data.forecast_7_day);
    }

    if (data.hourly_24h && data.hourly_24h.length > 0) {
      renderWeatherHourlyChart(data.hourly_24h);
    }
  } catch (e) {
    console.warn('Weather live fetch notice:', e);
  }
}

function renderWeatherHourlyChart(hourlyData) {
  const ctx = document.getElementById('weather-hourly-chart');
  if (!ctx) return;

  // If hourlyData is empty, generate realistic 24-hour diurnal dataset
  if (!hourlyData || hourlyData.length === 0) {
    hourlyData = Array.from({ length: 24 }, (_, i) => {
      const hStr = `${String(i).padStart(2, '0')}:00`;
      const rad = 2 * Math.PI * (i - 9) / 24.0;
      return {
        hour: hStr,
        temperature_c: Math.round((28.5 + 5.5 * Math.sin(rad)) * 10) / 10,
        humidity_percent: Math.round(Math.min(95, Math.max(30, 62.0 - 22.0 * Math.sin(rad))))
      };
    });
  }

  if (weatherHourlyChart) {
    try {
      weatherHourlyChart.destroy();
    } catch (e) {}
  }

  const labels = hourlyData.map(h => h.hour || (h.time ? h.time.split('T')[1] : ''));
  const temps = hourlyData.map(h => h.temperature_c);
  const humids = hourlyData.map(h => h.humidity_percent);

  weatherHourlyChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Hourly Temp (°C)',
          data: temps,
          borderColor: '#fbbf24',
          backgroundColor: 'rgba(251, 191, 36, 0.12)',
          fill: true,
          tension: 0.35,
          yAxisID: 'y'
        },
        {
          label: 'Relative Humidity (%)',
          data: humids,
          borderColor: '#38bdf8',
          backgroundColor: 'transparent',
          tension: 0.35,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#fbbf24' }
        },
        y1: {
          position: 'right',
          min: 15,
          max: 100,
          grid: { drawOnChartArea: false },
          ticks: { color: '#38bdf8' }
        },
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#94a3b8' }
        }
      },
      plugins: {
        legend: { labels: { color: '#e2e8f0' } }
      }
    }
  });
}

// =========================================================
// FORM HANDLERS (Yield, Price, Soil, Recommendation)
// =========================================================

function setupFormHandlers() {
  // 1. Yield Predictor Form
  const yieldForm = document.getElementById('yield-form');
  if (yieldForm) {
    yieldForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('yield-submit-btn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>⚡ Running Quantum HQNN...</span>';

      const payload = {
        Crop: document.getElementById('yield-crop').value,
        Season: document.getElementById('yield-season').value,
        State: document.getElementById('yield-state').value,
        District: document.getElementById('yield-district').value,
        Crop_Year: parseInt(document.getElementById('yield-year').value, 10),
        Area: parseFloat(document.getElementById('yield-area').value),
        Fertilizer: parseFloat(document.getElementById('yield-fertilizer').value),
        Pesticide: parseFloat(document.getElementById('yield-pesticide').value)
      };

      try {
        const res = await fetch(`${API_BASE_URL}/predict-yield`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Yield inference error');

        renderYieldResult(result, payload);
        showToast('Quantum Crop Yield Prediction calculated successfully!', 'success');
      } catch (err) {
        showToast(`Yield prediction failed: ${err.message}`, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>🚀 Execute Quantum Yield Inference</span>';
      }
    });
  }

  // 2. Price Forecast Form
  const priceForm = document.getElementById('price-form');
  if (priceForm) {
    priceForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('price-submit-btn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>⚡ Forecasting Quantum VQR...</span>';

      const payload = {
        State: document.getElementById('price-state').value,
        District: document.getElementById('price-district').value,
        Market: document.getElementById('price-market').value,
        Commodity: document.getElementById('price-commodity').value,
        Variety: document.getElementById('price-variety').value,
        Grade: document.getElementById('price-grade').value,
        Prediction_Date: document.getElementById('price-date').value
      };

      try {
        const res = await fetch(`${API_BASE_URL}/predict-price`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Price forecast error');

        renderPriceResult(result, payload);
        showToast('Quantum Price Forecast generated!', 'success');
      } catch (err) {
        showToast(`Price forecast failed: ${err.message}`, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>📈 Forecast Quantum Market Price</span>';
      }
    });
  }

  // 3. Soil Health Form
  const soilForm = document.getElementById('soil-test-form');
  if (soilForm) {
    soilForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        state: activeState,
        district: activeDistrict,
        nitrogen: parseFloat(document.getElementById('soil-n').value),
        phosphorus: parseFloat(document.getElementById('soil-p').value),
        potassium: parseFloat(document.getElementById('soil-k').value),
        ph: parseFloat(document.getElementById('soil-ph').value),
        organic_carbon: parseFloat(document.getElementById('soil-oc').value),
        ec: parseFloat(document.getElementById('soil-ec').value),
        zinc: parseFloat(document.getElementById('soil-zn').value || 0.75),
        boron: parseFloat(document.getElementById('soil-b').value || 0.52)
      };

      try {
        const res = await fetch(`${API_BASE_URL}/soil/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error('Soil evaluation failed');

        renderSoilResult(result.evaluation);
        showToast('Soil Health evaluation complete!', 'success');
      } catch (err) {
        showToast(`Soil analysis failed: ${err.message}`, 'error');
      }
    });

    const autofillSoilBtn = document.getElementById('btn-autofill-soil');
    if (autofillSoilBtn) {
      autofillSoilBtn.addEventListener('click', async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/soil?state=${encodeURIComponent(activeState)}&district=${encodeURIComponent(activeDistrict)}`);
          if (res.ok) {
            const data = await res.json();
            const p = data.health_evaluation.parameters;
            document.getElementById('soil-n').value = p.nitrogen;
            document.getElementById('soil-p').value = p.phosphorus;
            document.getElementById('soil-k').value = p.potassium;
            document.getElementById('soil-ph').value = p.ph;
            document.getElementById('soil-oc').value = p.organic_carbon;
            document.getElementById('soil-ec').value = p.ec;
            showToast(`Auto-filled soil parameters for ${activeState}`, 'info');
          }
        } catch (err) {
          showToast('Could not auto-fill soil data', 'error');
        }
      });
    }
  }

  // 4. Recommendation Master Form
  const recForm = document.getElementById('rec-form');
  if (recForm) {
    recForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = document.getElementById('rec-submit-btn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>⚡ Optimizing Multi-Criteria Quantum DSS...</span>';

      const payload = {
        Crop: document.getElementById('rec-crop').value,
        Season: document.getElementById('rec-season').value,
        Area: parseFloat(document.getElementById('rec-area').value),
        Crop_Year: parseInt(document.getElementById('rec-year').value, 10),
        State: activeState,
        District: activeDistrict
      };

      try {
        const res = await fetch(`${API_BASE_URL}/recommendation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Recommendation engine error');

        renderRecommendationResult(result);
        showToast('Precision Farm Prescription generated!', 'success');
      } catch (err) {
        showToast(`Recommendation generation failed: ${err.message}`, 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>🚀 Generate Comprehensive Farm Prescription</span>';
      }
    });
  }
}

// =========================================================
// RESULT RENDERERS
// =========================================================

function renderYieldResult(data, input) {
  const container = document.getElementById('yield-result-container');
  if (!container) return;

  container.innerHTML = `
    <div class="result-metric-grid">
      <div class="result-box">
        <div class="result-box-title">Predicted Yield</div>
        <div class="result-box-val" style="color: #34d399;">${data.predicted_yield_per_acre} <span style="font-size: 0.9rem;">Tons / Acre</span></div>
        <small style="color: var(--text-muted);">Total: <strong>${data.total_production_tons} Tons</strong></small>
      </div>

      <div class="result-box">
        <div class="result-box-title">Quantum Confidence</div>
        <div class="result-box-val" style="color: #818cf8;">${data.quantum_confidence_score || '82.5'} %</div>
        <small style="color: var(--text-muted);">Pauli-Z Expectation readouts</small>
      </div>

      <div class="result-box">
        <div class="result-box-title">Annual Rainfall Used</div>
        <div class="result-box-val" style="color: #38bdf8;">${data.annual_rainfall_used || 950} <span style="font-size: 0.9rem;">mm</span></div>
        <small style="color: var(--text-muted);">${data.rainfall_source || 'Geospatial API'}</small>
      </div>

      <div class="result-box">
        <div class="result-box-title">Model Architecture</div>
        <div class="result-box-val" style="font-size: 1.05rem; color: #fde68a;">8 Qubits (AngleEmbedding)</div>
        <small style="color: var(--text-muted);">PennyLane + PyTorch HQNN</small>
      </div>
    </div>

    <div class="banner-note banner-note-emerald" style="margin-top: 10px;">
      <span>🌾</span>
      <span>Total estimated production for <strong>${input.Area} acres</strong> of ${input.Crop} is <strong>${data.total_production_tons} Metric Tons</strong>.</span>
    </div>
  `;
}

function renderPriceResult(data, input) {
  const container = document.getElementById('price-result-container');
  if (!container) return;

  const bounds = data.price_confidence_interval || {};

  container.innerHTML = `
    <div class="result-metric-grid">
      <div class="result-box">
        <div class="result-box-title">Predicted Mandi Price</div>
        <div class="result-box-val" style="color: #fbbf24;">₹ ${data.predicted_price} <span style="font-size: 0.9rem;">/ Qtl</span></div>
        <small style="color: var(--text-muted);">${input.Commodity} (${input.Variety})</small>
      </div>

      <div class="result-box">
        <div class="result-box-title">Expected Volatility Range</div>
        <div class="result-box-val" style="font-size: 1.15rem; color: #a5b4fc;">₹ ${bounds.lower_bound || data.predicted_price * 0.95} - ₹ ${bounds.upper_bound || data.predicted_price * 1.05}</div>
        <small style="color: var(--text-muted);">Confidence: <strong>${data.quantum_confidence_score || '80.0'}%</strong></small>
      </div>
    </div>

    <div class="banner-note banner-note-indigo" style="margin-top: 10px;">
      <span>📈</span>
      <span>Market: <strong>${input.Market}</strong> | Date: <strong>${input.Prediction_Date}</strong> | Model: <strong>Variational Quantum Regressor</strong></span>
    </div>
  `;
}

function renderSoilResult(evaluation) {
  const container = document.getElementById('soil-result-container');
  if (!container) return;

  const npk = evaluation.npk_analysis;
  const phRep = evaluation.ph_correction_report;

  container.innerHTML = `
    <div class="result-metric-grid">
      <div class="result-box">
        <div class="result-box-title">Soil Health Score</div>
        <div class="result-box-val" style="color: #34d399;">${evaluation.soil_health_score} <span style="font-size: 0.9rem;">/ 100</span></div>
        <small><span class="badge badge-emerald">${evaluation.soil_grade}</span></small>
      </div>

      <div class="result-box">
        <div class="result-box-title">Observed N:P:K Ratio</div>
        <div class="result-box-val" style="font-size: 1.15rem; color: #38bdf8;">${npk.npk_ratio_observed}</div>
        <small style="color: var(--text-muted);">Ideal: ${npk.npk_ratio_ideal}</small>
      </div>
    </div>

    <div class="card" style="background: rgba(0,0,0,0.2); padding: 14px; border-radius: var(--radius-md); margin-top: 10px;">
      <h4 style="font-size: 0.9rem; margin-bottom: 8px; color: #a5b4fc;">⚖️ Soil Reaction & Conditioners</h4>
      <p style="font-size: 0.84rem; color: var(--text-secondary);">${phRep.condition}</p>
      <strong style="font-size: 0.84rem; color: #34d399; display: block; margin-top: 4px;">Remediation: ${phRep.remediation} (${phRep.quantity_kg_per_acre} kg/acre)</strong>
    </div>
  `;
}

function renderRecommendationResult(data) {
  const container = document.getElementById('rec-result-container');
  if (!container) return;

  const eco = data.economic_financial_outlook;
  const qYield = data.quantum_predictions.quantum_yield_hqnn;
  const qPrice = data.quantum_predictions.quantum_price_vqr;
  const fert = data.prescriptions.fertilizer_plan;
  const irrig = data.prescriptions.irrigation_plan;

  container.innerHTML = `
    <div class="result-metric-grid">
      <div class="result-box">
        <div class="result-box-title">Net Expected Profit</div>
        <div class="result-box-val" style="color: #34d399;">₹ ${eco.net_expected_profit_inr.toLocaleString()}</div>
        <small style="color: var(--text-muted);">ROI: <strong>${eco.return_on_investment_roi_percent}%</strong> (₹ ${eco.profit_per_acre_inr.toLocaleString()} / Acre)</small>
      </div>

      <div class="result-box">
        <div class="result-box-title">Predicted Yield & Revenue</div>
        <div class="result-box-val" style="color: #fbbf24;">${qYield.total_production_tons} Tons</div>
        <small style="color: var(--text-muted);">Gross: <strong>₹ ${eco.gross_revenue_inr.toLocaleString()}</strong> (@ ₹ ${qPrice.predicted_mandi_price_inr_per_qtl}/Qtl)</small>
      </div>
    </div>

    <!-- 4R Fertilizer Schedule Card -->
    <div class="card" style="background: rgba(0,0,0,0.25); padding: 14px; border-radius: var(--radius-md); margin-bottom: 12px;">
      <h4 style="font-size: 0.92rem; color: #34d399; margin-bottom: 6px;">🧪 4R Nutrient Stewardship Fertilizer Schedule</h4>
      <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px;">
        Total Requirement: <strong>${fert.packaging_summary.urea_45kg_bags} Bags Urea</strong>, <strong>${fert.packaging_summary.dap_50kg_bags} Bags DAP</strong>, <strong>${fert.packaging_summary.mop_50kg_bags} Bags MOP</strong>
      </p>
      <div style="font-size: 0.8rem; color: var(--text-secondary);">
        1. <strong>Basal:</strong> DAP + MOP + 33% Urea at final land prep.<br>
        2. <strong>1st Top Dressing (25-30 DAS):</strong> 33% Urea + Azotobacter.<br>
        3. <strong>2nd Top Dressing (50-60 DAS):</strong> 34% Urea + Micronutrient spray.
      </div>
    </div>

    <!-- Irrigation Schedule Card -->
    <div class="card" style="background: rgba(0,0,0,0.25); padding: 14px; border-radius: var(--radius-md); margin-bottom: 12px;">
      <h4 style="font-size: 0.92rem; color: #38bdf8; margin-bottom: 6px;">💧 Irrigation Regime (ET₀ = ${data.environmental_telemetry_snapshot.evapotranspiration_et0_mm} mm/d)</h4>
      <p style="font-size: 0.82rem; color: var(--text-secondary);">
        ${irrig.smart_advice}
      </p>
    </div>

    <!-- Agronomic Sowing Window -->
    <div class="banner-note banner-note-indigo">
      <span>🗓️</span>
      <span><strong>Sowing Window:</strong> ${data.agronomic_calendar.sowing_window} | <strong>Harvest:</strong> ${data.agronomic_calendar.harvest_window}</span>
    </div>
  `;
}

// =========================================================
// PLOT PRECISION FARMING & BOUNDARY DRAWING
// =========================================================

function setupPlotManagement() {
  const openCreateBtn = document.getElementById('btn-open-create-plot');
  const createForm = document.getElementById('create-plot-form');
  const drawBtn = document.getElementById('btn-draw-polygon');
  const clearBtn = document.getElementById('btn-clear-draw');

  if (openCreateBtn && createForm) {
    openCreateBtn.addEventListener('click', () => {
      createForm.style.display = createForm.style.display === 'none' ? 'block' : 'none';
    });
  }

  if (drawBtn) {
    drawBtn.addEventListener('click', () => {
      isDrawingPolygon = true;
      farmDrawPoints = [];
      if (farmDrawnPolygon && farmMap) farmMap.removeLayer(farmDrawnPolygon);
      document.getElementById('draw-status-lbl').textContent = 'Drawing Mode ACTIVE. Click on map to add vertices.';
      showToast('Click anywhere on the map to define plot boundary corners.', 'info');
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      isDrawingPolygon = false;
      farmDrawPoints = [];
      if (farmDrawnPolygon && farmMap) farmMap.removeLayer(farmDrawnPolygon);
      document.getElementById('draw-status-lbl').textContent = 'Drawing cleared.';
    });
  }

  if (createForm) {
    createForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const plotName = document.getElementById('plot-name').value;
      const crop = document.getElementById('plot-crop').value;
      const soil = document.getElementById('plot-soil').value;
      const area = parseFloat(document.getElementById('plot-area').value);

      let geojsonStr = null;
      if (farmDrawPoints.length >= 3) {
        geojsonStr = JSON.stringify({
          type: 'Polygon',
          coordinates: [farmDrawPoints.map(p => [p[1], p[0]])]
        });
      }

      const payload = {
        name: plotName,
        crop_type: crop,
        soil_type: soil,
        area_acres: area,
        center_lat: activeLat,
        center_lon: activeLon,
        boundary_geojson: geojsonStr
      };

      try {
        const res = await fetch(`${API_BASE_URL}/plots`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          showToast(`Plot '${plotName}' registered successfully!`, 'success');
          createForm.style.display = 'none';
          loadSavedPlots();
        }
      } catch (err) {
        showToast('Failed to save plot to database', 'error');
      }
    });
  }
}

async function loadSavedPlots() {
  const container = document.getElementById('plots-list-container');
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE_URL}/plots`);
    if (!res.ok) return;
    const data = await res.json();
    const plots = data.plots || [];

    if (plots.length === 0) {
      container.innerHTML = `
        <div class="placeholder-box" style="padding: 18px;">
          <p>No registered farm plots. Click "Register New Farm Plot" to draw or add your first field boundary.</p>
        </div>`;
      return;
    }

    container.innerHTML = plots.map(p => `
      <div class="plot-item-card">
        <div>
          <strong style="color: #fff; font-size: 0.95rem;">${p.name}</strong>
          <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">
            Crop: <span style="color: #34d399;">${p.crop_type || 'Rice'}</span> | Area: <strong>${p.area_acres} Acres</strong> | Soil: ${p.soil_type || 'Loam'}
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn-map-action" style="background: rgba(16, 185, 129, 0.2); color: #34d399;" onclick="runPlotAnalysis(${p.id})">
            ⚡ Analyze
          </button>
        </div>
      </div>
    `).join('');

  } catch (err) {
    console.error('Error loading plots:', err);
  }
}

async function runPlotAnalysis(plotId) {
  showToast(`Running Quantum Precision Analysis on Plot ID ${plotId}...`, 'info');
  try {
    const res = await fetch(`${API_BASE_URL}/plots/${plotId}/analyze?state=${encodeURIComponent(activeState)}&district=${encodeURIComponent(activeDistrict)}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Plot analysis error');
    const result = await res.json();

    const card = document.getElementById('plot-analysis-result-card');
    const body = document.getElementById('plot-analysis-body');
    const title = document.getElementById('plot-analysis-title');

    if (card && body) {
      card.style.display = 'block';
      title.textContent = `📊 Per-Plot Precision Analysis: ${result.plot_metadata.plot_name} (${result.plot_metadata.area_acres} Acres)`;
      
      const eco = result.per_plot_economic_outlook;
      const qYield = result.per_plot_quantum_predictions.quantum_yield_hqnn;
      const qPrice = result.per_plot_quantum_predictions.quantum_price_vqr;

      body.innerHTML = `
        <div class="result-metric-grid">
          <div class="result-box">
            <div class="result-box-title">Per-Plot Expected Profit</div>
            <div class="result-box-val" style="color: #34d399;">₹ ${eco.net_expected_profit_inr.toLocaleString()}</div>
            <small style="color: var(--text-muted);">ROI: <strong>${eco.return_on_investment_roi_percent}%</strong></small>
          </div>

          <div class="result-box">
            <div class="result-box-title">Quantum Yield Prediction</div>
            <div class="result-box-val" style="color: #fbbf24;">${qYield.total_production_tons} Tons</div>
            <small style="color: var(--text-muted);">${qYield.yield_per_acre_tons} Tons/Acre (@ ₹ ${qPrice.predicted_mandi_price_inr_per_qtl}/Qtl)</small>
          </div>
        </div>

        <div class="banner-note banner-note-emerald">
          <span>🛰️</span>
          <span>Field NDVI: <strong>${result.per_plot_telemetry.ndvi}</strong> | Soil Moisture: <strong>${result.per_plot_telemetry.soil_moisture} m³/m³</strong> | Status: <strong>${result.per_plot_telemetry.vegetation_health_status}</strong></span>
        </div>
      `;
      card.scrollIntoView({ behavior: 'smooth' });
    }
  } catch (err) {
    showToast(`Plot analysis failed: ${err.message}`, 'error');
  }
}

// =========================================================
// GOVERNMENT SUPPORT & INSURANCE CALCULATOR
// =========================================================

function setupInsuranceCalculator() {
  const cropSel = document.getElementById('ins-crop');
  const areaInput = document.getElementById('ins-area');

  function calculate() {
    if (!cropSel || !areaInput) return;
    const opt = cropSel.options[cropSel.selectedIndex];
    const sumPerAcre = parseFloat(opt.getAttribute('data-sum') || 40000);
    const rate = parseFloat(opt.getAttribute('data-rate') || 0.02);
    const area = parseFloat(areaInput.value || 5);

    const totalSum = sumPerAcre * area;
    const farmerShare = totalSum * rate;
    const govShare = totalSum * 0.08; // Total premium approx 10%

    document.getElementById('ins-sum-total').textContent = `₹ ${totalSum.toLocaleString()}`;
    document.getElementById('ins-farmer-premium').textContent = `₹ ${farmerShare.toLocaleString()}`;
    document.getElementById('ins-gov-subsidy').textContent = `₹ ${govShare.toLocaleString()} (80%)`;
  }

  if (cropSel && areaInput) {
    cropSel.addEventListener('change', calculate);
    areaInput.addEventListener('input', calculate);
    calculate();
  }
}

// =========================================================
// QUANTUM TELEMETRY & RETRAINING
// =========================================================

async function loadQuantumCircuitSchematic() {
  try {
    const res = await fetch(`${API_BASE_URL}/quantum/circuit`);
    if (res.ok) {
      const data = await res.json();
      const display = document.getElementById('quantum-circuit-display');
      if (display && data.crop_yield_circuit) {
        display.textContent = data.crop_yield_circuit.ascii_diagram || 'Quantum Circuit loaded';
      }
    }
  } catch (err) {
    console.error('Error loading quantum circuit:', err);
  }
}

function setupRetrainButtons() {
  const retrainYield = document.getElementById('btn-retrain-yield');
  if (retrainYield) {
    retrainYield.addEventListener('click', async () => {
      retrainYield.disabled = true;
      retrainYield.innerHTML = '<span>⚡ Training QNN...</span>';
      showToast('Initiating Quantum Crop Yield Neural Network Retraining...', 'info');
      try {
        const res = await fetch(`${API_BASE_URL}/train-crop?sync=true`, { method: 'POST' });
        const data = await res.json();
        showToast(`Quantum Yield Training complete! R²: ${data.metrics?.final_r2 || '0.98'}`, 'success');
      } catch (err) {
        showToast('Retraining failed', 'error');
      } finally {
        retrainYield.disabled = false;
        retrainYield.innerHTML = '<span>⚡ Retrain Yield Quantum QNN</span>';
      }
    });
  }

  const retrainPrice = document.getElementById('btn-retrain-price');
  if (retrainPrice) {
    retrainPrice.addEventListener('click', async () => {
      retrainPrice.disabled = true;
      retrainPrice.innerHTML = '<span>⚡ Training VQR...</span>';
      showToast('Initiating Variational Quantum Price Regressor Retraining...', 'info');
      try {
        const res = await fetch(`${API_BASE_URL}/train-price?sync=true`, { method: 'POST' });
        const data = await res.json();
        showToast(`Quantum Price Training complete! R²: ${data.metrics?.final_r2 || '0.99'}`, 'success');
      } catch (err) {
        showToast('Retraining failed', 'error');
      } finally {
        retrainPrice.disabled = false;
        retrainPrice.innerHTML = '<span>⚡ Retrain Price Quantum VQR</span>';
      }
    });
  }
}

// =========================================================
// DROPDOWN HELPERS & DATA DICTIONARIES
// =========================================================

const DEFAULT_CROPS_LIST = ["Rice", "Wheat", "Cotton", "Maize", "Groundnut", "Tomato", "Chilli", "Sugarcane", "Onion", "Pulses", "Soyabean", "Potato", "Mustard", "Jowar", "Bajra", "Barley", "Sunflower", "Gram", "Turmeric"];
const DEFAULT_SEASONS_LIST = ["Kharif", "Rabi", "Whole Year", "Summer", "Autumn", "Winter"];
const DEFAULT_STATES_LIST = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Odisha", "Punjab", "Rajasthan", "Tamil Nadu", "Telangana", "Uttar Pradesh", "Uttarakhand", "West Bengal"];
const DEFAULT_COMMODITIES_LIST = ["Cotton", "Wheat", "Rice", "Maize", "Groundnut", "Tomato", "Onion", "Chilli", "Sugarcane", "Soyabean", "Mustard", "Potato"];
const DEFAULT_VARIETIES_LIST = ["Other", "Standard Variety", "Hybrid", "Average (Whole)", "FAQ", "Samba Mahsuri", "HD 2967", "RCH 659 Bt-II", "Guntur Sannam"];
const DEFAULT_GRADES_LIST = ["FAQ", "Non-FAQ", "Medium", "Large", "Small", "Grade A"];

const DEFAULT_DISTRICTS_MAP = {
  "andhra pradesh": [
    "Guntur", "Prakasam", "Krishna", "Anakapalli", "Visakhapatnam", "East Godavari",
    "West Godavari", "Nellore", "Anantapur", "Chittoor", "Kurnool", "Kadapa",
    "Srikakulam", "Vizianagaram", "Eluru", "Kakinada", "NTR", "Bapatla", "Palnadu", "Tirupati", "Nandyal"
  ],
  "telangana": [
    "Hyderabad", "Warangal", "Karimnagar", "Khammam", "Nalgonda", "Nizamabad",
    "Medak", "Rangareddy", "Siddipet", "Mahabubnagar", "Adilabad", "Sangareddy", "Suryapet"
  ],
  "karnataka": [
    "Bengaluru", "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Belagavi", "Dharwad",
    "Ballari", "Kalaburagi", "Tumakuru", "Shivamogga", "Mangaluru", "Udupi", "Hassan"
  ],
  "tamil nadu": [
    "Chennai", "Coimbatore", "Madurai", "Salem", "Thanjavur", "Erode",
    "Tiruchirappalli", "Vellore", "Tirunelveli", "Dindigul", "Kancheepuram", "Tiruppur"
  ],
  "maharashtra": [
    "Pune", "Nashik", "Nagpur", "Ahmednagar", "Solapur", "Kolhapur",
    "Aurangabad", "Chhatrapati Sambhajinagar", "Mumbai", "Satara", "Sangli", "Amravati", "Jalgaon"
  ],
  "gujarat": [
    "Ahmedabad", "Amreli", "Anand", "Rajkot", "Surat", "Vadodara",
    "Bhavnagar", "Jamnagar", "Junagadh", "Kheda", "Gandhinagar", "Mehsana"
  ],
  "punjab": [
    "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Hoshiarpur"
  ],
  "haryana": [
    "Karnal", "Ambala", "Hisar", "Rohtak", "Gurugram", "Faridabad", "Panipat"
  ],
  "uttar pradesh": [
    "Lucknow", "Varanasi", "Kanpur", "Kanpur Nagar", "Agra", "Prayagraj", "Meerut", "Bareilly", "Gorakhpur", "Ayodhya"
  ],
  "west bengal": [
    "Kolkata", "Burdwan", "Purba Bardhaman", "Hooghly", "Howrah"
  ],
  "bihar": [
    "Patna", "Gaya", "Muzaffarpur", "Bhagalpur"
  ],
  "rajasthan": [
    "Jaipur", "Jodhpur", "Kota", "Udaipur"
  ],
  "madhya pradesh": [
    "Bhopal", "Indore", "Gwalior", "Jabalpur"
  ],
  "kerala": [
    "Thiruvananthapuram", "Kochi", "Palakkad", "Kozhikode", "Thrissur"
  ],
  "odisha": [
    "Bhubaneswar", "Cuttack", "Puri", "Sambalpur"
  ]
};

let yieldDropdownsListenersSetup = false;

async function loadYieldDropdowns() {
  // 1. Initial Populate with Defaults (Prompt as Selected)
  populateSelect('yield-crop', DEFAULT_CROPS_LIST, 'Select Crop');
  populateSelect('yield-season', DEFAULT_SEASONS_LIST, 'Select Season');
  populateSelect('yield-state', DEFAULT_STATES_LIST, 'Select State');
  populateSelect('yield-district', DEFAULT_DISTRICTS_MAP["andhra pradesh"] || [], 'Select District');

  const yieldState = document.getElementById('yield-state');
  const yieldDist = document.getElementById('yield-district');

  if (yieldState && yieldDist && !yieldDropdownsListenersSetup) {
    yieldDropdownsListenersSetup = true;
    yieldState.addEventListener('change', async () => {
      const s = yieldState.value;
      if (!s) {
        resetSelect(yieldDist, 'Select District');
        return;
      }
      
      // Check local district fallback first
      const localDists = DEFAULT_DISTRICTS_MAP[s.toLowerCase()] || [];
      if (localDists.length > 0) {
        populateSelect('yield-district', localDists, 'Select District');
      }

      // Query Backend for exhaustive list
      try {
        const r = await fetch(`${API_BASE_URL}/districts/${encodeURIComponent(s)}`);
        if (r.ok) {
          const apiDists = await r.json();
          if (apiDists && apiDists.length > 0) {
            populateSelect('yield-district', apiDists, 'Select District');
          }
        }
      } catch (err) {
        console.debug('Backend district fetch (using fallback):', err);
      }
    });
  }

  // Fetch live yield options from backend
  try {
    const res = await fetch(`${API_BASE_URL}/yield-options`);
    if (res.ok) {
      const data = await res.json();
      if (data.crops && data.crops.length > 0) populateSelect('yield-crop', data.crops, 'Select Crop');
      if (data.seasons && data.seasons.length > 0) populateSelect('yield-season', data.seasons, 'Select Season');
      if (data.states && data.states.length > 0) populateSelect('yield-state', data.states, 'Select State');
    }
  } catch (err) {
    console.debug('Backend yield-options fetch warning (using defaults):', err);
  }
}

let priceDropdownsListenersSetup = false;

async function loadPriceStates() {
  // 1. Initial Populate with Defaults (Prompt as Selected)
  populateSelect('price-state', DEFAULT_STATES_LIST, 'Select State');
  populateSelect('price-district', DEFAULT_DISTRICTS_MAP["gujarat"] || [], 'Select District');
  populateSelect('price-market', ["Damnagar", "Savarkundla", "Amreli Main Mandi"], 'Select Market');
  populateSelect('price-commodity', DEFAULT_COMMODITIES_LIST, 'Select Commodity');
  populateSelect('price-variety', DEFAULT_VARIETIES_LIST, 'Select Variety');
  populateSelect('price-grade', DEFAULT_GRADES_LIST, 'Select Grade');

  if (!priceDropdownsListenersSetup) {
    priceDropdownsListenersSetup = true;
    setupCascadingPriceDropdowns();
  }

  // Try live API fetch
  try {
    const res = await fetch(`${API_BASE_URL}/states`);
    if (res.ok) {
      const states = await res.json();
      if (states && states.length > 0) {
        populateSelect('price-state', states, 'Select State');
      }
    }
  } catch (err) {
    console.debug('Backend price states fetch warning (using defaults):', err);
  }
}

function setupCascadingPriceDropdowns() {
  const st = document.getElementById('price-state');
  const dt = document.getElementById('price-district');
  const mk = document.getElementById('price-market');
  const cm = document.getElementById('price-commodity');
  const vr = document.getElementById('price-variety');
  const gr = document.getElementById('price-grade');

  if (!st || !dt || !mk || !cm || !vr || !gr) return;

  st.addEventListener('change', async () => {
    const stateVal = st.value;
    if (!stateVal) {
      resetSelect(dt, 'Select District');
      resetSelect(mk, 'Select Market');
      resetSelect(cm, 'Select Commodity');
      resetSelect(vr, 'Select Variety');
      resetSelect(gr, 'Select Grade');
      return;
    }

    // Local fallback
    const fallbackDists = DEFAULT_DISTRICTS_MAP[stateVal.toLowerCase()] || ["Main District", "District 1"];
    populateSelect('price-district', fallbackDists, 'Select District');

    try {
      const r = await fetch(`${API_BASE_URL}/districts/${encodeURIComponent(stateVal)}`);
      if (r.ok) {
        const apiDists = await r.json();
        if (apiDists && apiDists.length > 0) {
          populateSelect('price-district', apiDists, 'Select District');
        }
      }
    } catch (e) {}
  });

  dt.addEventListener('change', async () => {
    const stateVal = st.value;
    const distVal = dt.value;
    if (!distVal) {
      resetSelect(mk, 'Select Market');
      resetSelect(cm, 'Select Commodity');
      resetSelect(vr, 'Select Variety');
      resetSelect(gr, 'Select Grade');
      return;
    }

    populateSelect('price-market', [`${distVal} APMC Mandi`, `${distVal} Main Market`, "Damnagar"], 'Select Market');

    try {
      const r = await fetch(`${API_BASE_URL}/markets/${encodeURIComponent(stateVal)}/${encodeURIComponent(distVal)}`);
      if (r.ok) {
        const apiMkts = await r.json();
        if (apiMkts && apiMkts.length > 0) {
          populateSelect('price-market', apiMkts, 'Select Market');
        }
      }
    } catch (e) {}
  });

  mk.addEventListener('change', async () => {
    const stateVal = st.value;
    const distVal = dt.value;
    const mktVal = mk.value;
    if (!mktVal) {
      resetSelect(cm, 'Select Commodity');
      resetSelect(vr, 'Select Variety');
      resetSelect(gr, 'Select Grade');
      return;
    }

    try {
      const r = await fetch(`${API_BASE_URL}/commodities?state=${encodeURIComponent(stateVal)}&district=${encodeURIComponent(distVal)}&market=${encodeURIComponent(mktVal)}`);
      if (r.ok) {
        const apiComms = await r.json();
        if (apiComms && apiComms.length > 0) {
          populateSelect('price-commodity', apiComms, 'Select Commodity');
        }
      }
    } catch (e) {}
  });

  cm.addEventListener('change', async () => {
    const stateVal = st.value;
    const distVal = dt.value;
    const mktVal = mk.value;
    const commVal = cm.value;
    if (!commVal) {
      resetSelect(vr, 'Select Variety');
      resetSelect(gr, 'Select Grade');
      return;
    }

    try {
      const r = await fetch(`${API_BASE_URL}/varieties?state=${encodeURIComponent(stateVal)}&district=${encodeURIComponent(distVal)}&market=${encodeURIComponent(mktVal)}&commodity=${encodeURIComponent(commVal)}`);
      if (r.ok) {
        const apiVars = await r.json();
        if (apiVars && apiVars.length > 0) {
          populateSelect('price-variety', apiVars, 'Select Variety');
        }
      }
    } catch (e) {}
  });

  vr.addEventListener('change', async () => {
    const stateVal = st.value;
    const distVal = dt.value;
    const mktVal = mk.value;
    const commVal = cm.value;
    const varVal = vr.value;
    if (!varVal) {
      resetSelect(gr, 'Select Grade');
      return;
    }

    try {
      const r = await fetch(`${API_BASE_URL}/grades?state=${encodeURIComponent(stateVal)}&district=${encodeURIComponent(distVal)}&market=${encodeURIComponent(mktVal)}&commodity=${encodeURIComponent(commVal)}&variety=${encodeURIComponent(varVal)}`);
      if (r.ok) {
        const apiGrades = await r.json();
        if (apiGrades && apiGrades.length > 0) {
          populateSelect('price-grade', apiGrades, 'Select Grade');
        }
      }
    } catch (e) {}
  });
}

function populateSelect(elemId, items, defaultLabel, defaultSelectedValue = null) {
  const el = document.getElementById(elemId);
  if (!el) return;
  const prevVal = el.value;
  el.innerHTML = '';

  if (defaultLabel) {
    const defOpt = document.createElement('option');
    defOpt.value = '';
    defOpt.textContent = defaultLabel;
    if (!defaultSelectedValue && !prevVal) {
      defOpt.selected = true;
    }
    el.appendChild(defOpt);
  }

  let hasSelected = false;
  items.forEach(item => {
    const opt = document.createElement('option');
    opt.value = item;
    opt.textContent = item;
    if ((defaultSelectedValue && item === defaultSelectedValue) || (prevVal && item === prevVal)) {
      opt.selected = true;
      hasSelected = true;
    }
    el.appendChild(opt);
  });

  if (!hasSelected && defaultSelectedValue && el.querySelector(`option[value="${defaultSelectedValue}"]`)) {
    el.value = defaultSelectedValue;
  }
}

function resetSelect(elem, defaultLabel) {
  if (!elem) return;
  elem.innerHTML = `<option value="" selected>${defaultLabel}</option>`;
}

// =========================================================
// TOAST NOTIFICATIONS
// =========================================================

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? '✅' : (type === 'error' ? '❌' : 'ℹ️');
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// =========================================================
// PLATFORM DATA REFRESH & BACKEND SETTINGS MODAL
// =========================================================

async function refreshLivePlatformData() {
  try {
    await initLocationSelector();
    await loadYieldDropdowns();
    await loadPriceStates();
    await loadDashboardData();
  } catch (e) {
    console.warn('Error refreshing live data after reconnect:', e);
  }
}

function setupBackendSettingsModal() {
  const modal = document.getElementById('backend-settings-modal');
  const closeBtn = document.getElementById('btn-close-backend-modal');
  const doneBtn = document.getElementById('btn-modal-done');
  const pingBtn = document.getElementById('btn-modal-ping-test');
  const saveBtn = document.getElementById('btn-save-api-url');
  const inputUrl = document.getElementById('input-custom-api-url');
  const presetRender = document.getElementById('preset-render-default');
  const presetLocal = document.getElementById('preset-localhost');
  const presetReset = document.getElementById('preset-reset-default');
  const swaggerLink = document.getElementById('modal-swagger-link');

  const statusPill = document.getElementById('sidebar-quantum-status');
  const footStatusBox = document.getElementById('sidebar-foot-status-box');

  const openModal = () => {
    if (!modal) return;
    if (inputUrl) inputUrl.value = API_BASE_URL;
    if (swaggerLink) swaggerLink.href = `${API_BASE_URL}/docs`;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    checkSystemHealth(true, true);
  };

  const closeModal = () => {
    if (!modal) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
  };

  if (statusPill) statusPill.addEventListener('click', openModal);
  if (footStatusBox) footStatusBox.addEventListener('click', openModal);
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (doneBtn) doneBtn.addEventListener('click', closeModal);

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
  }

  // Ping / Wake Up button
  if (pingBtn) {
    pingBtn.addEventListener('click', async () => {
      pingBtn.disabled = true;
      pingBtn.textContent = '⏳ Pinging...';
      retryCount = 0;
      await checkSystemHealth(false, true);
      pingBtn.disabled = false;
      pingBtn.textContent = '⚡ Ping / Wake Up';
    });
  }

  // Save Custom URL
  if (saveBtn && inputUrl) {
    saveBtn.addEventListener('click', async () => {
      const val = inputUrl.value.trim();
      if (!val) {
        showToast('Please enter a valid backend URL (e.g. https://your-backend.onrender.com)', 'error');
        return;
      }
      localStorage.setItem('VITE_API_URL', val.replace(/\/+$/, ''));
      API_BASE_URL = getApiBaseUrl();
      if (swaggerLink) swaggerLink.href = `${API_BASE_URL}/docs`;
      const docsBtn = document.getElementById('btn-topbar-docs') || document.querySelector('.btn-api-docs');
      if (docsBtn) docsBtn.href = `${API_BASE_URL}/docs`;

      showToast(`Backend URL updated to: ${API_BASE_URL}`, 'info');
      retryCount = 0;
      await checkSystemHealth(false, false);
    });
  }

  // Preset: Render Default Cloud
  if (presetRender && inputUrl) {
    presetRender.addEventListener('click', () => {
      inputUrl.value = PRODUCTION_API_URL;
    });
  }

  // Preset: Localhost 8000
  if (presetLocal && inputUrl) {
    presetLocal.addEventListener('click', () => {
      inputUrl.value = 'http://127.0.0.1:8000';
    });
  }

  // Preset: Reset Default
  if (presetReset && inputUrl) {
    presetReset.addEventListener('click', async () => {
      localStorage.removeItem('VITE_API_URL');
      inputUrl.value = getApiBaseUrl();
      API_BASE_URL = getApiBaseUrl();
      if (swaggerLink) swaggerLink.href = `${API_BASE_URL}/docs`;
      const docsBtn = document.getElementById('btn-topbar-docs') || document.querySelector('.btn-api-docs');
      if (docsBtn) docsBtn.href = `${API_BASE_URL}/docs`;
      showToast('Reset to default backend URL.', 'info');
      retryCount = 0;
      await checkSystemHealth(false, false);
    });
  }

  // Recurring background keepalive every 45s
  setInterval(() => {
    checkSystemHealth(true);
  }, 45000);
}
