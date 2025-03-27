document.addEventListener('DOMContentLoaded', function() {
    // Load server list on page load
    loadServerList();
    
    // Setup event listeners
    const addServerForm = document.getElementById('addServerForm');
    const addServerSubmit = document.getElementById('addServerSubmit');
    if (addServerSubmit) {
        addServerSubmit.addEventListener('click', handleAddServer);
    }

    // Refresh server list every 30 seconds
    setInterval(loadServerList, 30000);
});

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
        <td>${server.ipmi_host}</td>
        <td>
            <span class="badge bg-${server.power_state === 'on' ? 'success' : 'danger'}">
                ${server.power_state}
            </span>
        </td>
        <td>${new Date(server.last_update_time).toLocaleString()}</td>
        <td>
            <div>CPU: ${server.current_usage?.cpu_usage?.toFixed(1)}%</div>
            <div>GPU: ${server.current_usage?.gpu_usage?.toFixed(1)}%</div>
        </td>
        <td>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-${server.power_state === 'on' ? 'danger' : 'success'}"
                        onclick="togglePower('${server.name}', '${server.power_state}')">
                    ${server.power_state === 'on' ? 'Power Off' : 'Power On'}
                </button>
            </div>
        </td>
    `;
    
    return tr;
}

function togglePower(serverName, currentState) {
    const action = currentState === 'on' ? 'off' : 'on';
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

function handleAddServer() {
    const form = document.getElementById('addServerForm');
    const data = {
        name: form.querySelector('#serverName').value,
        ipmi_host: form.querySelector('#ipmiHost').value,
        ipmi_user: form.querySelector('#ipmiUser').value,
        ipmi_pass: form.querySelector('#ipmiPass').value
    };

    fetch('/api/servers/manage', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        const modal = bootstrap.Modal.getInstance(document.getElementById('addServerModal'));
        modal.hide();
        form.reset();
        loadServerList();
    })
    .catch(error => {
        console.error('Error adding server:', error);
        alert('Failed to add server');
    });
}