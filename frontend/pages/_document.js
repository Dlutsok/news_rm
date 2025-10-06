import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="ru">
      <Head>
        {/* Полное отключение индексации */}
        <meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />
        <meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />
        <meta name="bingbot" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />
        <meta name="yandexbot" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />

        {/* Дополнительные директивы */}
        <meta name="referrer" content="no-referrer" />
        <meta name="format-detection" content="telephone=no" />

        {/* X-Robots-Tag для дополнительной защиты */}
        <meta httpEquiv="X-Robots-Tag" content="noindex, nofollow, noarchive, nosnippet, noimageindex, nocache" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}