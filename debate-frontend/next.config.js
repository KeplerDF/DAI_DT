/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production';

const nextConfig = {
  // Only use basePath & static export when building for GitHub Pages production
  ...(isProd && {
    output: 'export',
    basePath: '/DAI_DT',
  }),
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;