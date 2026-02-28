"use client";

import { useEffect, useState, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";

export function PageLoader() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [isNavigating, setIsNavigating] = useState(false);
  const isFirstRender = useRef(true);
  const previousPathname = useRef(pathname);

  // Handle initial page load
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitialLoad(false);
    }, 800);

    return () => clearTimeout(timer);
  }, []);

  // Handle navigation between pages
  useEffect(() => {
    // Skip on first render (initial load is handled separately)
    if (isFirstRender.current) {
      isFirstRender.current = false;
      previousPathname.current = pathname;
      return;
    }

    // Check if pathname actually changed
    if (previousPathname.current !== pathname) {
      setIsNavigating(true);
      previousPathname.current = pathname;

      // Hide after a short delay
      const timer = setTimeout(() => {
        setIsNavigating(false);
      }, 400);

      return () => clearTimeout(timer);
    }
  }, [pathname, searchParams]);

  return (
    <>
      {/* Full Screen Loader - Initial Load Only */}
      <AnimatePresence>
        {isInitialLoad && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-white"
          >
            {/* Background decorations */}
            <div className="absolute top-0 left-0 w-64 h-64 bg-primary/5 rounded-sm -translate-x-1/2 -translate-y-1/2" />
            <div className="absolute bottom-0 right-0 w-80 h-80 bg-primary/5 rounded-sm translate-x-1/2 translate-y-1/2" />

            {/* Content */}
            <div className="relative z-10 flex flex-col items-center gap-8">
              {/* Logo */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <Image
                  src="/assets/logo.webp"
                  alt="Gastrotech"
                  width={180}
                  height={60}
                  className="object-contain"
                  priority
                />
              </motion.div>

              {/* Spinner */}
              <div className="relative">
                <motion.div
                  className="w-12 h-12 border-4 border-primary/20 rounded-full"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 }}
                />
                <motion.div
                  className="absolute inset-0 w-12 h-12 border-4 border-transparent border-t-primary rounded-full"
                  animate={{ rotate: 360 }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                />
              </div>

              {/* Loading text */}
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-sm font-medium text-muted-foreground"
              >
                Yükleniyor...
              </motion.p>
            </div>

            {/* Bottom decoration line */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-primary to-transparent opacity-50" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Corner Mini Loader - Navigation Between Pages */}
      <AnimatePresence>
        {isNavigating && !isInitialLoad && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, x: 20 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.8, x: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-6 right-6 z-[9998] flex items-center gap-3 bg-white rounded-sm px-4 py-3 shadow-lg border border-border/50"
          >
            {/* Mini spinner */}
            <div className="relative w-5 h-5">
              <div className="w-5 h-5 border-2 border-primary/20 rounded-full" />
              <motion.div
                className="absolute inset-0 w-5 h-5 border-2 border-transparent border-t-primary rounded-full"
                animate={{ rotate: 360 }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  ease: "linear",
                }}
              />
            </div>
            {/* Text */}
            <span className="text-xs font-medium text-muted-foreground">
              Yükleniyor
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
