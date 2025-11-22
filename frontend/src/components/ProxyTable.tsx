import React, { useEffect, useState } from "react";
import "./ProxyTable.css";

export default function ProxyTable({ data }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("theme") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((t) => (t === "light" ? "dark" : "light"));
  };

  return (
    <div className="proxy-table-container">
      <div className="table-controls">
        <div className="table-section-title">Proxy Table</div>

        {/* Theme Toggle Button */}
        <button className="sort-btn" onClick={toggleTheme}>
          {theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
        </button>
      </div>

      <div className="table-responsive-wrapper">
        <table className="proxy-table">
          <thead>
            <tr>
              <th>Proxy</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data && data.length > 0 ? (
              data.map((row, i) => (
                <tr
                  key={i}
                  className={`proxy-row status-row-${row.status}`}
                >
                  <td className="cell-proxy-string">{row.proxy}</td>
                  <td>
                    <span className={`status-badge status-${row.status}`}>
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="2" className="no-data-message prominent">
                  No proxies found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
