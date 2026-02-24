console.log("Testing fetch to 172.18.0.2:8000...");
fetch('http://172.18.0.2:8000/api/v1/health/')
    .then(r => {
        console.log('Status:', r.status);
        return r.text().then(t => console.log('Body length:', t.length));
    })
    .catch(e => {
        console.error('Fetch Error:', e);
        if (e.cause) console.error('Cause:', e.cause);
    });
