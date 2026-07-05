# Frontend

React + Vite frontend for the E-Commerce Management System.

## Setup

1. Copy `.env.example` to `.env`
2. Set `VITE_API_BASE_URL` to the FastAPI backend URL
3. Install dependencies with `npm install`
4. Start the app with `npm run dev`

If you are using Supabase Auth, populate `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` as well. The React app now restores sessions from Supabase and forwards the Supabase access token to the backend API.

## Available Pages

- Home
- Login and registration
- Product listing and product details
- Cart and checkout
- Orders
- Reviews
- Admin dashboard, products, categories, suppliers, and orders

## Notes

- Authentication uses Supabase sessions, with the access token stored locally for backend requests.
- Axios automatically attaches the Supabase access token to backend requests.
- The UI is responsive and uses reusable components for forms, cards, and states.
