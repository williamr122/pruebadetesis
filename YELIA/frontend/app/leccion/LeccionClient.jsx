'use client';

import { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { api } from '../_components/api';
import Confetti from '../_components/Confetti';

const FALLBACK_UNITS = [
  { id: 1, title: 'Introduccion a la Programacion Orientada a Objetos', subtitle: 'Clases, objetos, atributos, metodos y encapsulamiento.', topics: ['Introduccion a POO', 'Clases y Objetos', 'Atributos y metodos', 'Encapsulamiento'] },
  { id: 2, title: 'Lenguaje de Modelado Unificado', subtitle: 'Herencia, polimorfismo, clases abstractas e interfaces.', topics: ['Herencia', 'Polimorfismo', 'Sobrecarga y sobrescritura', 'Interfaces'] },
  { id: 3, title: 'Aplicacion de la Programacion Orientada a Objetos', subtitle: 'UML, patrones de diseno y MVC.', topics: ['Diagramas UML', 'Casos de uso', 'Secuencia y actividad', 'MVC'] },
  { id: 4, title: 'Acceso a Archivos y Base de Datos', subtitle: 'Persistencia, ORM, integracion y pruebas.', topics: ['Acceso a archivos', 'Bases de Datos y ORM', 'Integracion POO/MVC/Datos', 'Pruebas'] },
];

function unitFromLocation() {
  if (typeof window === 'undefined') return 1;
  const params = new URLSearchParams(window.location.search);
  return Math.max(1, Math.min(4, Number(params.get('unidad') || params.get('unit') || 1)));
}

function modeFromLocation() {
  if (typeof window === 'undefined') return 'content';
  const params = new URLSearchParams(window.location.search);
  const rawMode = params.get('modo') || params.get('mode') || 'content';
  const mode = rawMode.toLowerCase();
  if (mode === 'contenido' || mode === 'content') return 'content';
  if (mode === 'presentacion' || mode === 'presentation') return 'presentation';
  if (mode === 'videos') return 'videos';
  if (mode === 'taller' || mode === 'workshop') return 'workshop';
  if (mode === 'leccion' || mode === 'lesson') return 'lesson';
  if (mode === 'examen' || mode === 'exam' || mode === 'quiz') return 'exam';
  return mode;
}

function publicQuestions(questions = []) {
  return questions.map(({ answer: _answer, source: _source, ...item }) => item);
}

function scoreLocalQuiz(questions, answers) {
  let score = 0;
  const details = questions.map((question) => {
    const selected = Number(answers[question.id]);
    const correct = selected === Number(question.answer);
    if (correct) score += 1;
    return { id: question.id, topic: question.topic, correct, selected, answer: question.answer };
  });
  const total = questions.length;
  const percent = total ? Math.round((score / total) * 100) : 0;
  return { score, total, percent, details };
}

function hintFor(unit, text) {
  const clean = String(text || '').toLowerCase();
  if (!clean.trim()) return 'Escribe tu duda y te doy una pista sin resolver la respuesta por ti.';
  if (clean.includes('respuesta') || clean.includes('examen') || clean.includes('quiz')) {
    return 'No puedo darte la respuesta directa. Te puedo explicar el concepto clave y darte una pista para razonar la opcion.';
  }
  if (clean.includes('ejemplo')) {
    return `Pista: toma un caso pequeno de ${unit.topics?.[0] || unit.title}. Primero separa datos, acciones and responsabilidad.`;
  }
  if (clean.includes('no entiendo') || clean.includes('duda') || clean.includes('explica')) {
    return `Pista de ${unit.title}: identifica que problema resuelve el concepto y luego comparalo con un ejemplo simple.`;
  }
  return `Conecta tu duda con uno de estos temas: ${(unit.topics || []).join(', ')}.`;
}

export default function LeccionClient() {
  const [mounted, setMounted] = useState(false);
  const [lastAutoOpened, setLastAutoOpened] = useState('');
  const [showConfetti, setShowConfetti] = useState(false);
  const [unitId, setUnitId] = useState(1);
  const [video1Played, setVideo1Played] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setVideo1Played(localStorage.getItem(`yelia_u${unitId}_video1_played`) === 'true');
    } else {
      setVideo1Played(false);
    }
  }, [unitId]);
  const [units, setUnits] = useState(FALLBACK_UNITS);
  const [unitContent, setUnitContent] = useState(null);
  const [activePanel, setActivePanel] = useState('content');
  const [lessonAnswers, setLessonAnswers] = useState({});
  const [lessonResult, setLessonResult] = useState(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const handleFocus = () => {
      api.get('/api/learning-route')
        .then((data) => {
          if (data.route) setRoute(data.route);
        })
        .catch(() => {});
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [mounted]);

  const [workshopAnswers, setWorkshopAnswers] = useState({});
  const [workshopResult, setWorkshopResult] = useState(null);
  const [route, setRoute] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [finalQuiz, setFinalQuiz] = useState(null);
  const [finalAnswers, setFinalAnswers] = useState({});
  const [finalResult, setFinalResult] = useState(null);
  const [assistantText, setAssistantText] = useState('');
  const [assistantMessages, setAssistantMessages] = useState([
    { role: 'assistant', text: 'Estoy aqui para darte pistas y aclarar conceptos. Durante evaluaciones no doy respuestas directas.' },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = 'lesson-page ui desktop-pro';
    setUnitId(unitFromLocation());
    setActivePanel(modeFromLocation());
    return () => {
      document.body.className = previous;
    };
  }, []);

  useEffect(() => {
    api.get('/api/learning-route')
      .then((data) => {
        if (Array.isArray(data.units) && data.units.length) setUnits(data.units);
        if (data.route) setRoute(data.route);
      })
      .catch(() => {});
  }, []);

  const unit = useMemo(() => units.find((item) => Number(item.id) === Number(unitId)) || FALLBACK_UNITS[0], [units, unitId]);
  const resources = unitContent?.resources || unit.resources || [];
  const contentResource = resources.find((item) => item.type === 'unit_content') || resources.find((item) => item.type === 'pdf') || resources[0];
  const workshopResource = resources.find((item) => item.type === 'workshop');
  const lessonQuestions = unitContent?.lesson_questions || [];
  const workshopQuestions = unitContent?.workshop_questions || [];

  const unitState = useMemo(() => {
    return route?.units?.[String(unitId)] || {};
  }, [route, unitId]);

  const isUnitApproved = useMemo(() => {
    const state = units.find((u) => Number(u.id) === Number(unitId));
    return state?.status === 'done' || unitState?.status === 'done';
  }, [units, unitId, unitState]);

  const completedSteps = useMemo(() => {
    const hasRoute = !!route;
    return {
      content: hasRoute ? !!unitState.content_done : false,
      presentation: hasRoute ? !!unitState.presentation_done : false,
      videos: hasRoute ? !!unitState.videos_done : false,
      workshop: hasRoute ? !!unitState.workshop_done : false,
      lesson: hasRoute ? !!unitState.lesson_done : false,
    };
  }, [route, unitState, unitId]);

  // Clean up stale localStorage flags that do not match backend route data
  useEffect(() => {
    if (!route || typeof window === 'undefined') return;
    for (let u = 1; u <= 4; u++) {
      const uState = route.units?.[String(u)] || {};
      if (!uState.content_done) {
        localStorage.removeItem(`yelia_u${u}_content_done`);
      }
      if (!uState.presentation_done) {
        localStorage.removeItem(`yelia_u${u}_presentation_done`);
      }
      if (!uState.videos_done) {
        localStorage.removeItem(`yelia_u${u}_videos_done`);
        localStorage.removeItem(`yelia_u${u}_video1_played`);
      }
      if (!uState.workshop_done) {
        localStorage.removeItem(`yelia_u${u}_workshop_done`);
      }
      if (!uState.lesson_done) {
        localStorage.removeItem(`yelia_u${u}_lesson_done`);
      }
    }
  }, [route]);

  const isStepUnlocked = (step) => {
    if (isUnitApproved) return true;
    switch (step) {
      case 'content':
        return true;
      case 'presentation':
        return completedSteps.content;
      case 'videos':
        return completedSteps.content && completedSteps.presentation;
      case 'workshop':
        return completedSteps.content && completedSteps.presentation && completedSteps.videos;
      case 'lesson':
        return completedSteps.content && completedSteps.presentation && completedSteps.videos && (completedSteps.workshop || !!workshopResult);
      case 'exam':
        return completedSteps.content && completedSteps.presentation && completedSteps.videos && (completedSteps.workshop || !!workshopResult) && (completedSteps.lesson || !!lessonResult);
      default:
        return false;
    }
  };

  useEffect(() => {
    if (!mounted || !route) return;
    if (activePanel !== 'content' && activePanel !== 'final' && !isStepUnlocked(activePanel)) {
      setActivePanel('content');
      if (typeof window !== 'undefined') {
        window.history.replaceState(null, '', `/leccion?unidad=${unitId}`);
      }
    }
  }, [activePanel, completedSteps, isUnitApproved, unitId, mounted, route]);

  useEffect(() => {
    if (!mounted || !route) return;
    const key = `${unitId}-${activePanel}`;
    if (lastAutoOpened === key) return;

    if (activePanel === 'content' && !completedSteps.content) {
      setLastAutoOpened(key);
      try {
        window.open(`/visor-pdf?unidad=${unitId}&tipo=contenido`, '_blank');
      } catch (e) {
        console.warn('Popup blocked:', e);
      }
    } else if (activePanel === 'presentation' && !completedSteps.presentation) {
      setLastAutoOpened(key);
      try {
        window.open(`/visor-pdf?unidad=${unitId}&tipo=presentacion`, '_blank');
      } catch (e) {
        console.warn('Popup blocked:', e);
      }
    }
  }, [mounted, route, activePanel, unitId, completedSteps.content, completedSteps.presentation, lastAutoOpened]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError('');
    setUnitContent(null);
    api.get(`/api/learning-route/unit/${unitId}/content`)
      .then((data) => {
        if (!alive) return;
        setUnitContent(data);
        if (data.unit) {
          setUnits((current) => current.map((item) => (Number(item.id) === Number(unitId) ? { ...item, ...data.unit } : item)));
        }
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : 'No se pudo cargar el contenido oficial de la unidad.');
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [unitId]);

  useEffect(() => {
    if (activePanel === 'exam') openQuiz();
    if (activePanel === 'final') openFinalQuiz();
  }, [activePanel, unitId]);



  function changeUnit(nextId) {
    setUnitId(nextId);
    setActivePanel('content');
    setLessonAnswers({});
    setLessonResult(null);
    setWorkshopAnswers({});
    setWorkshopResult(null);
    setQuiz(null);
    setAnswers({});
    setResult(null);
    setFinalQuiz(null);
    setFinalAnswers({});
    setFinalResult(null);
    setVideo1Played(false);
    setShowConfetti(false);
    setError('');
    window.history.replaceState(null, '', `/leccion?unidad=${nextId}`);

    const hasRoute = !!route;
    const nextUnitState = route?.units?.[String(nextId)] || {};
    const nextContentDone = hasRoute ? !!nextUnitState.content_done : false;
    if (!nextContentDone) {
      setLastAutoOpened(`${nextId}-content`);
      try {
        window.open(`/visor-pdf?unidad=${nextId}&tipo=contenido`, '_blank');
      } catch (e) {
        console.warn('Popup blocked:', e);
      }
    }
  }

  function switchPanel(panel, isManualClick = false) {
    if (panel !== 'content' && panel !== 'final') {
      if (!isStepUnlocked(panel)) {
        setError('Primero completa el paso anterior para continuar.');
        return;
      }
    }
    setError('');
    setActivePanel(panel);
    setShowConfetti(false);
    if (panel !== 'workshop') {
      setWorkshopAnswers({});
      setWorkshopResult(null);
    }
    if (panel !== 'exam') {
      setQuiz(null);
      setAnswers({});
      setResult(null);
    }
    if (panel !== 'final') {
      setFinalQuiz(null);
      setFinalAnswers({});
      setFinalResult(null);
    }
    window.history.replaceState(null, '', `/leccion?unidad=${unit.id}${panel === 'content' ? '' : `&modo=${panel}`}`);

    if (isManualClick) {
      const key = `${unitId}-${panel}`;
      setLastAutoOpened(key);
      if (panel === 'content') {
        window.open(`/visor-pdf?unidad=${unitId}&tipo=contenido`, '_blank');
      } else if (panel === 'presentation') {
        window.open(`/visor-pdf?unidad=${unitId}&tipo=presentacion`, '_blank');
      }
    }
  }

  const handlePlayVideo1 = () => {
    setVideo1Played(true);
    if (typeof window !== 'undefined') {
      localStorage.setItem(`yelia_u${unitId}_video1_played`, 'true');
    }
  };

  const handlePlayVideo2 = async () => {
    if (!video1Played) {
      setError('Debes reproducir primero el Video 1 antes de poder reproducir el Video 2.');
      return;
    }
    setError('');
    if (completedSteps.videos) return;
    const localKey = `yelia_u${unitId}_videos_done`;
    if (typeof window !== 'undefined') {
      localStorage.setItem(localKey, 'true');
    }
    try {
      const data = await api.post(`/api/learning-route/unit/${unitId}/step`, { step: 'videos', completed: true });
      if (data.route) setRoute(data.route);
    } catch (err) {
      console.error('Error al registrar reproducción de video:', err);
    }
  };

  async function submitWorkshopCheck() {
    if (!workshopQuestions.length) return;
    if (Object.keys(workshopAnswers).length < workshopQuestions.length) {
      setError('Responde todas las preguntas del taller antes de finalizar.');
      return;
    }
    setError('');
    const scoreResult = scoreLocalQuiz(workshopQuestions, workshopAnswers);
    setWorkshopResult(scoreResult);
    
    const localKey = `yelia_u${unitId}_workshop_done`;
    if (typeof window !== 'undefined') {
      localStorage.setItem(localKey, 'true');
    }

    try {
      const data = await api.post(`/api/learning-route/unit/${unitId}/step`, { step: 'workshop', completed: true });
      if (data.route) setRoute(data.route);
      setAssistantMessages((items) => [
        ...items,
        { role: 'assistant', text: `Taller finalizado con ${scoreResult.percent}%. ¡Sigue así!` }
      ]);
    } catch (err) {
      console.error('Error al registrar la practica:', err);
    }
  }

  function submitLessonCheck() {
    if (!lessonQuestions.length) return;
    if (Object.keys(lessonAnswers).length < lessonQuestions.length) {
      setError('Responde todas las preguntas de la leccion antes de finalizar.');
      return;
    }
    setError('');
    const scoreResult = scoreLocalQuiz(lessonQuestions, lessonAnswers);
    setLessonResult(scoreResult);
    if (scoreResult.percent === 100) {
      setShowConfetti(true);
    }

    const localKey = `yelia_u${unitId}_lesson_done`;
    if (typeof window !== 'undefined') {
      localStorage.setItem(localKey, 'true');
    }

    api.post(`/api/learning-route/unit/${unitId}/step`, { step: 'lesson', completed: true })
      .then((data) => {
        if (data.route) setRoute(data.route);
      })
      .catch((err) => console.error(err));
  }

  async function openQuiz() {
    setError('');
    setResult(null);
    setAnswers({});
    try {
      const data = await api.get(`/api/learning-route/unit/${unit.id}/quiz`);
      setQuiz(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo abrir el examen de unidad.');
    }
  }

  async function submitQuiz() {
    if (!quiz?.questions?.length) return;
    if (Object.keys(answers).length < quiz.questions.length) {
      setError('Responde todas las preguntas antes de finalizar.');
      return;
    }
    setError('');
    try {
      const data = await api.post(`/api/learning-route/unit/${unit.id}/quiz`, { answers });
      setResult(data);
      setQuiz(null);
      if (data.route) setRoute(data.route);
      if (data.result?.percent === 100) {
        setShowConfetti(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo calificar el examen.');
    }
  }

  async function openFinalQuiz() {
    setError('');
    setQuiz(null);
    setAnswers({});
    setResult(null);
    setFinalResult(null);
    setFinalAnswers({});
    try {
      const data = await api.get('/api/learning-route/final-quiz');
      setFinalQuiz(data);
      window.history.replaceState(null, '', '/leccion?modo=final');
    } catch (err) {
      setFinalQuiz(null);
      setError(err instanceof Error ? err.message : 'Completa las 4 unidades antes de abrir la evaluacion final.');
    }
  }

  async function submitFinalQuiz() {
    if (!finalQuiz?.questions?.length) return;
    if (Object.keys(finalAnswers).length < finalQuiz.questions.length) {
      setError('Responde todas las preguntas de la evaluacion final.');
      return;
    }
    setError('');
    try {
      const data = await api.post('/api/learning-route/final-quiz', { answers: finalAnswers });
      setFinalResult(data);
      setFinalQuiz(null);
      if (data.result?.percent === 100) {
        setShowConfetti(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo calificar la evaluacion final.');
    }
  }

  function askAssistant() {
    const text = assistantText.trim();
    if (!text) return;
    setAssistantMessages((items) => [
      ...items,
      { role: 'user', text },
      { role: 'assistant', text: hintFor(unit, text) },
    ]);
    setAssistantText('');
  }

  function renderQuestionSet({ questions, currentAnswers, setCurrentAnswers }) {
    return questions.map((question, index) => (
      <section className="lesson-question" key={question.id}>
        <small>{index + 1}. {question.topic}</small>
        <h3>{question.question}</h3>
        <div className="lesson-answer-grid">
          {question.options.map((option, optionIndex) => (
            <button
              className={currentAnswers[question.id] === optionIndex ? 'is-picked' : ''}
              key={`${question.id}-${optionIndex}`}
              type="button"
              onClick={() => setCurrentAnswers((current) => ({ ...current, [question.id]: optionIndex }))}
            >
              <b>{String.fromCharCode(65 + optionIndex)}</b>
              <span>{option}</span>
            </button>
          ))}
        </div>
      </section>
    ));
  }

  const isFinalUnlocked = useMemo(() => {
    if (!route?.units) return false;
    return ['1', '2', '3', '4'].every((id) => route.units[id]?.status === 'done');
  }, [route]);

  return (
    <main className="lesson-shell">
      <aside className="lesson-helper">
        <a className="lesson-brand" href="/ruta">
          <span><i className="bi bi-stars" /></span>
          <b>YELIA apoyo</b>
          <small>Solo pistas</small>
        </a>
        <div className="lesson-helper-log">
          {assistantMessages.map((message, index) => (
            <div className={`lesson-helper-msg is-${message.role}`} key={`${message.role}-${index}`}>
              {message.text}
            </div>
          ))}
        </div>
        <div className="lesson-helper-input">
          <textarea value={assistantText} onChange={(event) => setAssistantText(event.target.value)} placeholder="Pregunta una duda, no la respuesta..." />
          <button type="button" onClick={askAssistant}><i className="bi bi-send-fill" /></button>
        </div>
      </aside>

      <section className="lesson-main">
        <header className="lesson-topbar">
          <div>
            <span>Leccion por unidad</span>
            <h1>Unidad {unit.id}: {unit.title}</h1>
            <p>{unit.subtitle}</p>
          </div>
          <nav>
            <a href="/ruta">Ruta</a>
            <a href="/progreso">Progreso</a>
            <a href="/chat">Chat general</a>
          </nav>
        </header>

        {error ? <div className="lesson-error">{error}</div> : null}
        {loading ? <div className="lesson-error is-info">Cargando contenido oficial de la unidad...</div> : null}

        <div className="lesson-unit-tabs">
          {units.map((item) => {
            const isLocked = mounted && route?.units?.[String(item.id)]?.status === 'locked';
            return (
              <button
                className={`${Number(item.id) === Number(unit.id) ? 'is-active' : ''} ${isLocked ? 'is-locked' : ''}`}
                key={item.id}
                type="button"
                onClick={() => {
                  if (isLocked) {
                    setError(`La Unidad ${item.id} está bloqueada. Completa las unidades anteriores para continuar.`);
                    return;
                  }
                  changeUnit(item.id);
                }}
              >
                {isLocked && <i className="bi bi-lock-fill" style={{ marginRight: '4px' }} />}
                U{item.id}
              </button>
            );
          })}
          <button
            className={`${activePanel === 'final' ? 'is-active' : ''} ${(mounted && !isFinalUnlocked) ? 'is-locked' : ''}`}
            type="button"
            onClick={() => {
              if (mounted && !isFinalUnlocked) {
                setError('Completa las 4 unidades anteriores antes de rendir la evaluación final.');
                return;
              }
              switchPanel('final');
            }}
          >
            {mounted && !isFinalUnlocked && <i className="bi bi-lock-fill" style={{ marginRight: '6px' }} />}
            Examen final
          </button>
        </div>

        <div className="lesson-mode-tabs">
          <button className={`${activePanel === 'content' ? 'is-active' : ''}`} type="button" onClick={() => switchPanel('content', true)}>Contenido</button>
          
          <button
            className={`${activePanel === 'presentation' ? 'is-active' : ''} ${mounted && !isStepUnlocked('presentation') ? 'is-locked' : ''}`}
            type="button"
            onClick={() => switchPanel('presentation', true)}
          >
            {mounted && !isStepUnlocked('presentation') && <i className="bi bi-lock-fill" style={{ marginRight: '6px' }} />}
            Presentación
          </button>

          <button
            className={`${activePanel === 'videos' ? 'is-active' : ''} ${mounted && !isStepUnlocked('videos') ? 'is-locked' : ''}`}
            type="button"
            onClick={() => switchPanel('videos', true)}
          >
            {mounted && !isStepUnlocked('videos') && <i className="bi bi-lock-fill" style={{ marginRight: '6px' }} />}
            Videos
          </button>
          
          <button
            className={`${activePanel === 'workshop' ? 'is-active' : ''} ${mounted && !isStepUnlocked('workshop') ? 'is-locked' : ''}`}
            type="button"
            onClick={() => switchPanel('workshop', true)}
          >
            {mounted && !isStepUnlocked('workshop') && <i className="bi bi-lock-fill" style={{ marginRight: '6px' }} />}
            Taller
          </button>
          
          <button
            className={`${activePanel === 'lesson' ? 'is-active' : ''} ${mounted && !isStepUnlocked('lesson') ? 'is-locked' : ''}`}
            type="button"
            onClick={() => switchPanel('lesson', true)}
          >
            {mounted && !isStepUnlocked('lesson') && <i className="bi bi-lock-fill" style={{ marginRight: '6px' }} />}
            Lección
          </button>
          
          <button
            className={`${activePanel === 'exam' ? 'is-active' : ''} ${mounted && !isStepUnlocked('exam') ? 'is-locked' : ''}`}
            type="button"
            onClick={() => switchPanel('exam', true)}
          >
            {mounted && !isStepUnlocked('exam') && <i className="bi bi-lock-fill" style={{ marginRight: '6px' }} />}
            Examen unidad
          </button>
        </div>

        {activePanel === 'content' ? (
          <article className="lesson-card">
            <div className="lesson-section-head">
              <span><i className="bi bi-book" /></span>
              <div>
                <h2>Contenido oficial</h2>
                <p>Material base cargado desde tu ZIP academico.</p>
              </div>
            </div>
            
            <div style={{ marginTop: '20px', padding: '32px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', textAlign: 'center' }}>
              <i className="bi bi-file-earmark-pdf-fill" style={{ fontSize: '3rem', color: '#dc3545', display: 'block', marginBottom: '16px' }} />
              <h3 style={{ fontSize: '1.2rem', color: '#fff', marginBottom: '8px' }}>Material de Lectura Oficial - Unidad {unit.id}</h3>
              <p style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '24px', maxWidth: '450px', marginLeft: 'auto', marginRight: 'auto' }}>
                Estudia el contenido oficial de esta unidad en el visor de lectura. El avance se registrará automáticamente después de leer todo el documento y esperar los 3 minutos obligatorios.
              </p>
              <button
                type="button"
                onClick={() => {
                  setLastAutoOpened(`${unitId}-content`);
                  window.open(`/visor-pdf?unidad=${unitId}&tipo=contenido`, '_blank');
                }}
                className="btn btn-primary"
                style={{
                  padding: '12px 28px',
                  fontSize: '0.95rem',
                  fontWeight: '600',
                  color: '#fff',
                  background: 'linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%)',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 12px rgba(13,110,253,0.3)',
                  transition: 'transform 0.2s, box-shadow 0.2s'
                }}
              >
                Abrir PDF <i className="bi bi-box-arrow-up-right" />
              </button>
            </div>
            
            <div className="lesson-topic-list" style={{ marginTop: '20px' }}>
              {(unit.topics || []).map((topic) => <span key={topic}>{topic}</span>)}
            </div>
          </article>
        ) : null}

        {activePanel === 'presentation' ? (
          <article className="lesson-card">
            <div className="lesson-section-head">
              <span><i className="bi bi-file-earmark-slides" /></span>
              <div>
                <h2>Presentación Unidad {unit.id}</h2>
                <p>Visualiza las diapositivas de la unidad en tu navegador.</p>
              </div>
            </div>
            
            <div style={{ marginTop: '20px', padding: '32px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', textAlign: 'center' }}>
              <i className="bi bi-file-earmark-slides-fill" style={{ fontSize: '3rem', color: '#ffc107', display: 'block', marginBottom: '16px' }} />
              <h3 style={{ fontSize: '1.2rem', color: '#fff', marginBottom: '8px' }}>Presentación Diapositivas - Unidad {unit.id}</h3>
              <p style={{ opacity: 0.7, fontSize: '0.9rem', marginBottom: '24px', maxWidth: '450px', marginLeft: 'auto', marginRight: 'auto' }}>
                Estudia las diapositivas oficiales de la unidad en el visor de lectura. El avance se registrará automáticamente después de leer todo el documento y esperar los 3 minutos obligatorios.
              </p>
              <button
                type="button"
                onClick={() => {
                  setLastAutoOpened(`${unitId}-presentation`);
                  window.open(`/visor-pdf?unidad=${unitId}&tipo=presentacion`, '_blank');
                }}
                className="btn btn-primary"
                style={{
                  padding: '12px 28px',
                  fontSize: '0.95rem',
                  fontWeight: '600',
                  color: '#fff',
                  background: 'linear-gradient(135deg, #ffc107 0%, #ffb300 100%)',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 12px rgba(255,193,7,0.3)',
                  transition: 'transform 0.2s, box-shadow 0.2s'
                }}
              >
                Abrir Presentación <i className="bi bi-box-arrow-up-right" />
              </button>
            </div>
          </article>
        ) : null}

        {activePanel === 'videos' ? (
          <article className="lesson-card">
            <div className="lesson-section-head">
              <span><i className="bi bi-play-btn" /></span>
              <div>
                <h2>Videos de refuerzo de la Unidad {unit.id}</h2>
                <p>Visualiza estos videos para reforzar y comprender mejor los conceptos presentados en el contenido y la presentación de esta unidad.</p>
              </div>
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '24px',
              marginTop: '24px'
            }}>
              <div style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '12px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                <h3 style={{ fontSize: '1.1rem', color: '#fff', margin: 0 }}>🎥 Video 1</h3>
                <div style={{ position: 'relative', borderRadius: '8px', overflow: 'hidden', backgroundColor: '#000', aspectRatio: '16/9' }}>
                  <video 
                    controls 
                    controlsList="nodownload" 
                    onPlay={handlePlayVideo1} 
                    src={`/resources/RECURSOS_YELIA4AP/u${unitId}/videos/${encodeURIComponent('video 1.mp4')}`} 
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                </div>
              </div>

              <div style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '12px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                <h3 style={{ fontSize: '1.1rem', color: '#fff', margin: 0 }}>🎥 Video 2</h3>
                <div style={{ position: 'relative', borderRadius: '8px', overflow: 'hidden', backgroundColor: '#000', aspectRatio: '16/9' }}>
                  <video 
                    controls 
                    controlsList="nodownload" 
                    onPlay={handlePlayVideo2} 
                    src={`/resources/RECURSOS_YELIA4AP/u${unitId}/videos/${encodeURIComponent('video 2.mp4')}`} 
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                </div>
              </div>
            </div>

            {completedSteps.videos && (
              <div style={{
                marginTop: '24px',
                padding: '16px',
                background: 'rgba(25, 135, 84, 0.1)',
                border: '1px solid rgba(25, 135, 84, 0.2)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                color: '#198754'
              }}>
                <i className="bi bi-check-circle-fill" style={{ fontSize: '1.2rem' }} />
                <span>Paso completado. El taller ha sido desbloqueado.</span>
              </div>
            )}
            
            <div className="lesson-actions" style={{ marginTop: '24px' }}>
              <button 
                type="button" 
                onClick={() => switchPanel('workshop')}
                disabled={!completedSteps.videos}
                className={!completedSteps.videos ? 'is-locked' : ''}
                style={{
                  opacity: completedSteps.videos ? 1 : 0.6,
                  cursor: completedSteps.videos ? 'pointer' : 'not-allowed'
                }}
              >
                {!completedSteps.videos && <i className="bi bi-lock-fill" style={{ marginRight: '6px' }} />}
                Ir al taller
              </button>
            </div>
          </article>
        ) : null}

        {activePanel === 'workshop' ? (
          <article className="lesson-card lesson-quiz">
            <div className="lesson-section-head">
              <span><i className="bi bi-pencil-square" /></span>
              <div>
                <h2>Taller Unidad {unit.id}</h2>
                <p>Resuelve las preguntas de práctica del taller oficial.</p>
              </div>
            </div>
            {workshopQuestions.length ? renderQuestionSet({
              questions: publicQuestions(workshopQuestions),
              currentAnswers: workshopAnswers,
              setCurrentAnswers: setWorkshopAnswers,
            }) : <p className="lesson-empty">No se encontraron preguntas de taller para esta unidad.</p>}
            <div className="lesson-actions">
              <button type="button" onClick={submitWorkshopCheck}>Finalizar taller</button>
              <button type="button" onClick={() => switchPanel('lesson')}>Ir a lección</button>
            </div>
          </article>
        ) : null}

        {workshopResult ? (
          <article className={`lesson-result ${workshopResult.percent >= 70 ? 'is-pass' : 'is-retry'}`}>
            <span>{workshopResult.percent >= 70 ? 'Taller aprobado' : 'Taller por mejorar'}</span>
            <strong>{workshopResult.percent}%</strong>
            <p>Resultado del taller: {workshopResult.score}/{workshopResult.total}. {workshopResult.percent >= 70 ? '¡Buen trabajo! Puedes continuar con la lección.' : 'Revisa los conceptos y vuelve a intentar.'}</p>
          </article>
        ) : null}

        {activePanel === 'lesson' ? (
          <article className="lesson-card lesson-quiz">
            <div className="lesson-section-head">
              <span><i className="bi bi-ui-checks" /></span>
              <div>
                <h2>Leccion Unidad {unit.id}</h2>
                <p>Autoevaluacion de 5 preguntas antes del examen de unidad.</p>
              </div>
            </div>
            {lessonQuestions.length ? renderQuestionSet({
              questions: publicQuestions(lessonQuestions),
              currentAnswers: lessonAnswers,
              setCurrentAnswers: setLessonAnswers,
            }) : <p className="lesson-empty">No se encontraron preguntas de leccion para esta unidad.</p>}
            <div className="lesson-actions">
              <button type="button" onClick={submitLessonCheck}>Finalizar leccion</button>
              <button type="button" onClick={() => switchPanel('exam')}>Ir al examen</button>
            </div>
          </article>
        ) : null}

        {lessonResult ? (
          <article className={`lesson-result ${lessonResult.percent >= 70 ? 'is-pass' : 'is-retry'}`}>
            <span>{lessonResult.percent >= 70 ? 'Leccion aprobada' : 'Conviene repasar'}</span>
            <strong>{lessonResult.percent}%</strong>
            <p>Resultado de leccion: {lessonResult.score}/{lessonResult.total}. {lessonResult.percent >= 70 ? 'Puedes pasar al examen de unidad.' : 'Revisa el contenido y vuelve a intentar.'}</p>
          </article>
        ) : null}

        {activePanel === 'exam' && quiz ? (
          <article className="lesson-card lesson-quiz">
            <div className="lesson-section-head">
              <span><i className="bi bi-clipboard-check" /></span>
              <div>
                <h2>Examen Unidad {unit.id}</h2>
                <p>Examen oficial de 10 preguntas. Necesitas {quiz.passing_score || 70}% para desbloquear la siguiente unidad.</p>
              </div>
            </div>
            {renderQuestionSet({ questions: quiz.questions, currentAnswers: answers, setCurrentAnswers: setAnswers })}
            <div className="lesson-actions">
              <button type="button" onClick={submitQuiz}>Finalizar examen</button>
              <button type="button" onClick={() => switchPanel('content')}>Cerrar</button>
            </div>
          </article>
        ) : null}

        {result ? (
          <article className={`lesson-result ${result.result?.passed ? 'is-pass' : 'is-retry'}`}>
            <span>{result.result?.passed ? 'Unidad aprobada' : 'Necesita refuerzo'}</span>
            <strong>{result.result?.percent || 0}%</strong>
            <p>{result.feedback}</p>
            <div className="lesson-actions">
              <a href="/ruta">Volver a ruta</a>
              <a href="/progreso">Ver progreso</a>
            </div>
          </article>
        ) : null}

        {activePanel === 'final' && finalQuiz ? (
          <article className="lesson-card lesson-quiz">
            <div className="lesson-section-head">
              <span><i className="bi bi-award" /></span>
              <div>
                <h2>Evaluacion final</h2>
                <p>Solo se habilita al completar Unidad 1, Unidad 2, Unidad 3 y Unidad 4. Necesitas {finalQuiz.passing_score || 70}%.</p>
              </div>
            </div>
            {renderQuestionSet({ questions: finalQuiz.questions, currentAnswers: finalAnswers, setCurrentAnswers: setFinalAnswers })}
            <div className="lesson-actions">
              <button type="button" onClick={submitFinalQuiz}>Finalizar evaluacion</button>
              <button type="button" onClick={() => switchPanel('content')}>Cerrar</button>
            </div>
          </article>
        ) : null}

        {finalResult ? (
          <article className={`lesson-result ${finalResult.result?.passed ? 'is-pass' : 'is-retry'}`}>
            <span>{finalResult.result?.passed ? 'Ruta completada' : 'Refuerzo final'}</span>
            <strong>{finalResult.result?.percent || 0}%</strong>
            {finalResult.result?.passed ? (
              <div style={{ marginTop: '16px', marginBottom: '20px', lineHeight: '1.6', fontSize: '1.05rem', textAlign: 'left' }}>
                <p style={{ fontWeight: 'bold', fontSize: '1.25rem', margin: '0 0 12px 0', color: '#fff' }}>🎉 ¡Felicitaciones!</p>
                <p style={{ margin: '0 0 10px 0' }}>Has completado satisfactoriamente todos los módulos de Programación Avanzada disponibles en YELIA4AP.</p>
                <p style={{ margin: '0 0 10px 0' }}>Gracias por tu dedicación y compromiso durante este proceso de aprendizaje.</p>
                <p style={{ margin: '0 0 10px 0' }}>Esperamos que los conocimientos adquiridos te sean de gran utilidad en tu formación profesional.</p>
                <p style={{ fontWeight: 'bold', margin: '12px 0 0 0', color: '#fff' }}>¡Gracias por utilizar YELIA4AP!</p>
              </div>
            ) : (
              <p>{finalResult.feedback}</p>
            )}
            <div className="lesson-actions">
              <a href="/ruta">Volver a ruta</a>
              <a href="/progreso">Ver progreso</a>
            </div>
          </article>
        ) : null}
      </section>
      <Confetti active={showConfetti} onComplete={() => setShowConfetti(false)} />
    </main>
  );
}
