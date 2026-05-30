# Frontend

Next.js product shell for the Muni Lost Time Atlas public MVP.

This bundle reads the historical/static API directly. By default it targets
`http://127.0.0.1:8000`; override with `API_BASE_URL` or
`NEXT_PUBLIC_API_BASE_URL` when needed.

Production maintenance mode:
- `MAINTENANCE_MODE=true` forces the site into the maintenance screen
- `MAINTENANCE_FLAG_PATH` lets the publisher toggle maintenance through a shared flag file

Primary commands:

- `npm install`
- `npm run dev`
- `npm test`
- `npm run smoke`
- `npm run build`
