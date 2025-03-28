document.addEventListener('DOMContentLoaded', function() {
    // Load server list on page load
    loadServerList();
    
    // Setup event listeners
    const saveIdleSettings = document.getElementById('saveIdleSettings');
    
    if (saveIdleSettings) {
        saveIdleSettings.addEventListener('click', handleSaveIdleSettings);
    }

    // Refresh server list every second
    setInterval(loadServerList, 1000);
});

function formatIdleTime(idleStartTime, idleDurationMins) {
    if (!idleStartTime) return 'Not idle';
    
    const hours = Math.floor(idleDurationMins / 60);
    const mins = idleDurationMins % 60;
    
    if (hours > 0) {
        return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
}

function formatDateTime(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    // Add 8 hours to convert to UTC+8
    const utc8Date = new Date(date.getTime() + (8 * 60 * 60 * 1000));
    return utc8Date.toLocaleString('en-US', { 
        timeZone: 'Asia/Taipei',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function loadServerList() {
    fetch('/api/servers')
        .then(response => response.json())
        .then(servers => {
            const serverList = document.getElementById('serverList');
            if (!serverList) return;

            serverList.innerHTML = '';
            servers.forEach(server => {
                const row = createServerRow(server);
                serverList.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading servers:', error));
}

function createServerRow(server) {
    const tr = document.createElement('tr');
    
    // Server name
    tr.innerHTML = `
        <td>${server.name}</td>
        <td>
            <span class="badge bg-${server.power_state === 'ON' ? 'success' : 'secondary'}">
                ${server.power_state.toUpperCase()}
            </span>
        </td>
        <td>${formatDateTime(server.last_update_time)}</td>
        <td>
            <div>CPU: ${server.current_usage?.cpu_usage?.toFixed(1)}%</div>
            <div>GPU: ${server.current_usage?.gpu_usage?.toFixed(1)}%</div>
        </td>
        <td>
            ${formatIdleTime(server.idle_start_time, server.idle_duration_mins)}
        </td>
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="openIdleSettings('${server.name}', ${server.idle_threshold_mins}, ${server.auto_shutdown_enabled})">
                <i class="bi bi-gear"></i> Settings
            </button>
        </td>
        <td>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-${server.power_state === 'ON' ? 'danger' : 'success'}"
                        onclick="togglePower('${server.name}', '${server.power_state}')">
                    ${server.power_state === 'ON' ? 'Power Off' : 'Power On'}
                </button>
            </div>
        </td>
    `;
    
    return tr;
}

function togglePower(serverName, currentState) {
    const action = currentState === 'ON' ? 'off' : 'on';
    const confirmMessage = `Are you sure you want to power ${action} server "${serverName}"?`;
    
    if (!confirm(confirmMessage)) {
        return; // 如果用戶點擊取消，就不執行後續操作
    }

    fetch(`/api/servers/name/${serverName}/power/${action}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadServerList();
        } else {
            alert(`Failed to ${action} server: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error toggling power:', error);
        alert('Failed to toggle server power');
    });
}

function openIdleSettings(serverName, threshold, autoShutdown) {
    const modal = new bootstrap.Modal(document.getElementById('idleSettingsModal'));
    document.getElementById('idleSettingsServerName').value = serverName;
    document.getElementById('idleThreshold').value = threshold;
    document.getElementById('autoShutdown').checked = autoShutdown;
    modal.show();
}

function handleSaveIdleSettings() {
    const serverName = document.getElementById('idleSettingsServerName').value;
    const threshold = parseInt(document.getElementById('idleThreshold').value);
    const autoShutdown = document.getElementById('autoShutdown').checked;
    
    fetch(`/api/servers/name/${serverName}/idle-settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            idle_threshold_mins: threshold,
            auto_shutdown_enabled: autoShutdown
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('idleSettingsModal'));
            modal.hide();
            loadServerList();
        } else {
            alert('Failed to save idle settings: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error saving idle settings:', error);
        alert('Failed to save idle settings');
    });
}
