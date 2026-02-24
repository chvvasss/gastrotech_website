console.log("Testing fetch to backend...");
fetch('http://backend:8000/api/v1/health/')
    .then(r => {
        console.log('Status:', r.status);
        return r.text().then(t => console.log('Body:', t.substring(0, 100)));
    })
    .catch(e => {
        console.error('Fetch Error:', e);
        if (e.cause) console.error('Cause:', e.cause);
    });
