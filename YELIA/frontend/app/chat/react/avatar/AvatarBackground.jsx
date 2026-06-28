'use client';

import React, { useEffect, useRef } from 'react';

export default function AvatarBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let width = canvas.width = canvas.offsetWidth || 300;
    let height = canvas.height = canvas.offsetHeight || 300;

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth || 300;
      height = canvas.height = canvas.offsetHeight || 300;
    };
    window.addEventListener('resize', handleResize);

    // Particle settings: 28 general particles + 9 HUD ring particles
    const particles = [];

    const initializeParticles = () => {
      particles.length = 0;
      const baseDim = Math.min(width, height);
      const centerX = width / 2;
      const centerY = height * 0.46;

      // 1. General background particles (28 particles)
      for (let i = 0; i < 28; i++) {
        const radius = 0.5 + Math.random() * 1.3;
        const speed = 0.012 + Math.random() * 0.022; // very slow/subtle drift
        const angle = Math.random() * Math.PI * 2;
        const opacity = 0.22 + Math.random() * 0.18;

        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          radius,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          color: Math.random() > 0.5 
            ? `rgba(0, 242, 254, ${opacity})` 
            : `rgba(56, 189, 248, ${opacity})`,
          opacity
        });
      }

      // 2. HUD-specific particles (9 cian particles distributed around the tech circle)
      for (let i = 0; i < 9; i++) {
        const angle = (i * Math.PI * 2) / 9 + (Math.random() - 0.5) * 0.3;
        const dist = baseDim * 0.32 + (Math.random() - 0.5) * 16; // close to Circle 2 radius
        const pAngle = Math.random() * Math.PI * 2;
        const speed = 0.008 + Math.random() * 0.012; // extra slow drift
        const opacity = 0.35 + Math.random() * 0.15; // soft, discrete glow

        particles.push({
          x: centerX + Math.cos(angle) * dist,
          y: centerY + Math.sin(angle) * dist,
          radius: 0.6 + Math.random() * 0.6, // small particles
          vx: Math.cos(pAngle) * speed,
          vy: Math.sin(pAngle) * speed,
          color: `rgba(0, 242, 254, ${opacity})`,
          opacity
        });
      }
    };

    initializeParticles();

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height * 0.46;
      const baseDim = Math.min(width, height);

      // 1. Soft Backdrop Ambient Glow (resplandor azul 10-15% más profundo)
      const bgGlowRadius = baseDim * 0.70;
      const bgGlowGradient = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, bgGlowRadius
      );
      bgGlowGradient.addColorStop(0, 'rgba(0, 242, 254, 0.23)'); // slightly more intense cian halo
      bgGlowGradient.addColorStop(0.3, 'rgba(16, 62, 120, 0.40)'); // #103E78 blue resplandor (increased 10-15%)
      bgGlowGradient.addColorStop(0.8, 'rgba(7, 24, 39, 0.10)'); // #071827 deep blue blend
      bgGlowGradient.addColorStop(1, 'rgba(7, 24, 39, 0)');
      ctx.fillStyle = bgGlowGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, bgGlowRadius, 0, Math.PI * 2);
      ctx.fill();

      // 2. Holographic Pedestal (con brillo ligeramente incrementado para efecto de suspensión)
      const pedestalY = height * 0.84;
      const pedRadiusX = baseDim * 0.28;
      const pedRadiusY = baseDim * 0.07;

      // Pedestal Base Glow (increased brightness)
      const pedGlow = ctx.createRadialGradient(
        centerX, pedestalY, 0,
        centerX, pedestalY, pedRadiusX
      );
      pedGlow.addColorStop(0, 'rgba(0, 242, 254, 0.40)'); // increased cian base glow
      pedGlow.addColorStop(0.5, 'rgba(16, 62, 120, 0.18)'); // increased blue outer glow
      pedGlow.addColorStop(1, 'rgba(7, 24, 39, 0)');
      ctx.fillStyle = pedGlow;
      ctx.beginPath();
      ctx.ellipse(centerX, pedestalY, pedRadiusX, pedRadiusY, 0, 0, 2 * Math.PI);
      ctx.fill();

      // Outer Pedestal Ring (solid, cian, slightly brighter)
      ctx.strokeStyle = 'rgba(0, 242, 254, 0.58)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.ellipse(centerX, pedestalY, pedRadiusX, pedRadiusY, 0, 0, 2 * Math.PI);
      ctx.stroke();

      // Inner Pedestal Ring (solid, cian, slightly brighter)
      ctx.strokeStyle = 'rgba(0, 242, 254, 0.38)';
      ctx.lineWidth = 1.0;
      ctx.beginPath();
      ctx.ellipse(centerX, pedestalY, pedRadiusX * 0.7, pedRadiusY * 0.7, 0, 0, 2 * Math.PI);
      ctx.stroke();

      // Mid Pedestal Ring (dashed, slowly rotating, slightly brighter)
      const pedAngle = (performance.now() / 25000) % (Math.PI * 2);
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
      ctx.lineWidth = 1.0;
      ctx.setLineDash([4, 8]);
      ctx.save();
      ctx.translate(centerX, pedestalY);
      ctx.rotate(pedAngle);
      ctx.beginPath();
      ctx.ellipse(0, 0, pedRadiusX * 0.85, pedRadiusY * 0.85, 0, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.restore();
      ctx.setLineDash([]); // reset

      // Rising Projection Rays from the pedestal (slightly brighter)
      const drawRay = (offsetX, targetY) => {
        const x = centerX + offsetX;
        const grad = ctx.createLinearGradient(x, pedestalY, x, targetY);
        grad.addColorStop(0, 'rgba(0, 242, 254, 0.22)'); // increased ray brightness
        grad.addColorStop(1, 'rgba(0, 242, 254, 0)');
        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(x, pedestalY);
        ctx.lineTo(x, targetY);
        ctx.stroke();
      };
      drawRay(-pedRadiusX * 0.6, pedestalY - baseDim * 0.15);
      drawRay(pedRadiusX * 0.6, pedestalY - baseDim * 0.15);
      drawRay(-pedRadiusX * 0.2, pedestalY - baseDim * 0.25);
      drawRay(pedRadiusX * 0.2, pedestalY - baseDim * 0.25);

      // 3. Concentric HUD Circles (Con brillo cian intenso y glow)
      const time = performance.now();
      
      // Circle 1: Inner core rim (solid, very faint cian)
      ctx.strokeStyle = 'rgba(0, 242, 254, 0.30)';
      ctx.lineWidth = 1.0;
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseDim * 0.24, 0, Math.PI * 2);
      ctx.stroke();

      // Circle 2: Main HUD circle with intense cian glow
      ctx.save();
      ctx.strokeStyle = 'rgba(0, 242, 254, 0.75)';
      ctx.lineWidth = 1.8;
      ctx.shadowBlur = 10;
      ctx.shadowColor = 'rgba(0, 242, 254, 0.70)';
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseDim * 0.32, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      // Circle 3: Mid tech ring (dashed, rotating slowly clockwise)
      const rotAngle3 = (time / 22000) % (Math.PI * 2);
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.52)';
      ctx.lineWidth = 1.2;
      ctx.setLineDash([5, 10]);
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(rotAngle3);
      ctx.beginPath();
      ctx.arc(0, 0, baseDim * 0.39, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      // Circle 4: Outer tech ring (fine dashes, rotating counter-clockwise)
      const rotAngle4 = (-time / 30000) % (Math.PI * 2);
      ctx.strokeStyle = 'rgba(0, 242, 254, 0.35)';
      ctx.lineWidth = 1.0;
      ctx.setLineDash([2, 5]);
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(rotAngle4);
      ctx.beginPath();
      ctx.arc(0, 0, baseDim * 0.46, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
      ctx.setLineDash([]); // reset

      // Circle 5: Corner HUD Bracket Arcs (outer accents)
      ctx.strokeStyle = 'rgba(0, 242, 254, 0.30)';
      ctx.lineWidth = 1.5;
      const bracketRadius = baseDim * 0.54;
      
      const drawBracket = (start, end) => {
        ctx.beginPath();
        ctx.arc(centerX, centerY, bracketRadius, start, end);
        ctx.stroke();
      };
      drawBracket(0.08 * Math.PI, 0.38 * Math.PI);
      drawBracket(0.58 * Math.PI, 0.88 * Math.PI);
      drawBracket(1.08 * Math.PI, 1.38 * Math.PI);
      drawBracket(1.58 * Math.PI, 1.88 * Math.PI);

      // 4. Tenue circuit lines (8 branches)
      const branchCount = 8;
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.40)';
      ctx.lineWidth = 1.0;
      
      for (let i = 0; i < branchCount; i++) {
        const angle = (i * Math.PI * 2) / branchCount;
        const startRad = baseDim * 0.24;
        const startX = centerX + Math.cos(angle) * startRad;
        const startY = centerY + Math.sin(angle) * startRad;
        
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        
        // Extend line outward
        const extX = startX + Math.cos(angle) * 12;
        const extY = startY + Math.sin(angle) * 12;
        ctx.lineTo(extX, extY);
        
        // 45 degree bend
        const bendAngle = angle + (i % 2 === 0 ? Math.PI / 4 : -Math.PI / 4);
        const endX = extX + Math.cos(bendAngle) * 9;
        const endY = extY + Math.sin(bendAngle) * 9;
        ctx.lineTo(endX, endY);
        ctx.stroke();

        // Small glowing dot at the end
        ctx.fillStyle = i % 2 === 0 ? 'rgba(0, 242, 254, 0.85)' : 'rgba(56, 189, 248, 0.85)';
        ctx.beginPath();
        ctx.arc(endX, endY, 2.0, 0, Math.PI * 2);
        ctx.fill();
      }

      // 5. Draw small glowing HUD data points along the main circle
      ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
      for (let i = 0; i < 4; i++) {
        const angle = (i * Math.PI / 2) + (time / 50000);
        const ptX = centerX + Math.cos(angle) * (baseDim * 0.32);
        const ptY = centerY + Math.sin(angle) * (baseDim * 0.32);
        ctx.beginPath();
        ctx.arc(ptX, ptY, 1.2, 0, Math.PI * 2);
        ctx.fill();
      }

      // 6. Draw particles (very slowly floating and subtle)
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        // boundary wrap
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        ctx.beginPath();
        ctx.fillStyle = p.color;
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 1, // behind the 3D canvas stage
      }}
    />
  );
}
