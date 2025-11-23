import React, { useState, useMemo, useEffect } from 'react'; // Added useEffect for console logs
import './ProxyTable.css';
import type { ProxyDisplayInfo, SchedulerStatus } from '../types';

type ProxyFilterType = 'all' | 'valid' | 'invalid';
type ProxySortByType = 'default' | 'responseTimeAsc' | 'responseTimeDesc';

interface ProxyTableProps {
  proxies: ProxyDisplayInfo[];
  schedulerStatus?: SchedulerStatus | null;
  blockedCountries: string[];
}

const ProxyTable: React.FC<ProxyTableProps> = ({ proxies, schedulerStatus, blockedCountries }) => {
  const [filter, setFilter] = useState<ProxyFilterType>('all');
  const [sortBy, setSortBy] = useState<ProxySortByType>('default');

  // For debugging:
  useEffect(() => { console.log('[ProxyTable] Filter state updated to:', filter); }, [filter]);
  useEffect(() => { console.log('[ProxyTable] SortBy state updated to:', sortBy); }, [sortBy]);
  useEffect(() => { console.log('[ProxyTable] Proxies prop updated, length:', proxies.length); }, [proxies]);
  useEffect(() => { console.log('[ProxyTable] BlockedCountries prop updated, length:', blockedCountries.length);}, [blockedCountries]);


  const proxiesAfterCountryBlock = useMemo(() => {
    // console.log('[ProxyTable] Recalculating proxiesAfterCountryBlock. Input proxies:', proxies.length, 'Blocked:', blockedCountries);
    if (blockedCountries.length > 0) {
      return proxies.filter(p =>
        !p.country || !blockedCountries.includes(p.country.toUpperCase())
      );
    }
    return proxies;
  }, [proxies, blockedCountries]);

  const filteredAndSortedProxies = useMemo(() => {
    // console.log('[ProxyTable] Recalculating filteredAndSortedProxies. Proxies after country block:', proxiesAfterCountryBlock.length, 'Filter:', filter, 'SortBy:', sortBy);
    let processedProxies = [...proxiesAfterCountryBlock]; // Start with country-filtered proxies

    if (filter === 'valid') {
      processedProxies = processedProxies.filter(p => p.status === 'Valid');
    } else if (filter === 'invalid') {
      processedProxies = processedProxies.filter(p => p.status === 'Invalid');
    }

    if (sortBy === 'responseTimeAsc') {
      processedProxies.sort((a, b) => {
        const timeA = a.rawResponseTime === null || a.rawResponseTime === undefined ? Infinity : a.rawResponseTime;
        const timeB = b.rawResponseTime === null || b.rawResponseTime === undefined ? Infinity : b.rawResponseTime;
        return timeA - timeB;
      });
    } else if (sortBy === 'responseTimeDesc') {
      processedProxies.sort((a, b) => {
        const timeA = a.rawResponseTime === null || a.rawResponseTime === undefined ? Infinity : a.rawResponseTime;
        const timeB = b.rawResponseTime === null || b.rawResponseTime === undefined ? Infinity : b.rawResponseTime;
        return timeB - timeA;
      });
    }
    // console.log('[ProxyTable] Final list for table render, length:', processedProxies.length);
    return processedProxies;
  }, [proxiesAfterCountryBlock, filter, sortBy]); // Depend on country-filtered list

  const toggleSortByResponseTime = () => {
    if (sortBy === 'responseTimeAsc') setSortBy('responseTimeDesc');
    else if (sortBy === 'responseTimeDesc') setSortBy('default');
    else setSortBy('responseTimeAsc');
  };

  const getSortButtonText = () => {
    if (sortBy === 'responseTimeAsc') return 'Speed (Fastest)';
    if (sortBy === 'responseTimeDesc') return 'Speed (Slowest)';
    return 'Sort by Speed';
  };

  // Counts for buttons based on proxiesAfterCountryBlock
  const allCount = proxiesAfterCountryBlock.length;
  const validCount = proxiesAfterCountryBlock.filter(p => p.status === 'Valid').length;
  const invalidCount = proxiesAfterCountryBlock.filter(p => p.status === 'Invalid').length;


  if (!schedulerStatus) return <p className="no-data-message">Loading scheduler status...</p>;

  const isLoadingFirstTime = schedulerStatus.validation_in_progress && proxies.length === 0; // Based on raw proxies from App
  const noProxiesAfterLoad = !schedulerStatus.validation_in_progress && proxies.length === 0 && schedulerStatus.current_proxy_count === 0 && schedulerStatus.status !== 'stopped';

  return (
    <div className="proxy-table-container">
      <div className="table-controls">
        <span className="table-section-title">Available Proxies</span>
        <div className="filter-sort-group">
          <div className="filter-buttons">
            <button className={`filter-btn ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>All ({allCount})</button>
            <button className={`filter-btn ${filter === 'valid' ? 'active' : ''} valid`} onClick={() => setFilter('valid')}>Valid ({validCount})</button>
            <button className={`filter-btn ${filter === 'invalid' ? 'active' : ''} invalid`} onClick={() => setFilter('invalid')}>Invalid ({invalidCount})</button>
          </div>
          <button className={`sort-btn ${sortBy !== 'default' ? 'active' : ''}`} onClick={toggleSortByResponseTime} disabled={filteredAndSortedProxies.length === 0}>
            {getSortButtonText()}
          </button>
        </div>
      </div>
      {schedulerStatus.status === 'stopped' && proxies.length === 0 && !schedulerStatus.validation_in_progress && <p className="no-data-message prominent">Scheduler stopped. Start process.</p>}
      {isLoadingFirstTime && <p className="no-data-message prominent">Scheduler validating for first time...</p>}
      {noProxiesAfterLoad && <p className="no-data-message prominent">No proxies found in last run.</p>}
      {(proxies.length > 0 || schedulerStatus.validation_in_progress) && !isLoadingFirstTime && !noProxiesAfterLoad && (
        <div className="table-responsive-wrapper">
          {filteredAndSortedProxies.length === 0 && <p className="no-data-message">No proxies match current filters.</p>}
          {filteredAndSortedProxies.length > 0 && (
            <table className="proxy-table">
              <thead><tr><th>Proxy String</th><th>Status</th><th>Anonymity</th><th>Country</th><th>Response Time</th><th>Last Checked</th><th>Source</th></tr></thead>
              <tbody>
                {filteredAndSortedProxies.map(proxy => (
                  <tr key={proxy.id} className={`proxy-row status-row-${proxy.status.toLowerCase()}`}>
                    <td className="cell-proxy-string">{proxy.proxyString}</td>
                    <td><span className={`status-badge status-${proxy.status.toLowerCase()}`}>{proxy.status}</span></td>
                    <td>{proxy.anonymity}</td><td>{proxy.country}</td><td>{proxy.responseTimeString}</td><td>{proxy.lastChecked}</td><td>{proxy.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};
export default ProxyTable;