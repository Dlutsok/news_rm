import '@styles/globals.css'
import Head from 'next/head'
import { AuthProvider } from '@contexts/AuthContext'

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Head>
        <title>Rusmedical News AI</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />

        {/* Полное отключение индексации для всех страниц */}
        <meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />
        <meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />
        <meta name="bingbot" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />
        <meta name="yandexbot" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />

        {/* Дополнительная защита от индексации */}
        <meta name="referrer" content="no-referrer" />
        <meta name="format-detection" content="telephone=no" />
        <meta httpEquiv="X-Robots-Tag" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />

        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>
      <Component {...pageProps} />
    </AuthProvider>
  )
}