/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Включаем standalone сборку для Docker
  output: 'standalone',
  
  // Оптимизация изображений (если используются)
  images: {
    unoptimized: true
  },

  // Экспериментальные функции для уменьшения размера
  experimental: {
    // Отключаем optimizeCss - вызывает проблемы с critters в Docker
    // optimizeCss: true,
    // Улучшает производительность
    proxyTimeout: 120000,
  },

  // Webpack оптимизации
  webpack: (config, { isServer }) => {
    // Уменьшаем размер бандла
    if (!isServer) {
      config.resolve.fallback = {
        fs: false,
        net: false,
        tls: false,
      }
    }
    
    return config
  },
}

module.exports = nextConfig
