"use client";

import { useEffect } from "react";
import { useSiteSettings } from "@/hooks/use-site-settings";

export function SiteSettingsInitializer() {
    // const { fetchSettings } = useSiteSettings(); // Removed unused destructuring

    useEffect(() => {
        // Initial fetch on mount
        useSiteSettings.getState().fetchSettings();
    }, []);

    return null;
}
