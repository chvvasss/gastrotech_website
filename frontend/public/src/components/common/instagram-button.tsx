"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";

const INSTAGRAM_URL = "https://www.instagram.com/gastrotech.tr/";

export function InstagramButton() {
    const [hovered, setHovered] = useState(false);

    const onEnter = useCallback(() => setHovered(true), []);
    const onLeave = useCallback(() => setHovered(false), []);

    return (
        <motion.a
            href={INSTAGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            onMouseEnter={onEnter}
            onMouseLeave={onLeave}
            className="fixed right-0 top-1/2 z-50 flex items-center no-underline"
            style={{ marginTop: 32 }}
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{
                type: "spring",
                stiffness: 260,
                damping: 20,
                delay: 1.3,
            }}
            aria-label="Instagram'da takip et"
        >
            <motion.div
                className="flex items-center h-12 text-white rounded-l-sm shadow-lg overflow-hidden cursor-pointer"
                style={{
                    background: "linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)",
                }}
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
                        width: hovered ? 74 : 0,
                        opacity: hovered ? 1 : 0,
                        marginRight: hovered ? 8 : 0,
                    }}
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                >
                    Takip Et
                </motion.span>

                {/* Icon container — always 48×48 */}
                <span className="flex items-center justify-center w-12 h-12 flex-shrink-0">
                    <svg
                        viewBox="0 0 24 24"
                        className="w-6 h-6 fill-current"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                    </svg>
                </span>
            </motion.div>
        </motion.a>
    );
}
