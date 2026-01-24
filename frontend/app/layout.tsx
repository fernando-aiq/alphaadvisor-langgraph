import type { Metadata } from 'next'
import './globals.css'
import { ProfileProvider } from './contexts/ProfileContext'
import Layout from './components/Layout'
import { NuqsAdapter } from 'nuqs/adapters/next/app'

export const metadata: Metadata = {
  title: 'AlphaAdvisor',
  description: 'Seu assistente inteligente para investimentos',
  icons: {
    icon: '/icon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body>
        <NuqsAdapter>
          <ProfileProvider>
            <Layout>{children}</Layout>
          </ProfileProvider>
        </NuqsAdapter>
      </body>
    </html>
  )
}

