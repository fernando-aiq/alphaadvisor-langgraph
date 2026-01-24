/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000',
  },
  async rewrites() {
    // Usar variável de ambiente API_URL ou padrão
    const apiUrl = process.env.API_URL || 'http://localhost:8000'
    
    // Log para debug (apenas no build, não em runtime)
    if (process.env.NODE_ENV === 'development') {
      console.log('[Next.js Config] API_URL configurada:', apiUrl)
    }
    
    return [
      // Redirecionar /info para /api/info (para compatibilidade com LangSmith Studio)
      {
        source: '/info',
        destination: '/api/info',
      },
    ];
  },
};

module.exports = nextConfig;


