# Frontend

React + Vite frontend for the E-Commerce Management System.

## Setup

1. Copy `.env.example` to `.env`
2. Set `VITE_API_BASE_URL` to the FastAPI backend URL
3. Install dependencies with `npm install`
4. Start the app with `npm run dev`

## Available Pages

- Home
- Login and registration
- Product listing and product details
- Cart and checkout
- Orders
- Reviews
- Admin dashboard, products, categories, suppliers, and orders

## Notes

- Authentication is stored with JWT in local storage.
- Axios automatically attaches the token to backend requests.
- The UI is responsive and uses reusable components for forms, cards, and states.
