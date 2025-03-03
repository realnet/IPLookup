function showIpLookup() {
  const content = document.getElementById('main-content');
  content.innerHTML = `
    <h2>IP查询</h2>
    <form id="ip-lookup-form">
      <label for="ip">Enter IP address or range:</label>
      <input type="text" id="ip" name="ip" required>
      <button type="submit">Lookup</button>
    </form>
    <div id="ip-result"></div>
  `;
  const ipLookupForm = document.getElementById('ip-lookup-form');
  const ipResultDiv = document.getElementById('ip-result');

  ipLookupForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const ipValue = document.getElementById('ip').value;

    fetch(`/api/ip-lookup/?ip=${ipValue}`)
      .then(response => {
        if(!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        return response.json();
      })
      .then(data => {
        if(data.error) {
          ipResultDiv.innerHTML = `<p class="error">Error: ${data.error}</p>`;
        } else {
          // 省略: 处理 type === 'EC2' / 'Subnet' 等场景
          // ...
          // ipResultDiv.innerHTML = ...
        }
      })
      .catch(err => {
        ipResultDiv.innerHTML = `<p class="error">Fetch error: ${err.message}</p>`;
      });
  });
}
