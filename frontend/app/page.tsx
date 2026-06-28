import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default function RoleSelectionPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/pages/role-selection.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='role-selection-body';" }} />

      <main className="selection-container">
        <header className="selection-header">
          <div className="selection-logo">YELIA4AP</div>
          <h1>Portal de Acceso Universitario</h1>
          <p>
            Plataforma educativa con inteligencia artificial adaptativa para Programación Orientada a Objetos y Programación Avanzada.
          </p>
        </header>

        <div className="role-grid">
          {/* Tarjeta de Administrador */}
          <Link href="/admin/login" className="role-card admin">
            <div className="role-icon-container">
              <i className="bi bi-shield-lock-fill" />
            </div>
            <h2>Administrador</h2>
            <p>Acceso a la configuración global del sistema, gestión de bases de datos, tokens de acceso y control de servicios.</p>
            <span className="role-btn">Ingresar</span>
          </Link>

          {/* Tarjeta de Docente */}
          <Link href="/docente/login" className="role-card docente">
            <div className="role-icon-container">
              <i className="bi bi-mortarboard-fill" />
            </div>
            <h2>Docente</h2>
            <p>Visualización del progreso del curso, mapas de calor estudiantiles, análisis de debilidades y métricas académicas.</p>
            <span className="role-btn">Ingresar</span>
          </Link>

          {/* Tarjeta de Estudiante */}
          <Link href="/launcher" className="role-card estudiante">
            <div className="role-icon-container">
              <i className="bi bi-person-fill-gear" />
            </div>
            <h2>Estudiante</h2>
            <p>Acceso al chat adaptativo con Yelia, ruta de aprendizaje por unidades, actividades prácticas y quizzes formativos.</p>
            <span className="role-btn">Ingresar</span>
          </Link>
        </div>

        <footer className="selection-footer">
          <div>YELIA4AP &bull; Universidad de Guayaquil &bull; Facultad de Ingeniería Industrial</div>
          <div style={{ marginTop: '0.5rem' }}>Proyecto Académico de Titulación &bull; Carrera de Telemática</div>
        </footer>
      </main>
    </>
  );
}
