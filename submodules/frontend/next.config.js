/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.APP_ENV === "production"
        ? "https://api.mysuperagent.io"
        : process.env.APP_ENV === "staging"
        ? "https://api-staging.mysuperagent.io"
        : "http://localhost:8888",
  },
  output: "export",
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
