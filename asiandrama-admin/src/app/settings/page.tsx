'use client';

import { supabase } from '@/lib/supabase';
import { Image as ImageIcon, Save, ToggleLeft, ToggleRight, Upload, CheckCircle2, XCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export default function SettingsPage() {
    const [appName, setAppName] = useState('AsianDrama');
    const [appIcon, setAppIcon] = useState<string | null>(null);
    const [maintenanceMode, setMaintenanceMode] = useState(false);
    const [coinPrice, setCoinPrice] = useState('10000');
    const [vipMonthlyPrice, setVipMonthlyPrice] = useState('49000');
    const [adEnabled, setAdEnabled] = useState(true);
    const [freeEpisodes, setFreeEpisodes] = useState('5');
    const [adInterval, setAdInterval] = useState('5');

    // Layout Settings
    const [layoutDramabox, setLayoutDramabox] = useState('10');
    const [layoutNetshort, setLayoutNetshort] = useState('10');
    const [layoutFlickreels, setLayoutFlickreels] = useState('10');
    const [layoutDramanova, setLayoutDramanova] = useState('10');
    const [layoutDramawave, setLayoutDramawave] = useState('10');
    const [layoutMelolo, setLayoutMelolo] = useState('10');

    // Default Provider Order
    const [providerOrder, setProviderOrder] = useState<string[]>([
        'dramabox', 'netshort', 'flickreels', 'dramanova', 'dramawave', 'melolo'
    ]);

    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Toast State
    const [toast, setToast] = useState<{ show: boolean; type: 'success' | 'error'; message: string } | null>(null);

    const showToast = (message: string, type: 'success' | 'error' = 'success') => {
        setToast({ show: true, type, message });
        setTimeout(() => setToast(null), 3000);
    };

    useEffect(() => {
        fetchSettings();
    }, []);

    async function fetchSettings() {
        const { data } = await supabase.from('app_settings').select('*');
        if (data) {
            data.forEach((setting) => {
                switch (setting.key) {
                    case 'app_name': setAppName(setting.value); break;
                    case 'app_icon': setAppIcon(setting.value); break;
                    case 'maintenance_mode': setMaintenanceMode(setting.value === 'true'); break;
                    case 'coin_price': setCoinPrice(setting.value); break;
                    case 'vip_monthly_price': setVipMonthlyPrice(setting.value); break;
                    case 'ad_enabled': setAdEnabled(setting.value === 'true'); break;
                    case 'free_episodes': setFreeEpisodes(setting.value); break;
                    case 'ad_interval': setAdInterval(setting.value); break;
                    case 'provider_layout':
                        try {
                            const parsed = JSON.parse(setting.value);
                            if (parsed.dramabox !== undefined) setLayoutDramabox(String(parsed.dramabox));
                            if (parsed.netshort !== undefined) setLayoutNetshort(String(parsed.netshort));
                            if (parsed.flickreels !== undefined) setLayoutFlickreels(String(parsed.flickreels));
                            if (parsed.dramanova !== undefined) setLayoutDramanova(String(parsed.dramanova));
                            if (parsed.dramawave !== undefined) setLayoutDramawave(String(parsed.dramawave));
                            if (parsed.melolo !== undefined) setLayoutMelolo(String(parsed.melolo));
                            
                            if (Array.isArray(parsed.order) && parsed.order.length > 0) {
                                setProviderOrder(parsed.order);
                            }
                        } catch(e) {
                            console.error('Failed to parse provider_layout', e);
                        }
                        break;
                }
            });
        }
        setLoading(false);
    }

    const handleIconUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Validate file type
        if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
            showToast('Hanya file JPG atau PNG yang diperbolehkan', 'error');
            return;
        }

        // Validate file size (max 2MB)
        if (file.size > 2 * 1024 * 1024) {
            showToast('Ukuran file maksimal 2MB', 'error');
            return;
        }

        setUploading(true);

        try {
            // Upload via server-side API route (uses service_role key, bypasses RLS)
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/api/upload-icon', { method: 'POST', body: formData });
            const result = await res.json();

            if (!res.ok) throw new Error(result.error);

            setAppIcon(result.url);
            showToast('Icon berhasil diupload!', 'success');
        } catch (error: any) {
            console.error('Upload error:', error);
            showToast('Gagal upload: ' + error.message, 'error');
        } finally {
            setUploading(false);
        }
    };

    const handleSave = async () => {
        const settings = [
            { key: 'app_name', value: appName },
            { key: 'app_icon', value: appIcon || '' },
            { key: 'maintenance_mode', value: maintenanceMode.toString() },
            { key: 'coin_price', value: coinPrice },
            { key: 'vip_monthly_price', value: vipMonthlyPrice },
            { key: 'ad_enabled', value: adEnabled.toString() },
            { key: 'free_episodes', value: freeEpisodes },
            { key: 'ad_interval', value: adInterval },
            { 
                key: 'provider_layout', 
                value: JSON.stringify({
                    dramabox: parseInt(layoutDramabox) || 10,
                    netshort: parseInt(layoutNetshort) || 10,
                    flickreels: parseInt(layoutFlickreels) || 10,
                    dramanova: parseInt(layoutDramanova) || 10,
                    dramawave: parseInt(layoutDramawave) || 10,
                    melolo: parseInt(layoutMelolo) || 10,
                    order: providerOrder
                }) 
            },
        ];

        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            const result = await res.json();
            if (!res.ok) throw new Error(result.error || 'Failed to save settings');
            showToast('Settings saved successfully!', 'success');
        } catch (error: any) {
            console.error('Error saving settings:', error);
            showToast(error.message, 'error');
        }
    };

    const moveProviderUp = (index: number) => {
        if (index === 0) return;
        const newOrder = [...providerOrder];
        [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]];
        setProviderOrder(newOrder);
    };

    const moveProviderDown = (index: number) => {
        if (index === providerOrder.length - 1) return;
        const newOrder = [...providerOrder];
        [newOrder[index + 1], newOrder[index]] = [newOrder[index], newOrder[index + 1]];
        setProviderOrder(newOrder);
    };

    const getProviderName = (id: string) => {
        const names: Record<string, string> = {
            dramabox: 'Dramabox', netshort: 'Netshort', flickreels: 'FlickReels',
            dramanova: 'DramaNova', dramawave: 'DramaWave', melolo: 'Melolo'
        };
        return names[id] || id;
    };

    const getProviderLayoutState = (id: string) => {
        switch(id) {
            case 'dramabox': return layoutDramabox;
            case 'netshort': return layoutNetshort;
            case 'flickreels': return layoutFlickreels;
            case 'dramanova': return layoutDramanova;
            case 'dramawave': return layoutDramawave;
            case 'melolo': return layoutMelolo;
            default: return '10';
        }
    };

    const setProviderLayoutState = (id: string, val: string) => {
        switch(id) {
            case 'dramabox': setLayoutDramabox(val); break;
            case 'netshort': setLayoutNetshort(val); break;
            case 'flickreels': setLayoutFlickreels(val); break;
            case 'dramanova': setLayoutDramanova(val); break;
            case 'dramawave': setLayoutDramawave(val); break;
            case 'melolo': setLayoutMelolo(val); break;
        }
    };

    if (loading) return <div className="text-center py-20">Loading...</div>;

    return (
        <div className="relative min-h-screen">
            <h1 className="text-2xl font-bold mb-6">Settings</h1>

            <div className="max-w-2xl space-y-6">
                {/* App Settings */}
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                    <h2 className="font-semibold mb-4">App Configuration</h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Nama Aplikasi</label>
                            <input
                                type="text"
                                value={appName}
                                onChange={(e) => setAppName(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                        </div>

                        {/* App Icon Upload */}
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Icon Aplikasi</label>
                            <div className="flex items-center gap-4">
                                {/* Preview */}
                                <div className="w-20 h-20 bg-gray-800 rounded-xl border border-gray-700 flex items-center justify-center overflow-hidden">
                                    {appIcon ? (
                                        <img src={appIcon} alt="App Icon" className="w-full h-full object-cover" />
                                    ) : (
                                        <ImageIcon className="text-gray-600" size={32} />
                                    )}
                                </div>

                                {/* Upload Button */}
                                <div>
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept=".jpg,.jpeg,.png"
                                        onChange={handleIconUpload}
                                        className="hidden"
                                    />
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={uploading}
                                        className="bg-gray-800 hover:bg-gray-700 border border-gray-700 px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50"
                                    >
                                        <Upload size={18} />
                                        {uploading ? 'Uploading...' : 'Upload Icon'}
                                    </button>
                                    <p className="text-xs text-gray-500 mt-2">JPG atau PNG, max 2MB</p>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between py-3 border-t border-gray-800">
                            <div>
                                <p className="font-medium">Maintenance Mode</p>
                                <p className="text-sm text-gray-500">Nonaktifkan akses user sementara</p>
                            </div>
                            <button
                                onClick={() => setMaintenanceMode(!maintenanceMode)}
                                className={`text-3xl ${maintenanceMode ? 'text-red-500' : 'text-gray-600'}`}
                            >
                                {maintenanceMode ? <ToggleRight /> : <ToggleLeft />}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Pricing Settings */}
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                    <h2 className="font-semibold mb-4">Pricing</h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Harga per 100 Koin (Rp)</label>
                            <input
                                type="number"
                                value={coinPrice}
                                onChange={(e) => setCoinPrice(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Harga VIP Bulanan (Rp)</label>
                            <input
                                type="number"
                                value={vipMonthlyPrice}
                                onChange={(e) => setVipMonthlyPrice(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                        </div>
                    </div>
                </div>

                {/* Ad Settings */}
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                    <h2 className="font-semibold mb-4">Pengaturan Iklan</h2>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between py-3">
                            <div>
                                <p className="font-medium">Iklan Aktif</p>
                                <p className="text-sm text-gray-500">Tampilkan iklan interstitial antar episode</p>
                            </div>
                            <button
                                onClick={() => setAdEnabled(!adEnabled)}
                                className={`text-3xl ${adEnabled ? 'text-green-500' : 'text-gray-600'}`}
                            >
                                {adEnabled ? <ToggleRight /> : <ToggleLeft />}
                            </button>
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Episode Gratis (tanpa iklan)</label>
                            <input
                                type="number"
                                value={freeEpisodes}
                                onChange={(e) => setFreeEpisodes(e.target.value)}
                                min="0"
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                            <p className="text-xs text-gray-500 mt-1">Episode 1 sampai {freeEpisodes} tidak ada iklan</p>
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Interval Iklan (setiap N episode)</label>
                            <input
                                type="number"
                                value={adInterval}
                                onChange={(e) => setAdInterval(e.target.value)}
                                min="1"
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                            <p className="text-xs text-gray-500 mt-1">Iklan muncul setiap {adInterval} episode setelah episode gratis</p>
                        </div>
                    </div>
                </div>

                {/* Provider Layout Settings */}
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                    <h2 className="font-semibold mb-4">Urutan & Tampilan "Semua Drama"</h2>
                    <p className="text-sm text-gray-500 mb-6">
                        Tentukan jumlah maksimal drama yang ditarik per giliran rotasi.<br/>
                        <b>Urutan tayang baku:</b> Dramabox → Netshort → FlickReels → DramaNova → DramaWave → Melolo.
                    </p>
                    <div className="flex flex-col gap-3">
                        {providerOrder.map((providerId, index) => (
                            <div key={providerId} className="flex items-center gap-4 bg-gray-800 p-3 rounded-lg border border-gray-700">
                                <div className="flex flex-col gap-1">
                                    <button 
                                        onClick={() => moveProviderUp(index)} 
                                        disabled={index === 0}
                                        className={`p-1 rounded bg-gray-700 hover:bg-gray-600 ${index === 0 ? 'opacity-30 cursor-not-allowed' : ''}`}
                                    >
                                        ↑
                                    </button>
                                    <button 
                                        onClick={() => moveProviderDown(index)} 
                                        disabled={index === providerOrder.length - 1}
                                        className={`p-1 rounded bg-gray-700 hover:bg-gray-600 ${index === providerOrder.length - 1 ? 'opacity-30 cursor-not-allowed' : ''}`}
                                    >
                                        ↓
                                    </button>
                                </div>
                                <div className="flex-1">
                                    <label className="block text-sm text-gray-400 mb-1">{index + 1}. {getProviderName(providerId)}</label>
                                    <input 
                                        type="number" 
                                        value={getProviderLayoutState(providerId)} 
                                        onChange={e => setProviderLayoutState(providerId, e.target.value)} 
                                        min="1" 
                                        className="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500" 
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Save Button */}
                <button
                    onClick={handleSave}
                    className="bg-amber-500 hover:bg-amber-600 px-6 py-3 rounded-lg flex items-center gap-2"
                >
                    <Save size={20} /> Simpan Settings
                </button>
            </div>

            {/* Toast Notification */}
            {toast && toast.show && (
                <div className={`fixed bottom-6 right-6 flex items-center gap-3 px-6 py-4 rounded-xl shadow-lg shadow-black/50 transform transition-all duration-300 translate-y-0 opacity-100 ${toast.type === 'success' ? 'bg-green-500/20 border border-green-500/50 text-green-400' : 'bg-red-500/20 border border-red-500/50 text-red-400'} z-50`} style={{ backdropFilter: 'blur(8px)' }}>
                    {toast.type === 'success' ? <CheckCircle2 size={24} className="text-green-500" /> : <XCircle size={24} className="text-red-500" />}
                    <span className="font-medium">{toast.message}</span>
                </div>
            )}
        </div>
    );
}
