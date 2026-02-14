import React from "react";

export function TurkeyFlag({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 1200 800"
            className={className}
            aria-label="Turkey Flag"
        >
            <rect width="1200" height="800" fill="#E30A17" />
            <circle cx="444" cy="400" r="240" fill="#ffffff" />
            <circle cx="474" cy="400" r="192" fill="#E30A17" />
            <path
                fill="#ffffff"
                d="m 583.334,400 183.393,133.242 -70.046,-215.586 70.046,-215.586 -183.393,133.242 h -226.68 l 183.393,133.242 z"
                transform="matrix(0.32029,0,0,0.32029,484.09,271.88)"
            />
            <polygon
                fill="#ffffff"
                points="652.6,359.1 635.5,459.7 724.4,395.1 578.8,395.1 667.7,459.7 "
                transform="translate(150,0)"
            />
        </svg>
    );
}

export function UKFlag({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 60 30"
            className={className}
            aria-label="United Kingdom Flag"
        >
            <clipPath id="t">
                <path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z" />
            </clipPath>
            <path d="M0,0 v30 h60 v-30 z" fill="#00247d" />
            <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" strokeWidth="6" />
            <path
                d="M0,0 L60,30 M60,0 L0,30"
                clipPath="url(#t)"
                stroke="#cf142b"
                strokeWidth="4"
            />
            <path d="M30,0 v30 M0,15 h60" stroke="#fff" strokeWidth="10" />
            <path d="M30,0 v30 M0,15 h60" stroke="#cf142b" strokeWidth="6" />
        </svg>
    );
}

export function GermanyFlag({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 5 3"
            className={className}
            aria-label="Germany Flag"
        >
            <rect width="5" height="3" y="0" fill="#000" />
            <rect width="5" height="2" y="1" fill="#D00" />
            <rect width="5" height="1" y="2" fill="#FFCE00" />
        </svg>
    );
}

export function FranceFlag({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 3 2"
            className={className}
            aria-label="France Flag"
        >
            <rect width="3" height="2" fill="#ED2939" />
            <rect width="2" height="2" fill="#fff" />
            <rect width="1" height="2" fill="#002395" />
        </svg>
    );
}

export function ItalyFlag({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 3 2"
            className={className}
            aria-label="Italy Flag"
        >
            <rect width="3" height="2" fill="#CE2B37" />
            <rect width="2" height="2" fill="#fff" />
            <rect width="1" height="2" fill="#009246" />
        </svg>
    );
}

export function SaudiArabiaFlag({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 300 200"
            className={className}
            aria-label="Saudi Arabia Flag"
        >
            <rect width="300" height="200" fill="#006C35" />
            <text
                x="150"
                y="90"
                fill="#fff"
                fontSize="24"
                fontFamily="serif"
                textAnchor="middle"
                dominantBaseline="middle"
            >
                العربية
            </text>
        </svg>
    );
}

