/**
 * Gastrotech Premium Animation Library
 * Reusable Framer Motion variants and animations
 */

import { Variants, Transition } from "framer-motion";

// ============================================================================
// MOTION PREFERENCES UTILITY
// ============================================================================

/**
 * Check if user prefers reduced motion
 */
export const prefersReducedMotion = (): boolean => {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
};

/**
 * Wrapper for motion components that respects reduced motion preferences
 */
export const getMotionProps = <T extends Record<string, unknown>>(
  motionProps: T
): T | Record<string, never> => {
  return prefersReducedMotion() ? {} as Record<string, never> : motionProps;
};

// ============================================================================
// TRANSITION PRESETS
// ============================================================================

export const transitions = {
  // Spring animations
  spring: {
    type: "spring",
    stiffness: 300,
    damping: 30,
  } as Transition,
  
  springBouncy: {
    type: "spring",
    stiffness: 500,
    damping: 25,
  } as Transition,
  
  springSlow: {
    type: "spring",
    stiffness: 200,
    damping: 40,
  } as Transition,
  
  // Ease animations
  ease: {
    duration: 0.3,
    ease: [0.4, 0, 0.2, 1],
  } as Transition,
  
  easeSlow: {
    duration: 0.5,
    ease: [0.4, 0, 0.2, 1],
  } as Transition,
  
  easeOut: {
    duration: 0.3,
    ease: [0, 0, 0.2, 1],
  } as Transition,
};

// ============================================================================
// FADE VARIANTS
// ============================================================================

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: transitions.ease,
  },
};

export const fadeInUp: Variants = {
  hidden: { 
    opacity: 0, 
    y: 20,
  },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: transitions.ease,
  },
};

export const fadeInDown: Variants = {
  hidden: { 
    opacity: 0, 
    y: -20,
  },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: transitions.ease,
  },
};

export const fadeInLeft: Variants = {
  hidden: { 
    opacity: 0, 
    x: -20,
  },
  visible: { 
    opacity: 1, 
    x: 0,
    transition: transitions.ease,
  },
};

export const fadeInRight: Variants = {
  hidden: { 
    opacity: 0, 
    x: 20,
  },
  visible: { 
    opacity: 1, 
    x: 0,
    transition: transitions.ease,
  },
};

// ============================================================================
// SCALE VARIANTS
// ============================================================================

export const scaleIn: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.9,
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: transitions.spring,
  },
};

export const scaleInBounce: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.5,
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: transitions.springBouncy,
  },
};

export const popIn: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.8,
    y: 10,
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: transitions.spring,
  },
};

// ============================================================================
// STAGGER CONTAINERS
// ============================================================================

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

export const staggerContainerFast: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.05,
    },
  },
};

export const staggerContainerSlow: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.2,
    },
  },
};

// ============================================================================
// STAGGER CHILDREN
// ============================================================================

export const staggerItem: Variants = {
  hidden: { 
    opacity: 0, 
    y: 20,
  },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: transitions.ease,
  },
};

export const staggerItemScale: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.9,
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: transitions.spring,
  },
};

// ============================================================================
// HOVER & TAP VARIANTS
// ============================================================================

export const hoverScale = {
  scale: 1.02,
  transition: transitions.spring,
};

export const hoverScaleSm = {
  scale: 1.05,
  transition: transitions.spring,
};

export const hoverLift = {
  y: -4,
  transition: transitions.spring,
};

export const tapScale = {
  scale: 0.98,
  transition: { duration: 0.1 },
};

// ============================================================================
// LIST ITEM VARIANTS (for AnimatePresence)
// ============================================================================

export const listItem: Variants = {
  hidden: { 
    opacity: 0, 
    x: -20,
    height: 0,
  },
  visible: { 
    opacity: 1, 
    x: 0,
    height: "auto",
    transition: transitions.ease,
  },
  exit: { 
    opacity: 0, 
    x: 20,
    height: 0,
    transition: { duration: 0.2 },
  },
};

export const gridItem: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.9,
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: transitions.spring,
  },
  exit: { 
    opacity: 0, 
    scale: 0.9,
    transition: { duration: 0.2 },
  },
};

// ============================================================================
// MODAL & OVERLAY VARIANTS
// ============================================================================

export const overlay: Variants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { duration: 0.2 },
  },
  exit: { 
    opacity: 0,
    transition: { duration: 0.2 },
  },
};

export const modal: Variants = {
  hidden: { 
    opacity: 0, 
    scale: 0.95,
    y: 20,
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: transitions.spring,
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    y: 20,
    transition: { duration: 0.2 },
  },
};

export const drawer: Variants = {
  hidden: { 
    x: "100%",
  },
  visible: { 
    x: 0,
    transition: transitions.springSlow,
  },
  exit: { 
    x: "100%",
    transition: { duration: 0.3 },
  },
};

// ============================================================================
// PAGE TRANSITION VARIANTS
// ============================================================================

export const pageTransition: Variants = {
  hidden: { 
    opacity: 0,
    y: 20,
  },
  visible: { 
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1],
    },
  },
  exit: { 
    opacity: 0,
    y: -20,
    transition: {
      duration: 0.3,
    },
  },
};

// ============================================================================
// SKELETON LOADING VARIANTS
// ============================================================================

export const skeleton: Variants = {
  loading: {
    opacity: [0.5, 1, 0.5],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
};

// ============================================================================
// SCROLL-TRIGGERED VARIANTS
// ============================================================================

export const scrollFadeIn: Variants = {
  offscreen: {
    opacity: 0,
    y: 50,
  },
  onscreen: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.4, 0, 0.2, 1],
    },
  },
};

export const scrollScaleIn: Variants = {
  offscreen: {
    opacity: 0,
    scale: 0.9,
  },
  onscreen: {
    opacity: 1,
    scale: 1,
    transition: transitions.spring,
  },
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Creates a staggered delay for array items
 */
export function staggerDelay(index: number, baseDelay = 0.1): number {
  return index * baseDelay;
}

/**
 * Viewport options for scroll-triggered animations
 */
export const viewportOnce = { once: true, margin: "-100px" };
export const viewportAlways = { once: false, margin: "-50px" };

