'use client';

import { useEffect, useRef } from 'react';

export default function Confetti({ active, duration = 4000, onComplete }) {
  const canvasRef = useRef(null);

  const onCompleteRef = useRef(onComplete);

  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    if (!active) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let isRunning = true;
    const startTime = Date.now();

    // Resize canvas to full screen
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Particle class
    class Particle {
      constructor(x, y, angle, spread, color) {
        this.x = x;
        this.y = y;
        
        // Shoot direction
        const velocity = 15 + Math.random() * 15;
        const radAngle = angle + (Math.random() - 0.5) * spread;
        this.vx = Math.cos(radAngle) * velocity;
        this.vy = Math.sin(radAngle) * velocity;
        
        // Particle attributes
        this.color = color;
        this.width = 6 + Math.random() * 8;
        this.height = 12 + Math.random() * 12;
        this.rotation = Math.random() * 360;
        this.rotationSpeed = (Math.random() - 0.5) * 10;
        this.opacity = 1;
        this.gravity = 0.5;
        this.drag = 0.98;
        this.shape = Math.random() > 0.5 ? 'rect' : 'circle';
      }

      update() {
        this.vx *= this.drag;
        this.vy *= this.drag;
        this.vy += this.gravity;
        this.x += this.vx;
        this.y += this.vy;
        this.rotation += this.rotationSpeed;
        
        // Fade out near the end of the duration
        const elapsed = Date.now() - startTime;
        if (elapsed > duration - 1000) {
          this.opacity = Math.max(0, 1 - (elapsed - (duration - 1000)) / 1000);
        }
      }

      draw() {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate((this.rotation * Math.PI) / 180);
        ctx.globalAlpha = this.opacity;
        ctx.fillStyle = this.color;

        if (this.shape === 'rect') {
          ctx.fillRect(-this.width / 2, -this.height / 2, this.width, this.height);
        } else {
          ctx.beginPath();
          ctx.arc(0, 0, this.width / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }
    }

    const colors = [
      '#FFC107', '#FF5722', '#E91E63', '#9C27B0', '#3F51B5',
      '#00BCD4', '#4CAF50', '#8BC34A', '#CDDC39', '#FFEB3B'
    ];

    const particles = [];

    // Create particles from both bottom corners (left & right)
    const createBurst = () => {
      // Left corner shooting up-right (angle around -45 deg)
      for (let i = 0; i < 75; i++) {
        particles.push(
          new Particle(
            0,
            canvas.height,
            -Math.PI / 4,
            Math.PI / 6,
            colors[Math.floor(Math.random() * colors.length)]
          )
        );
      }
      // Right corner shooting up-left (angle around -135 deg)
      for (let i = 0; i < 75; i++) {
        particles.push(
          new Particle(
            canvas.width,
            canvas.height,
            (-3 * Math.PI) / 4,
            Math.PI / 6,
            colors[Math.floor(Math.random() * colors.length)]
          )
        );
      }
    };

    createBurst();

    // Animation Loop
    const tick = () => {
      if (!isRunning) return;

      const elapsed = Date.now() - startTime;
      if (elapsed > duration) {
        isRunning = false;
        if (onCompleteRef.current) onCompleteRef.current();
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p) => {
        p.update();
        p.draw();
      });

      animationFrameId = requestAnimationFrame(tick);
    };

    tick();

    return () => {
      isRunning = false;
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', resizeCanvas);
    };
  }, [active, duration]);

  if (!active) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 99999,
      }}
    />
  );
}
