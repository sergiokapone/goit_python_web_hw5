console.log("Hello world!");

const ws = new WebSocket("ws://localhost:8080");

formChat.addEventListener("submit", (e) => {
  e.preventDefault();
  ws.send(textField.value);
  textField.value = null;
});

ws.onopen = (e) => {
  console.log("Hello WebSocket!");
};

ws.onmessage = (e) => {
  console.log(e.data);
  let response = e.data;
  response = response.replace(/'/g, '"');

  try {
    const jsonData = JSON.parse(response);

    for (const dateRate of jsonData) {
      for (const date in dateRate) {
        const rates = dateRate[date];
        for (const currency in rates) {
          const { sale, purchase } = rates[currency];
          console.log(
            `Date: ${date}, Currency: ${currency}, Sale: ${sale}, Purchase: ${purchase}`
          );
        }
      }
    }

    let tableHTML = `
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Currency</th>
            <th>Sale</th>
            <th>Purchase</th>
          </tr>
        </thead>
        <tbody>
    `;

    let previousDate = null;
    let rowspan = 0;

    for (const dateRate of jsonData) {
      for (const date in dateRate) {
        const rates = dateRate[date];
        const currencies = Object.keys(rates);

        const rowCount = currencies.length;

        if (date === previousDate) {
          rowspan += rowCount;
        } else {
          if (previousDate !== null) {
            tableHTML += "</tr>";
          }
          rowspan = rowCount;
        }

        tableHTML += `
          <tr>
            ${
              rowspan === rowCount
                ? `<td rowspan="${rowspan}">${date}</td>`
                : ""
            }
            <td>${currencies.shift()}</td>
            <td>${rates[currencies[0]].sale}</td>
            <td>${rates[currencies[0]].purchase}</td>
          </tr>
        `;

        for (const currency of currencies) {
          tableHTML += `
            <tr>
              <td>${currency}</td>
              <td>${rates[currency].sale}</td>
              <td>${rates[currency].purchase}</td>
            </tr>
          `;
        }

        previousDate = date;
      }
    }

    tableHTML += `
        </tbody>
      </table>
    `;

    const container = document.createElement("div");
    container.innerHTML = tableHTML;
    document.body.appendChild(container);
  } catch (error) {
    const elMsg = document.createElement("div");
    elMsg.textContent = response;
    elMsg.className = "subscribe";
    document.body.appendChild(elMsg);
  }
};
