"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/layout";

interface FeatureSplitSectionProps {
  title: string;
  description: string;
  bullets?: string[];
  imageSrc: string;
  imageAlt: string;
  ctaLabel?: string;
  ctaHref?: string;
  imagePosition?: "left" | "right";
}

export function FeatureSplitSection({
  title,
  description,
  bullets = [],
  imageSrc,
  imageAlt,
  ctaLabel,
  ctaHref,
  imagePosition = "left",
}: FeatureSplitSectionProps) {
  const isImageLeft = imagePosition === "left";

  return (
    <section className="relative py-10 lg:py-14 overflow-hidden">
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-muted/40 via-background to-muted/20" />

      <Container className="relative">
        <div className="max-w-5xl mx-auto">
          <div
            className={`grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 items-center ${isImageLeft ? "" : "lg:flex-row-reverse"
              }`}
          >
            {/* Image Column */}
            <motion.div
              className={`relative ${isImageLeft ? "lg:order-1" : "lg:order-2"}`}
              initial={{ opacity: 0, x: isImageLeft ? -40 : 40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <div className="relative aspect-[4/3] w-full overflow-hidden shadow-2xl">
                {/* Image */}
                <Image
                  src={imageSrc}
                  alt={imageAlt}
                  fill
                  className="object-cover"
                  sizes="(max-width: 1024px) 100vw, 40vw"
                />

                {/* Premium overlay gradient */}
                <div className="absolute inset-0 bg-gradient-to-tr from-black/20 via-transparent to-white/10" />

                {/* Corner accent - Sharp & Technical */}
                <div className="absolute top-0 left-0 h-20 w-20 bg-primary flex items-center justify-center">
                  <div className="text-white text-center">
                    <div className="text-2xl font-bold leading-none">40+</div>
                    <div className="text-xs uppercase tracking-wider mt-1 opacity-90">Yıl</div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Text Column */}
            <motion.div
              className={`space-y-6 ${isImageLeft ? "lg:order-2" : "lg:order-1"}`}
              initial={{ opacity: 0, x: isImageLeft ? 40 : -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              {/* Section label */}
              <div className="flex items-center gap-3">
                <div className="h-0.5 w-8 bg-primary" />
                <span className="text-xs font-bold text-primary uppercase tracking-widest">
                  Hakkımızda
                </span>
              </div>

              {/* Title */}
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-foreground leading-tight tracking-tight">
                {title}
              </h2>

              {/* Description */}
              <p className="text-muted-foreground text-base lg:text-lg leading-relaxed">
                {description}
              </p>

              {/* Bullet points */}
              {bullets.length > 0 && (
                <ul className="space-y-3 pt-2">
                  {bullets.map((bullet, index) => (
                    <motion.li
                      key={index}
                      className="flex items-start gap-3"
                      initial={{ opacity: 0, x: 20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
                    >
                      <div className="flex-shrink-0 h-6 w-6 bg-primary/10 flex items-center justify-center mt-0.5">
                        <Check className="h-4 w-4 text-primary" />
                      </div>
                      <span className="text-foreground/90 font-medium">{bullet}</span>
                    </motion.li>
                  ))}
                </ul>
              )}

              {/* CTA Button */}
              {ctaLabel && ctaHref && (
                <motion.div
                  className="pt-4"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: 0.5 }}
                >
                  <Button
                    asChild
                    size="lg"
                    className="rounded-sm h-12 px-8 font-semibold text-base shadow-lg shadow-primary/15"
                  >
                    <Link href={ctaHref}>
                      {ctaLabel}
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </motion.div>
              )}
            </motion.div>
          </div>
        </div>
      </Container>
    </section>
  );
}
