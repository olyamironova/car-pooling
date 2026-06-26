export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
      color: 'white',
      fontFamily: 'Inter, sans-serif',
    }}>
      <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🚗</div>
      <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>ОфисРайд</h1>
      <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '2rem' }}>Совместные поездки в офис</p>
      <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.9rem' }}>Перенаправление на приложение...</p>
      <script dangerouslySetInnerHTML={{
        __html: `
          // Redirect to Django app
          setTimeout(() => { window.location.reload(); }, 1000);
        `
      }} />
    </div>
  );
}
