import localFont from 'next/font/local';

export const notoSerifThai = localFont({
  src: '../assets/fonts/NotoSerifThai-Variable.ttf',
  variable: '--font-editorial',
  display: 'swap',
});

export const ibmPlexSansThai = localFont({
  src: [
    { path: '../assets/fonts/IBMPlexSansThai-Regular.ttf', weight: '400' },
    { path: '../assets/fonts/IBMPlexSansThai-Medium.ttf', weight: '500' },
    { path: '../assets/fonts/IBMPlexSansThai-SemiBold.ttf', weight: '600' },
  ],
  variable: '--font-ui',
  display: 'swap',
});

export const jetBrainsMono = localFont({
  src: '../assets/fonts/JetBrainsMono-Variable.ttf',
  variable: '--font-technical',
  display: 'swap',
});
