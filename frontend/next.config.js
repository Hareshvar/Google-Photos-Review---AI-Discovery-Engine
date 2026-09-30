/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: '/',
        destination: '/overview',
        permanent: false,
      },
    ];
  },
};

module.exports = nextConfig;
