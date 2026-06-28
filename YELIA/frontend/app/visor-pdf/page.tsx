import { Suspense } from 'react';
import VisorPdfClient from './VisorPdfClient';

export const dynamic = 'force-dynamic';

export default function VisorPdfPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/base/yelia-theme-tokens.css" />
      <Suspense fallback={<div style={{ background: '#121212', color: '#fff', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>Cargando visor...</div>}>
        <VisorPdfClient />
      </Suspense>
    </>
  );
}
