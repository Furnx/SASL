// Site-wide configuration
export interface SiteConfig {
  language: string;
  siteName: string;
  siteDescription: string;
}

export const siteConfig: SiteConfig = {
  language: "en",
  siteName: "SignBridge SA",
  siteDescription: "Bridging communication between the deaf and hearing communities in South Africa through AI-powered sign language translation",
};

// Hero Section
export interface HeroConfig {
  backgroundImage: string;
  backgroundAlt: string;
  title: string;
  subtitle: string;
}

export const heroConfig: HeroConfig = {
  backgroundImage: "/hero-signlanguage.jpg",
  backgroundAlt: "Hands communicating in South African Sign Language",
  title: "SignBridge SA",
  subtitle: "Every Voice Deserves to Be Heard",
};

// Narrative Text Section
export interface NarrativeTextConfig {
  line1: string;
  line2: string;
  line3: string;
}

export const narrativeTextConfig: NarrativeTextConfig = {
  line1: "Breaking the silence between worlds",
  line2: "Connecting the deaf and hearing communities of South Africa",
  line3: "Our AI-powered platform translates South African Sign Language into spoken words and converts speech back into text, enabling natural, real-time conversations between people who communicate differently.",
};

// ZigZag Grid Section
export interface ZigZagGridItem {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  image: string;
  imageAlt: string;
  reverse: boolean;
}

export interface ZigZagGridConfig {
  sectionLabel: string;
  sectionTitle: string;
  items: ZigZagGridItem[];
}

export const zigZagGridConfig: ZigZagGridConfig = {
  sectionLabel: "How It Works",
  sectionTitle: "Simple. Powerful. Inclusive.",
  items: [
    {
      id: "sign",
      title: "Sign Naturally",
      subtitle: "For Deaf Users",
      description: "Simply sign in front of your camera using South African Sign Language. Our AI model trained on SASL gestures captures your movements in real-time, predicting each sign with high accuracy. No need to learn new technology—just communicate the way you know best.",
      image: "/feature-video.jpg",
      imageAlt: "Person signing in front of camera",
      reverse: false,
    },
    {
      id: "ai",
      title: "AI Translation",
      subtitle: "Smart Processing",
      description: "Behind the scenes, our system processes your signs, predicts the words, and sends them to an intelligent language model. The AI refines your message into natural, grammatically correct sentences—handling repetitions and filling in context so your meaning comes through clearly.",
      image: "/feature-voice.jpg",
      imageAlt: "AI processing visualization",
      reverse: true,
    },
    {
      id: "conversation",
      title: "Two-Way Conversation",
      subtitle: "Seamless Flow",
      description: "Your signed message is spoken aloud for the hearing person. When they respond, their voice is instantly converted to text that you can read. The conversation flows naturally back and forth—no barriers, no delays, just pure communication.",
      image: "/feature-tts.jpg",
      imageAlt: "Two people communicating",
      reverse: false,
    },
  ],
};

// Breath Section
export interface BreathSectionConfig {
  backgroundImage: string;
  backgroundAlt: string;
  title: string;
  subtitle: string;
  description: string;
}

export const breathSectionConfig: BreathSectionConfig = {
  backgroundImage: "/breath-connection.jpg",
  backgroundAlt: "Hands reaching toward each other in connection",
  title: "Connect",
  subtitle: "Communication Without Boundaries",
  description: "In South Africa, over 4 million people are deaf or hard of hearing. SignBridge SA creates a world where everyone can participate in conversations—at home, at work, in shops, and with friends. No one should be left out because of how they communicate.",
};

// Card Stack Section
export interface CardStackItem {
  id: number;
  image: string;
  title: string;
  description: string;
  rotation: number;
}

export interface CardStackConfig {
  sectionTitle: string;
  sectionSubtitle: string;
  cards: CardStackItem[];
}

export const cardStackConfig: CardStackConfig = {
  sectionTitle: "The Journey",
  sectionSubtitle: "From Signs to Understanding",
  cards: [
    {
      id: 1,
      image: "/step-1.jpg",
      title: "Capture",
      description: "Your camera captures every gesture with precision, frame by frame.",
      rotation: -2,
    },
    {
      id: 2,
      image: "/step-2.jpg",
      title: "Predict",
      description: "Our AI model recognizes each sign and builds your message word by word.",
      rotation: 1,
    },
    {
      id: 3,
      image: "/step-3.jpg",
      title: "Refine & Speak",
      description: "The message is polished into natural language and spoken aloud.",
      rotation: -1,
    },
  ],
};

// Footer Section
export interface FooterContactItem {
  type: "email" | "phone";
  label: string;
  value: string;
  href: string;
}

export interface FooterSocialItem {
  platform: string;
  href: string;
}

export interface FooterConfig {
  heading: string;
  description: string;
  ctaText: string;
  contact: FooterContactItem[];
  locationLabel: string;
  address: string[];
  socialLabel: string;
  socials: FooterSocialItem[];
  logoText: string;
  copyright: string;
  links: { label: string; href: string }[];
}

export const footerConfig: FooterConfig = {
  heading: "Start the Conversation",
  description: "Join thousands of South Africans who are breaking down communication barriers. SignBridge SA is free and always will be—because communication is a right, not a privilege.",
  ctaText: "Try It Now",
  contact: [
    {
      type: "email",
      label: "hello@signbridge.org.za",
      value: "hello@signbridge.org.za",
      href: "mailto:hello@signbridge.org.za",
    },
  ],
  locationLabel: "Location",
  address: ["South Africa"],
  socialLabel: "Follow",
  socials: [
    {
      platform: "instagram",
      href: "https://instagram.com/signbridgesa",
    },
    {
      platform: "facebook",
      href: "https://facebook.com/signbridgesa",
    },
  ],
  logoText: "SignBridge SA",
  copyright: "2025 SignBridge SA. All rights reserved.",
  links: [
    { label: "Privacy Policy", href: "#" },
    { label: "Terms of Service", href: "#" },
  ],
};
