import React, { useLayoutEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';

gsap.registerPlugin(ScrollTrigger);

function BlurText({ text }) {
  const words = text.split(' ');
  const root = useRef(null);

  useLayoutEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;

    const context = gsap.context(() => {
      gsap.fromTo(
        root.current.querySelectorAll('[data-blur-word]'),
        { autoAlpha: 0, y: 18, filter: 'blur(8px)' },
        { autoAlpha: 1, y: 0, filter: 'blur(0px)', duration: 0.7, stagger: 0.08, ease: 'power3.out' },
      );
    }, root);

    return () => context.revert();
  }, []);

  return (
    <span ref={root} className="about-blur-text">
      <span className="visually-hidden">{text}</span>
      <span aria-hidden="true">
        {words.map((word, index) => (
          <span className="about-blur-word" data-blur-word key={`${word}-${index}`}>{word}</span>
        ))}
      </span>
    </span>
  );
}

const titleMount = document.getElementById('about-react-title');
if (titleMount) {
  createRoot(titleMount).render(<BlurText text={titleMount.dataset.text} />);
}

if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const lenis = new Lenis({ autoRaf: false, smoothWheel: true });
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add((time) => lenis.raf(time * 1000));
  gsap.ticker.lagSmoothing(0);

  const preview = document.querySelector('.about-session-preview');
  if (preview) {
    gsap.fromTo(
      preview,
      { autoAlpha: 0, x: 28, y: 12 },
      {
        autoAlpha: 1,
        x: 0,
        y: 0,
        duration: 0.9,
        ease: 'power3.out',
        scrollTrigger: { trigger: preview, start: 'top 88%', once: true },
      },
    );
  }
}
