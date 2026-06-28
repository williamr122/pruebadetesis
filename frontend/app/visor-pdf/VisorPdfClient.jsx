'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { api } from '../_components/api';

export default function VisorPdfClient() {
  const searchParams = useSearchParams();
  const unidad = Number(searchParams.get('unidad') || 1);
  const tipo = searchParams.get('tipo') || 'contenido'; // 'contenido' o 'presentacion'

  const [mounted, setMounted] = useState(false);
  const [reachedEnd, setReachedEnd] = useState(false);
  const LIMIT_TIME = 3; // 3 seconds timer for tests
  const [timeLeft, setTimeLeft] = useState(LIMIT_TIME);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [version, setVersion] = useState('');
  const triggeringRef = useRef(false);

  const pdfUrl = tipo === 'presentacion'
    ? `/resources/RECURSOS_YELIA4AP/u${unidad}/presentation.pdf`
    : `/resources/RECURSOS_YELIA4AP/u${unidad}/pdf.pdf`;

  const stepName = tipo === 'presentacion' ? 'presentation' : 'content';
  const label = tipo === 'presentacion' ? 'Diapositivas' : 'Lectura de Contenido';

  useEffect(() => {
    setMounted(true);
    setVersion(Date.now().toString());
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const handleMessage = (event) => {
      // Verify origin strictly matching local origin
      if (event.origin !== window.location.origin) return;
      if (event.data) {
        if (event.data.type === 'pdf-page-changed') {
          const decodedUrl = decodeURIComponent(event.data.url).split('?')[0];
          const decodedTarget = decodeURIComponent(pdfUrl).split('?')[0];
          if (decodedUrl.includes(decodedTarget) || decodedTarget.includes(decodedUrl)) {
            setReachedEnd(event.data.page === event.data.total);
          }
        } else if (event.data.type === 'pdf-completed') {
          const decodedUrl = decodeURIComponent(event.data.url).split('?')[0];
          const decodedTarget = decodeURIComponent(pdfUrl).split('?')[0];
          if (decodedUrl.includes(decodedTarget) || decodedTarget.includes(decodedUrl)) {
            setReachedEnd(true);
          }
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [mounted, pdfUrl]);

  useEffect(() => {
    if (!reachedEnd || timeLeft <= 0 || completed) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          triggerCompletion();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [reachedEnd, timeLeft, completed]);

  const triggerCompletion = async () => {
    if (triggeringRef.current || completed) return;
    triggeringRef.current = true;
    setSaving(true);
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem(`yelia_u${unidad}_${stepName}_done`, 'true');
      }
      await api.post(`/api/learning-route/unit/${unidad}/step`, { step: stepName, completed: true });
      setCompleted(true);
      setTimeout(() => {
        try {
          if (window.opener) {
            window.close();
          } else {
            window.location.href = `/leccion?unidad=${unidad}&modo=${tipo === 'presentacion' ? 'presentacion' : 'contenido'}`;
          }
        } catch {
          window.location.href = `/leccion?unidad=${unidad}&modo=${tipo === 'presentacion' ? 'presentacion' : 'contenido'}`;
        }
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el progreso. Reintentando...');
      setSaving(false);
      triggeringRef.current = false;
      // Auto-retry in 5 seconds
      setTimeout(triggerCompletion, 5000);
    }
  };

  if (!mounted) {
    return <div className="visor-loading">Cargando visor...</div>;
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progressPercent = reachedEnd ? ((LIMIT_TIME - timeLeft) / LIMIT_TIME) * 100 : 0;

  return (
    <main className="visor-shell">
      <style dangerouslySetInnerHTML={{ __html: `
        .visor-shell {
          display: flex;
          flex-direction: column;
          height: 100vh;
          background: #121212;
          color: #fff;
          font-family: var(--yelia-font-sans, system-ui, -apple-system, sans-serif);
        }
        .visor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 6px 16px;
          background: rgba(30, 30, 30, 0.85);
          backdrop-filter: blur(12px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          z-index: 10;
        }
        .visor-title-section {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .visor-title-section h1 {
          font-size: 0.95rem;
          margin: 0;
          font-weight: 700;
          color: #fff;
        }
        .visor-title-section p {
          font-size: 0.75rem;
          margin: 0;
          opacity: 0.5;
        }
        .visor-btn-back {
          padding: 4px 10px;
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 4px;
          color: #fff;
          font-size: 0.8rem;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
          display: flex;
          align-items: center;
          gap: 6px;
          text-decoration: none;
        }
        .visor-btn-back:hover {
          background: rgba(255, 255, 255, 0.15);
        }
        .visor-body {
          flex: 1;
          position: relative;
        }
        .visor-iframe {
          width: 100%;
          height: 100%;
          border: none;
          background: #1a1a1a;
        }
        .visor-timer-banner {
          position: absolute;
          bottom: 24px;
          left: 50%;
          transform: translateX(-50%);
          width: 90%;
          max-width: 600px;
          background: rgba(20, 20, 20, 0.9);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(13, 110, 253, 0.4);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
          border-radius: 12px;
          padding: 16px 20px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          z-index: 20;
          animation: slideUp 0.3s ease-out;
        }
        @keyframes slideUp {
          from { transform: translate(-50%, 50px); opacity: 0; }
          to { transform: translate(-50%, 0); opacity: 1; }
        }
        .visor-timer-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .visor-timer-text {
          font-size: 0.9rem;
          font-weight: 500;
          color: #fff;
        }
        .visor-timer-clock {
          font-size: 1.2rem;
          font-weight: 800;
          color: #0d6efd;
          text-shadow: 0 0 10px rgba(13, 110, 253, 0.3);
        }
        .visor-progress-bg {
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          overflow: hidden;
        }
        .visor-progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #0d6efd 0%, #0dcaf0 100%);
          border-radius: 3px;
          transition: width 1s linear;
        }
        .visor-success-banner {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(18, 18, 18, 0.95);
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          gap: 16px;
          z-index: 30;
        }
        .visor-success-icon {
          font-size: 4rem;
          color: #198754;
          animation: scaleUp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        @keyframes scaleUp {
          from { transform: scale(0.5); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
        .visor-success-banner h2 {
          font-size: 1.5rem;
          margin: 0;
          font-weight: 700;
        }
        .visor-success-banner p {
          font-size: 0.95rem;
          opacity: 0.7;
          margin: 0;
        }
        .visor-loading {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background: #121212;
          color: #fff;
          font-size: 1.2rem;
        }
      ` }} />

      <header className="visor-header">
        <div className="visor-title-section">
          <h1>Unidad {unidad}: {label}</h1>
          <p>YELIA Ruta de Aprendizaje Avanzada</p>
        </div>
        <button className="visor-btn-back" type="button" onClick={() => window.location.href = `/leccion?unidad=${unidad}`}>
          <i className="bi bi-arrow-left" /> Volver a Lección
        </button>
      </header>

      <section className="visor-body">
        <iframe
          className="visor-iframe"
          src={`/pdfviewer.html?file=${encodeURIComponent(pdfUrl + (version ? '?v=' + version : ''))}`}
          title="Visor de PDF"
        />

        {reachedEnd && !completed && (
          <div className="visor-timer-banner">
            <div className="visor-timer-row">
              <span className="visor-timer-text">
                <i className="bi bi-info-circle-fill" style={{ color: '#0d6efd', marginRight: '6px' }} />
                Has llegado al final. Analiza esta página durante 3 segundos para registrar tu avance.
              </span>
              <strong className="visor-timer-clock">{formatTime(timeLeft)}</strong>
            </div>
            <div className="visor-progress-bg">
              <div className="visor-progress-fill" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>
        )}

        {completed && (
          <div className="visor-success-banner">
            <i className="bi bi-check-circle-fill visor-success-icon" />
            <h2>Lectura Completada</h2>
            <p>Tu avance ha sido guardado exitosamente. Redirigiendo...</p>
          </div>
        )}

        {error && (
          <div style={{ position: 'absolute', top: '24px', left: '50%', transform: 'translateX(-50%)', background: '#dc3545', color: '#fff', padding: '12px 24px', borderRadius: '8px', zIndex: 40, boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
            <i className="bi bi-exclamation-triangle-fill" style={{ marginRight: '8px' }} />
            {error}
          </div>
        )}
      </section>
    </main>
  );
}
