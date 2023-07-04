import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
    return (
        <Html lang="en">
            <Head>
                <meta charSet="utf-8" />
                <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
                <meta name="description" content="LIA" />
                <meta name="keywords" content="LIA" />

                {/* <!-- Pinned Sites  --> */}
                <meta name='application-name' content='LIA' />
                <meta name="msapplication-tooltip" content="Tooltip Text" />
                <meta name="msapplication-starturl" content="/" />

                {/* <!-- iOS --> */}
                <meta name="apple-mobile-web-app-title" content="LIA" />
                <meta name='apple-mobile-web-app-capable' content='yes' />
                <meta name="apple-touch-fullscreen" content="yes" /> 
                <meta name='apple-mobile-web-app-status-bar-style' content='black' />
                <meta name='apple-mobile-web-app-title' content='LIA' />
                
                {/* <!-- Android  --> */}
                <meta name='theme-color' content='#0f172a' />
                <meta name='format-detection' content='telephone=no' />
                <meta name='mobile-web-app-capable' content='yes' />
                
                {/* <!-- Windows  --> */}
                <meta name="msapplication-navbutton-color" content="#0f172a" />
                <meta name="msapplication-TileColor" content="#0f172a" />
                <meta name="msapplication-TileImage" content="ms-icon-144x144.png" />
                <meta name="msapplication-config" content="browserconfig.xml" />
                <meta name="msapplication-tap-highlight" content="no" />
                
                {/* IOS */}
                <link rel='apple-touch-icon' href='/assets/icons/ios/180.png' />
                <link rel='apple-touch-icon' sizes='120x120' href='/assets/icons/ios/120.png' />
                <link rel='apple-touch-icon' sizes='152x152' href='/assets/icons/ios/152.png' />
                <link rel='apple-touch-icon' sizes='167x167' href='/assets/icons/ios/167.png' />
                <link rel='apple-touch-icon' sizes='180x180' href='/assets/icons/ios/180.png' />

                <link rel="apple-touch-startup-image" href="/images/splash/launch-640x1136.jpeg" />
                
                
                <link rel='icon' type='image/png' sizes='32x32' href='/assets/icons/favicon-32x32.png' />
                <link rel='icon' type='image/png' sizes='16x16' href='/assets/icons/favicon-16x16.png' />
                
                <link rel='manifest' href='/manifest.json' />
                <link rel='shortcut icon' href='/favicon.ico' />				
                
                {/* FONTS */}
                {/* <link rel="preconnect" href="https://fonts.googleapis.com"></link>
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin=""></link>
                <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300&family=Raleway:wght@300&display=swap" rel="stylesheet"></link>

                <link rel="preconnect" href="https://fonts.googleapis.com"></link>
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin=""></link>
                <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300&display=swap" rel="stylesheet"></link> */}
            </Head>
            <body>
                <Main />
                <NextScript />
            </body>
        </Html>
    );
}
