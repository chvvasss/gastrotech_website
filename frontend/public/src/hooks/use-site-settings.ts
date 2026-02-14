
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';
import { ENDPOINTS } from '@/lib/api/endpoints';

interface SiteSettingsState {
    showPrices: boolean;
    setShowPrices: (show: boolean) => void;
    catalogMode: boolean;
    setCatalogMode: (mode: boolean) => void;
    isLoading: boolean;
    fetchSettings: () => Promise<void>;
    _hasHydrated: boolean;
    setHasHydrated: (state: boolean) => void;
}

export const useSiteSettings = create<SiteSettingsState>()(
    persist(
        (set) => ({
            showPrices: true,
            catalogMode: false,
            isLoading: false,
            _hasHydrated: false,
            setHasHydrated: (state) => set({ _hasHydrated: state }),
            setShowPrices: (show) => set({ showPrices: show }),
            setCatalogMode: (mode) => set({ catalogMode: mode }),
            fetchSettings: async () => {
                set({ isLoading: true });
                try {
                    const response = await axios.get(`${ENDPOINTS.COMMON_CONFIG}?t=${Date.now()}`);
                    if (response.data) {
                        const updates: Partial<SiteSettingsState> = {};
                        if (typeof response.data.show_prices === 'boolean') {
                            updates.showPrices = response.data.show_prices;
                        }
                        if (typeof response.data.catalog_mode === 'boolean') {
                            updates.catalogMode = response.data.catalog_mode;
                        }
                        console.log("Fetched Site Settings:", updates);
                        set(updates);
                    }
                } catch (error) {
                    console.error('Failed to fetch site settings:', error);
                } finally {
                    set({ isLoading: false });
                }
            },
        }),
        {
            name: 'site-settings-storage',
            onRehydrateStorage: () => (state) => {
                state?.setHasHydrated(true);
            },
        }
    )
);
