import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { zigZagGridConfig, type ZigZagGridItem } from '../config';

gsap.registerPlugin(ScrollTrigger);

const GridItem = ({
  item,
  index,
}: {
  item: ZigZagGridItem;
  index: number;
}) => {
  const itemRef = useRef<HTMLDivElement>(null);
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const itemEl = itemRef.current;
    const imageContainer = imageContainerRef.current;
    const image = imageRef.current;
    const text = textRef.current;

    if (!itemEl || !imageContainer || !image || !text) return;

    // Initial state for text
    gsap.set(text.children, { opacity: 0, y: 30 });

    const triggers: ScrollTrigger[] = [];

    // Text reveal animation
    const textTrigger = ScrollTrigger.create({
      trigger: text,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        gsap.to(text.children, {
          opacity: 1,
          y: 0,
          duration: 0.8,
          stagger: 0.1,
          ease: 'power3.out',
        });
      },
    });
    triggers.push(textTrigger);

    // Internal parallax on image
    const imageTrigger = ScrollTrigger.create({
      trigger: imageContainer,
      start: 'top bottom',
      end: 'bottom top',
      scrub: true,
      onUpdate: (self) => {
        const yPercent = (self.progress - 0.5) * 20;
        gsap.set(image, { yPercent });
      },
    });
    triggers.push(imageTrigger);

    return () => {
      triggers.forEach(trigger => trigger.kill());
    };
  }, []);

  return (
    <div
      ref={itemRef}
      className={`grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16 items-center ${
        index > 0 ? 'mt-24 md:mt-32' : ''
      }`}
    >
      {/* Image Column */}
      <div
        ref={imageContainerRef}
        className={`relative overflow-hidden rounded-3xl ${
          item.reverse ? 'lg:order-2' : 'lg:order-1'
        }`}
      >
        <div className="relative aspect-[4/3] overflow-hidden">
          <img
            ref={imageRef}
            src={item.image}
            alt={item.imageAlt}
            className="w-full h-[120%] object-cover"
            style={{
              willChange: 'transform',
              transform: 'scale(1.1)',
            }}
          />
        </div>
      </div>

      {/* Text Column */}
      <div
        ref={textRef}
        className={`${item.reverse ? 'lg:order-1 lg:pr-8' : 'lg:order-2 lg:pl-8'}`}
      >
        <span className="font-body text-xs uppercase tracking-[0.2em] text-kaleo-terracotta">
          {item.subtitle}
        </span>
        <h3 className="font-display text-headline text-kaleo-earth mt-3">
          {item.title}
        </h3>
        <p className="font-body text-sm md:text-base text-kaleo-earth/70 leading-relaxed mt-6">
          {item.description}
        </p>

        {/* Decorative line */}
        <div className="w-16 h-px bg-kaleo-terracotta/30 mt-8" />
      </div>
    </div>
  );
};

const ZigZagGrid = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const header = headerRef.current;
    if (!header) return;

    gsap.set(header.children, { opacity: 0, y: 30 });

    const trigger = ScrollTrigger.create({
      trigger: header,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        gsap.to(header.children, {
          opacity: 1,
          y: 0,
          duration: 0.8,
          stagger: 0.15,
          ease: 'power3.out',
        });
      },
    });

    return () => {
      trigger.kill();
    };
  }, []);

  if (!zigZagGridConfig.sectionTitle && zigZagGridConfig.items.length === 0) return null;

  return (
    <section
      ref={sectionRef}
      className="relative w-full py-24 md:py-32 lg:py-40 bg-kaleo-sand"
    >
      <div className="max-w-7xl mx-auto px-6 md:px-8 lg:px-12">
        {/* Section Header */}
        <div ref={headerRef} className="text-center mb-20 md:mb-28">
          <span className="font-body text-xs uppercase tracking-[0.2em] text-kaleo-terracotta">
            {zigZagGridConfig.sectionLabel}
          </span>
          <h2 className="font-display text-headline text-kaleo-earth mt-4">
            {zigZagGridConfig.sectionTitle}
          </h2>
        </div>

        {/* Grid Items */}
        {zigZagGridConfig.items.map((item, index) => (
          <GridItem key={item.id} item={item} index={index} />
        ))}
      </div>
    </section>
  );
};

export default ZigZagGrid;
