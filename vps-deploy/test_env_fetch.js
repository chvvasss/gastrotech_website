const djangoUrl = process.env.DJANGO_URL;
console.log("Reading DJANGO_URL:", djangoUrl);

if (!djangoUrl) {
    console.error("DJANGO_URL is missing!");
    process.exit(1);
}

const target = djangoUrl + '/api/v1/health/';
console.log("Fetching:", target);

fetch(target)
    .then(r => {
        console.log('Status:', r.status);
        return r.text().then(t => console.log('Body:', t.substring(0, 100)));
    })
    .catch(e => {
        console.error('Fetch Error:', e);
        if (e.cause) console.error('Cause:', e.cause);
    });
