import { useRef, useEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import ConversationInterface from '../components/ConversationInterface';

gsap.registerPlugin(ScrollTrigger);

export default function FeaturesDemo() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const section = sectionRef.current;
    const title = titleRef.current;
    const content = contentRef.current;

    if (!section || !title || !content) return;

    const triggers: ScrollTrigger[] = [];

    // Title animation
    const titleTrigger = ScrollTrigger.create({
      trigger: section,
      start: 'top 80%',
      onEnter: () => {
        gsap.fromTo(title,
          { y: 50, opacity: 0 },
          { y: 0, opacity: 1, duration: 1, ease: 'power3.out' }
        );
      },
      once: true
    });
    triggers.push(titleTrigger);

    // Content animation
    const contentTrigger = ScrollTrigger.create({
      trigger: content,
      start: 'top 80%',
      onEnter: () => {
        gsap.fromTo(content,
          { y: 80, opacity: 0 },
          { y: 0, opacity: 1, duration: 1, delay: 0.2, ease: 'power3.out' }
        );
      },
      once: true
    });
    triggers.push(contentTrigger);

    return () => {
      triggers.forEach(trigger => trigger.kill());
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative py-24 md:py-32 bg-kaleo-sand"
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-12">
          <span className="inline-block text-xs uppercase tracking-[0.3em] text-kaleo-terracotta mb-4">
            Try It Now
          </span>
          <h2
            ref={titleRef}
            className="font-display text-headline text-kaleo-earth opacity-0"
          >
            Start Communicating
          </h2>
          <p className="mt-4 text-kaleo-earth/70 max-w-2xl mx-auto">
            Enable your camera and microphone. Sign to speak, and read what others say. 
            It's that simple.
          </p>
        </div>

        {/* Conversation Interface */}
        <div
          ref={contentRef}
          className="opacity-0"
        >
          <ConversationInterface />
        </div>

        {/* How It Works */}
        <div className="mt-16 grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-12 h-12 bg-kaleo-terracotta/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-kaleo-terracotta font-display text-xl">1</span>
            </div>
            <h4 className="font-medium text-kaleo-earth mb-2">You Sign</h4>
            <p className="text-sm text-kaleo-earth/70">
              Use your camera to capture your sign language gestures
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-kaleo-terracotta/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-kaleo-terracotta font-display text-xl">2</span>
            </div>
            <h4 className="font-medium text-kaleo-earth mb-2">AI Converts</h4>
            <p className="text-sm text-kaleo-earth/70">
              Our AI predicts your signs, refines the sentence, and speaks it aloud
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-12 h-12 bg-kaleo-terracotta/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-kaleo-terracotta font-display text-xl">3</span>
            </div>
            <h4 className="font-medium text-kaleo-earth mb-2">They Respond</h4>
            <p className="text-sm text-kaleo-earth/70">
              Their voice response is converted to text for you to read
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
