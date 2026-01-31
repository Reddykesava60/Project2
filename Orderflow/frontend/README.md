# Frontend (Next.js)

This directory contains the Next.js frontend for OrderFlow, using the App Router for modern, scalable web applications.

---

## Tech Stack
- Next.js (App Router)
- React
- Tailwind CSS
- TypeScript

---

## Installation

1. Install dependencies:
   ```sh
   npm install
   # or
   pnpm install
   ```

2. Copy the environment variable template and fill in required values:
   ```sh
   cp .env.local.example .env.local
   ```

---

## Environment Variables

Create a `.env.local` file in the `frontend/` directory. Example:

```
# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Razorpay Keys
NEXT_PUBLIC_RAZORPAY_KEY_ID=your_razorpay_key_id
NEXT_PUBLIC_RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Stripe Keys (if used)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your_stripe_key
```

---

## Running Locally

```sh
npm run dev
# or
pnpm dev
```

- App will be available at http://localhost:3000

---

## API Connection Setup
- The frontend connects to the backend API via `NEXT_PUBLIC_API_URL`.
- Ensure the backend is running and accessible at the specified URL.

---

## Production Build

1. Build the app:
   ```sh
   npm run build
   # or
   pnpm build
   ```
2. Start the production server:
   ```sh
   npm start
   # or
   pnpm start
   ```

---

## Deployment (Vercel)
- Connect the `frontend` directory to Vercel.
- Set environment variables in the Vercel dashboard.
- Vercel will handle builds and deployments automatically.

---

## Additional Notes
- Do not commit secrets to the repository.
- For custom domains, configure in Vercel dashboard.
