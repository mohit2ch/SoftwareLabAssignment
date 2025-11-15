// src/App.tsx
import React, { useState, useEffect, useCallback } from 'react';
import ProxyTable from './components/ProxyTable';
import type { ApiProxyItem, ProxyDisplayInfo, SchedulerStatus } from './types';
import './App.css'; // Your existing App.css

const API_BASE_URL = 'http://localhost:8000';
const POLLING_INTERVAL_MS = 5000;
const BLOCKED_COUNTRIES_LS_KEY = 'proxyAppBlockedCountries';
const VALIDATION_THREADS_LS_KEY = 'proxyAppValidationThreads'; // localStorage key for threads

const TIME_INTERVALS_SECONDS = [
  5 * 60, 10 * 60, 15 * 60, 30 * 60, 60 * 60, 120 * 60,
];
const THREAD_OPTIONS = [10, 20, 30, 40, 50, 75, 100, 150, 200]; // Example thread options

const formatDate = (isoString: string | null | undefined): string => {
  if (!isoString) return 'N/A';
  try { return new Date(isoString).toLocaleString(); } catch (e) { return 'Invalid Date'; }
};

const mapApiProxyToDisplay = (apiProxy: ApiProxyItem): ProxyDisplayInfo => {
  return {
    id: `${apiProxy.protocol}-${apiProxy.ip}-${apiProxy.port}`,
    proxyString: `${apiProxy.protocol}://${apiProxy.ip}:${apiProxy.port}`,
    status: apiProxy.is_valid ? 'Valid' : 'Invalid',
    anonymity: apiProxy.anonymity || 'N/A',
    country: apiProxy.country?.toUpperCase() || 'N/A',
    responseTimeString: apiProxy.response_time ? `${apiProxy.response_time.toFixed(2)} ms` : 'N/A',
    rawResponseTime: apiProxy.response_time,
    lastChecked: formatDate(apiProxy.last_checked),
    source: apiProxy.source || 'N/A',
  };
};

