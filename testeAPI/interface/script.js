async function updateTable() {
    try {
        const response = await fetch('http://localhost:5000/get_status');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();

        const table = document.querySelector('table');
        table.innerHTML = `
            <tr>
                <th>Estado</th>
                <th>EDV</th>
                <th>Status</th>
            </tr>
        `;

        data.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>Estado</td>
                <td>${row.edv}</td>
                <td class="status-${row.status.toLowerCase()}">${row.status}</td>
            `;
            table.appendChild(tr);
        });
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

updateTable();
