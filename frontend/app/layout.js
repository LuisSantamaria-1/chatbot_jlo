import './globals.css';

export const metadata = {
  title: 'Leonardito - Asistente Virtual MDJLO',
  description: 'Chatbot de atención ciudadana para trámites de la Municipalidad Distrital de José Leonardo Ortiz',
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className="antialiased bg-[#f4f6f9]">{children}</body>
    </html>
  );
}
