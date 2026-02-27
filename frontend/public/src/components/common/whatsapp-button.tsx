"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";

const WHATSAPP_NUMBER = "902122379055";
const WHATSAPP_MESSAGE = "Merhaba, ürünleriniz hakkında bilgi almak istiyorum.";

export function WhatsAppButton() {
  const [hovered, setHovered] = useState(false);
  const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(WHATSAPP_MESSAGE)}`;

  const onEnter = useCallback(() => setHovered(true), []);
  const onLeave = useCallback(() => setHovered(false), []);

  return (
    <motion.a
      href={whatsappUrl}
      target="_blank"
      rel="noopener noreferrer"
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      className="fixed right-0 top-1/2 z-50 flex items-center no-underline"
      style={{ marginTop: -32 }}
      initial={{ x: 100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
        delay: 1,
      }}
      aria-label="WhatsApp ile iletişime geç"
    >
      <motion.div
        className="flex items-center h-12 bg-[#25D366] text-white rounded-l-sm shadow-lg overflow-hidden cursor-pointer"
        animate={{
          paddingLeft: hovered ? 16 : 0,
          paddingRight: hovered ? 12 : 0,
        }}
        whileTap={{ scale: 0.97 }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
      >
        {/* Label — slides in from right */}
        <motion.span
          className="text-sm font-semibold whitespace-nowrap overflow-hidden leading-none"
          animate={{
            width: hovered ? 90 : 0,
            opacity: hovered ? 1 : 0,
            marginRight: hovered ? 8 : 0,
          }}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
        >
          Bize Ulaşın
        </motion.span>

        {/* Icon container — always 48×48 */}
        <span className="flex items-center justify-center w-12 h-12 flex-shrink-0">
          <svg
            viewBox="0 0 24 24"
            className="w-6 h-6 fill-current"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
          </svg>
        </span>
      </motion.div>
    </motion.a>
  );
}
