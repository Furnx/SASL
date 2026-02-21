import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { narrativeTextConfig } from '../config';

gsap.registerPlugin(ScrollTrigger);

// 4-Point Star SVG Component
const StarIcon = ({ className }: { className?: string }) => (
  <svg
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M12 0L14.5 9.5L24 12L14.5 14.5L12 24L9.5 14.5L0 12L9.5 9.5L12 0Z" />
  </svg>
);

const NarrativeText = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const line1Ref = useRef<HTMLParagraphElement>(null);
  const line2Ref = useRef<HTMLParagraphElement>(null);
  const line3Ref = useRef<HTMLParagraphElement>(null);
  const starRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const line1 = line1Ref.current;
    const line2 = line2Ref.current;
    const line3 = line3Ref.current;
    const star = starRef.current;

    if (!section || !line1 || !line2 || !line3 || !star) return;

    // Set initial states
    gsap.set([line1, line2, line3], { opacity: 0, y: 30 });
    gsap.set(star, { opacity: 0, scale: 0.5 });

    const triggers: ScrollTrigger[] = [];

    // Star animation
    const starTrigger = ScrollTrigger.create({
      trigger: star,
      start: 'top 85%',
      once: true,
      onEnter: () => {
        gsap.to(star, {
          opacity: 1,
          scale: 1,
          duration: 0.8,
          ease: 'back.out(1.7)',
        });
      },
    });
    triggers.push(starTrigger);

    // Line animations with stagger
    const line1Trigger = ScrollTrigger.create({
      trigger: line1,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        gsap.to(line1, {
          opacity: 1,
          y: 0,
          duration: 1,
          ease: 'power3.out',
        });
      },
    });
    triggers.push(line1Trigger);

    const line2Trigger = ScrollTrigger.create({
      trigger: line2,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        gsap.to(line2, {
          opacity: 1,
          y: 0,
          duration: 1,
          delay: 0.15,
          ease: 'power3.out',
        });
      },
    });
    triggers.push(line2Trigger);

    const line3Trigger = ScrollTrigger.create({
      trigger: line3,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        gsap.to(line3, {
          opacity: 1,
          y: 0,
          duration: 1,
          delay: 0.3,
          ease: 'power3.out',
        });
      },
    });
    triggers.push(line3Trigger);

    return () => {
      triggers.forEach(trigger => trigger.kill());
    };
  }, []);

  if (!narrativeTextConfig.line1 && !narrativeTextConfig.line2 && !narrativeTextConfig.line3) return null;

  return (
    <section
      ref={sectionRef}
      className="relative w-full py-32 md:py-48 lg:py-56 bg-kaleo-sand"
    >
      <div className="max-w-4xl mx-auto px-6 md:px-8 text-center">
        {/* Spinning Star */}
        <div
          ref={starRef}
          className="flex justify-center mb-16"
          style={{ willChange: 'transform, opacity' }}
        >
          <StarIcon className="w-6 h-6 md:w-8 md:h-8 text-kaleo-terracotta spin-slow" />
        </div>

        {/* Narrative Text */}
        <div className="space-y-8 md:space-y-10">
          <p
            ref={line1Ref}
            className="font-display text-headline text-kaleo-earth"
            style={{ willChange: 'transform, opacity' }}
          >
            {narrativeTextConfig.line1}
          </p>

          <p
            ref={line2Ref}
            className="font-display text-subheadline text-kaleo-earth/80 italic max-w-2xl mx-auto"
            style={{ willChange: 'transform, opacity' }}
          >
            {narrativeTextConfig.line2}
          </p>

          <p
            ref={line3Ref}
            className="font-body text-sm md:text-base text-kaleo-earth/60 max-w-lg mx-auto leading-relaxed tracking-wide"
            style={{ willChange: 'transform, opacity' }}
          >
            {narrativeTextConfig.line3}
          </p>
        </div>

        {/* Bottom Star */}
        <div className="flex justify-center mt-16">
          <StarIcon className="w-4 h-4 text-kaleo-terracotta/50" />
        </div>
      </div>
    </section>
  );
};

export default NarrativeText;