function App() {
  const [proxies, setProxies] = useState<ProxyDisplayInfo[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [selectedIntervalSeconds, setSelectedIntervalSeconds] = useState<number>(TIME_INTERVALS_SECONDS[2]);
  const [isLoading, setIsLoading] = useState<Record<string, boolean>>({});
  const [blockedCountries, setBlockedCountries] = useState<string[]>(() => {
    const saved = localStorage.getItem(BLOCKED_COUNTRIES_LS_KEY);
    return saved ? JSON.parse(saved) : [];
  });
  const [newBlockedCountry, setNewBlockedCountry] = useState<string>('');

  // --- Validation Threads State ---
  const [validationThreads, setValidationThreads] = useState<number>(() => {
    const savedThreads = localStorage.getItem(VALIDATION_THREADS_LS_KEY);
    return savedThreads ? parseInt(savedThreads, 10) : 50; // Default to 50
  });

  useEffect(() => {
    localStorage.setItem(BLOCKED_COUNTRIES_LS_KEY, JSON.stringify(blockedCountries));
  }, [blockedCountries]);

  useEffect(() => {
    localStorage.setItem(VALIDATION_THREADS_LS_KEY, validationThreads.toString());
  }, [validationThreads]);
  // --- End Validation Threads State ---


  const handleAddBlockedCountry = () => { /* ... (same as before) ... */
    const countryToAdd = newBlockedCountry.trim().toUpperCase();
    if (countryToAdd && !blockedCountries.includes(countryToAdd)) {
      setBlockedCountries(prev => [...prev, countryToAdd].sort());
      setNewBlockedCountry('');
    } else if (!countryToAdd) alert("Please enter a country code or name.");
    else alert(`"${countryToAdd}" is already in the blocklist.`);
  };
  const handleRemoveBlockedCountry = (countryToRemove: string) => { /* ... (same as before) ... */
    setBlockedCountries(prev => prev.filter(country => country !== countryToRemove));
  };

  const setLoading = (action: string, value: boolean) => setIsLoading(prev => ({ ...prev, [action]: value }));

  const fetchSchedulerStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/scheduler/status`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data: SchedulerStatus = await response.json();
      setSchedulerStatus(data);
      if (data.interval_seconds && data.interval_seconds !== selectedIntervalSeconds) {
        setSelectedIntervalSeconds(data.interval_seconds);
      }
      if (data.validation_threads && data.validation_threads !== validationThreads) { // Update local threads state
        setValidationThreads(data.validation_threads);
      }
    } catch (error) { console.error('Failed to fetch scheduler status:', error); }
  }, [selectedIntervalSeconds, validationThreads]); // Add validationThreads

  const fetchProxies = useCallback(async () => { /* ... (same as before) ... */
    try {
      const response = await fetch(`${API_BASE_URL}/proxies?only_valid=false`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data: ApiProxyItem[] = await response.json();
      setProxies(data.map(mapApiProxyToDisplay));
    } catch (error) { console.error('Failed to fetch proxies:', error); }
  }, []);

  useEffect(() => {
    fetchSchedulerStatus();
    fetchProxies();
    const intervalId = setInterval(() => {
      fetchSchedulerStatus();
      if (schedulerStatus?.status === 'running' || schedulerStatus?.status === 'validating') fetchProxies();
    }, POLLING_INTERVAL_MS);
    return () => clearInterval(intervalId);
  }, [fetchSchedulerStatus, fetchProxies, schedulerStatus?.status]);

  const handleApiAction = async (endpoint: string, actionName: string, method: 'POST' | 'GET' = 'POST', body?: any) => {
    setLoading(actionName, true);
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: method, headers: body ? { 'Content-Type': 'application/json' } : {},
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!response.ok) {
        let errorData = { detail: `HTTP error! status: ${response.status}` };
        try { errorData = await response.json(); } catch (e) {
          const textError = await response.text();
          errorData = { detail: textError || `HTTP error! status: ${response.status}`};
        }
        throw new Error(`Failed to ${actionName}: ${response.status} - ${errorData.detail || response.statusText}`);
      }
      await response.json();
      await fetchSchedulerStatus(); // This will update status including threads
      await fetchProxies();
    } catch (error) {
      console.error(`Error during ${actionName}:`, error);
      alert(`Error during ${actionName}: ${error instanceof Error ? error.message : String(error)}`);
    } finally { setLoading(actionName, false); }
  };

  const handleStartProcess = () => {
    // Ensure current thread setting is sent if scheduler is stopped
    // Or, backend could always use its current setting.
    // For simplicity, let's assume backend uses its current setting.
    // If you want to force threads on start:
    // await handleApiAction('/scheduler/threads', 'Set Threads on Start', 'POST', { validation_threads: validationThreads });
    handleApiAction('/scheduler/start', 'Start Process');
  };
  const handleStopProcess = () => handleApiAction('/scheduler/stop', 'Stop Process');
  const handleRefresh = () => handleApiAction('/scheduler/refresh', 'Refresh Proxies');
  const handleSetTimeIntervalChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newInterval = parseInt(event.target.value, 10);
    setSelectedIntervalSeconds(newInterval);
    handleApiAction('/scheduler/interval', 'Set Interval', 'POST', { interval_seconds: newInterval });
  };
  const handleSetValidationThreadsChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newThreads = parseInt(event.target.value, 10);
    setValidationThreads(newThreads); // Update local state immediately for UI responsiveness
    handleApiAction('/scheduler/threads', 'Set Threads', 'POST', { validation_threads: newThreads });
  };
  const handleStopAndExit = () => handleApiAction('/scheduler/stop', 'Stop and Exit');


  return (
    <div className="app-container">
      {/* <h1 className="app-main-title">PSADGM Application</h1> */}
      <header className="header-controls">
        <div className="button-group">
          <button className="btn btn-start" onClick={handleStartProcess} disabled={isLoading['Start Process'] || schedulerStatus?.status === 'running' || schedulerStatus?.status === 'validating'}>
            {isLoading['Start Process'] ? 'Starting...' : 'Start Process'}
          </button>
          {/* ... other buttons ... */}
          <button className="btn btn-stop" onClick={handleStopProcess} disabled={isLoading['Stop Process'] || schedulerStatus?.status === 'stopped'}>
            {isLoading['Stop Process'] ? 'Stopping...' : 'Stop Process'}
          </button>
          <button className="btn btn-refresh" onClick={handleRefresh} disabled={isLoading['Refresh Proxies'] || schedulerStatus?.status === 'stopped'}>
            {isLoading['Refresh Proxies'] ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </div>

        <div className="settings-group"> {/* Wrapper for interval and threads */}
            <div className="time-interval-group">
                <label htmlFor="time-interval-select">Interval:</label>
                <select
                    id="time-interval-select" className="select-control" value={selectedIntervalSeconds}
                    onChange={handleSetTimeIntervalChange}
                    disabled={isLoading['Set Interval'] || !schedulerStatus}
                >
                    {TIME_INTERVALS_SECONDS.map((intervalSec) => (
                    <option key={intervalSec} value={intervalSec}> {intervalSec / 60} min </option>
                    ))}
                </select>
            </div>
            <div className="validation-threads-group">
                <label htmlFor="validation-threads-select">Threads:</label>
                <select
                    id="validation-threads-select" className="select-control" value={validationThreads}
                    onChange={handleSetValidationThreadsChange}
                    disabled={isLoading['Set Threads'] || !schedulerStatus}
                >
                    {THREAD_OPTIONS.map((threads) => (
                    <option key={threads} value={threads}> {threads} </option>
                    ))}
                </select>
            </div>
        </div>
      </header>

      <div className="scheduler-info">
        {schedulerStatus ? (
          <>
            <p>Status: <span className={`status-text status-${schedulerStatus.status}`}>{schedulerStatus.status.toUpperCase()} </span></p>
            <p>Proxies: {schedulerStatus.current_proxy_count} (Valid: {schedulerStatus.valid_proxy_count})</p>
            <p>Last Run: {formatDate(schedulerStatus.last_run_time)}</p>
            <p>Next Run: {formatDate(schedulerStatus.next_run_time)}</p>
            <p>Threads: {schedulerStatus.validation_threads}</p> {/* Display current threads */}
          </>
        ) : ( <p>Loading scheduler info...</p> )}
      </div>

      <main className="table-area">
        <ProxyTable proxies={proxies} schedulerStatus={schedulerStatus} blockedCountries={blockedCountries} />
      </main>

      <section className="blocklist-section">
        <h2 className="blocklist-title">Country Blocklist</h2>
        <div className="blocklist-input-group">
          <input type="text" className="blocklist-input" placeholder="Enter Country Code/Name (e.g., US, China)"
            value={newBlockedCountry} onChange={(e) => setNewBlockedCountry(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddBlockedCountry()}
          />
          <button className="btn btn-add-blocklist" onClick={handleAddBlockedCountry}>Add to Blocklist</button>
        </div>
        {blockedCountries.length > 0 && (
          <ul className="blocked-countries-list">
            {blockedCountries.map(country => (
              <li key={country} className="blocked-country-item">
                <span>{country}</span>
                <button className="btn-remove-blocklist" onClick={() => handleRemoveBlockedCountry(country)} title={`Remove ${country}`}>×</button>
              </li>
            ))}
          </ul>
        )}
         {blockedCountries.length === 0 && (<p className="blocklist-empty-message">No countries are currently blocked.</p>)}
      </section>

      <footer className="footer-actions">
        <button className="btn btn-exit" onClick={handleStopAndExit} disabled={isLoading['Stop and Exit']}>
         {isLoading['Stop and Exit'] ? 'Stopping...' : 'Stop Scheduler & Exit UI'}
        </button>
      </footer>
    </div>
  );
}
export default App;