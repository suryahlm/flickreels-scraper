'use client';

import { supabase } from '@/lib/supabase';
import { 
    Settings, 
    Save, 
    Upload, 
    CheckCircle2, 
    XCircle, 
    GripVertical, 
    Shield, 
    Crown, 
    Tv, 
    Sliders, 
    Sparkles, 
    AlertTriangle, 
    Coins, 
    CreditCard, 
    Loader2, 
    Layers, 
    Image as ImageIcon,
    Info
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

type TabKey = 'identity' | 'vip' | 'ads' | 'layout';

const PROVIDER_NAMES: Record<string, { label: string; badge: string; color: string }> = {
    dramabox: { label: 'DramaBox', badge: 'DB', color: 'from-amber-500/20 to-yellow-500/10 text-amber-400 border-amber-500/30' },
    netshort: { label: 'NetShort', badge: 'NS', color: 'from-emerald-500/20 to-teal-500/10 text-emerald-400 border-emerald-500/30' },
    flickreels: { label: 'FlickReels', badge: 'FR', color: 'from-rose-500/20 to-red-500/10 text-rose-400 border-rose-500/30' },
    dramanova: { label: 'DramaNova', badge: 'DN', color: 'from-sky-500/20 to-blue-500/10 text-sky-400 border-sky-500/30' },
    dramawave: { label: 'DramaWave', badge: 'DW', color: 'from-purple-500/20 to-indigo-500/10 text-purple-400 border-purple-500/30' },
    melolo: { label: 'Melolo', badge: 'ML', color: 'from-amber-600/20 to-orange-500/10 text-orange-400 border-orange-500/30' },
};

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState<TabKey>('identity');

    // App Identity
    const [appName, setAppName] = useState('AsianDrama');
    const [appIcon, setAppIcon] = useState<string | null>(null);
    const [maintenanceMode, setMaintenanceMode] = useState(false);
    const [rewardBottomText, setRewardBottomText] = useState('Kumpulkan koinmu sekarang - Fitur VIP untuk nonton tanpa iklan & download drama telah hadir');
    
    // VIP with Real Money
    const [vipMonthlyPrice, setVipMonthlyPrice] = useState('49000');
    const [vip3MonthPrice, setVip3MonthPrice] = useState('129000');
    const [vip1YearPrice, setVip1YearPrice] = useState('399000');

    // VIP with Coins
    const [vipCoin1Month, setVipCoin1Month] = useState('1000');
    const [vipCoin3Month, setVipCoin3Month] = useState('2500');
    const [vipCoin1Year, setVipCoin1Year] = useState('8000');

    // VIP Feature Toggles
    const [vipMoneyEnabled, setVipMoneyEnabled] = useState(true);
    const [vipMoneyMsg, setVipMoneyMsg] = useState('Fitur VIP sedang dalam pengembangan atau perbaikan oleh Admin.');
    const [vipCoinEnabled, setVipCoinEnabled] = useState(true);
    const [vipCoinMsg, setVipCoinMsg] = useState('Fitur Tukar Koin sedang dalam perbaikan oleh Admin.');

    // Ad & Free Mode Settings
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
    const [providerOrder, setProviderOrder] = useState<string[]>(['dramabox', 'netshort', 'flickreels', 'dramanova', 'dramawave', 'melolo']);
    
    // Drag and drop refs
    const dragItem = useRef<number | null>(null);
    const dragOverItem = useRef<number | null>(null);

    const handleSort = () => {
        if (dragItem.current === null || dragOverItem.current === null) return;
        
        let _providerOrder = [...providerOrder];
        const draggedItemContent = _providerOrder.splice(dragItem.current, 1)[0];
        _providerOrder.splice(dragOverItem.current, 0, draggedItemContent);
        
        dragItem.current = null;
        dragOverItem.current = null;
        setProviderOrder(_providerOrder);
    };

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Toast State
    const [toast, setToast] = useState<{ show: boolean; type: 'success' | 'error'; message: string } | null>(null);

    const showToast = (message: string, type: 'success' | 'error' = 'success') => {
        setToast({ show: true, type, message });
        setTimeout(() => setToast(null), 3500);
    };

    useEffect(() => {
        fetchSettings();
    }, []);

    async function fetchSettings() {
        setLoading(true);
        const { data } = await supabase.from('app_settings').select('*');
        if (data) {
            data.forEach((setting) => {
                switch (setting.key) {
                    case 'app_name': setAppName(setting.value); break;
                    case 'app_icon': setAppIcon(setting.value); break;
                    case 'maintenance_mode': setMaintenanceMode(setting.value === 'true'); break;
                    case 'reward_bottom_text': setRewardBottomText(setting.value); break;
                    case 'vip_monthly_price': setVipMonthlyPrice(setting.value); break;
                    case 'vip_3month_price': setVip3MonthPrice(setting.value); break;
                    case 'vip_1year_price': setVip1YearPrice(setting.value); break;
                    case 'vip_coin_1month': setVipCoin1Month(setting.value); break;
                    case 'vip_coin_3month': setVipCoin3Month(setting.value); break;
                    case 'vip_coin_1year': setVipCoin1Year(setting.value); break;
                    case 'vip_money_enabled': setVipMoneyEnabled(setting.value !== 'false'); break;
                    case 'vip_money_msg': setVipMoneyMsg(setting.value); break;
                    case 'vip_coin_enabled': setVipCoinEnabled(setting.value !== 'false'); break;
                    case 'vip_coin_msg': setVipCoinMsg(setting.value); break;
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
                            if (Array.isArray(parsed.order)) {
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

        if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
            showToast('Hanya format JPG atau PNG yang diperbolehkan', 'error');
            return;
        }

        if (file.size > 2 * 1024 * 1024) {
            showToast('Ukuran file maksimal 2MB', 'error');
            return;
        }

        setUploading(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/api/upload-icon', { method: 'POST', body: formData });
            const result = await res.json();

            if (!res.ok) throw new Error(result.error || 'Gagal mengunggah icon');

            setAppIcon(result.url);
            showToast('Icon aplikasi berhasil diperbarui! Simpan pengaturan untuk menerapkan.', 'success');
        } catch (error: any) {
            console.error('Upload error:', error);
            showToast('Gagal upload: ' + error.message, 'error');
        } finally {
            setUploading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        const settings = [
            { key: 'app_name', value: appName },
            { key: 'app_icon', value: appIcon || '' },
            { key: 'maintenance_mode', value: maintenanceMode.toString() },
            { key: 'reward_bottom_text', value: rewardBottomText },
            { key: 'vip_monthly_price', value: vipMonthlyPrice },
            { key: 'vip_3month_price', value: vip3MonthPrice },
            { key: 'vip_1year_price', value: vip1YearPrice },
            { key: 'vip_coin_1month', value: vipCoin1Month },
            { key: 'vip_coin_3month', value: vipCoin3Month },
            { key: 'vip_coin_1year', value: vipCoin1Year },
            { key: 'vip_money_enabled', value: vipMoneyEnabled.toString() },
            { key: 'vip_money_msg', value: vipMoneyMsg },
            { key: 'vip_coin_enabled', value: vipCoinEnabled.toString() },
            { key: 'vip_coin_msg', value: vipCoinMsg },
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
                body: JSON.stringify(settings),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.error || 'Gagal menyimpan pengaturan');
            }

            showToast('Seluruh konfigurasi sistem berhasil disimpan ke database!', 'success');
        } catch (error: any) {
            console.error('Save error:', error);
            showToast('Gagal menyimpan: ' + error.message, 'error');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-[60vh] flex-col items-center justify-center space-y-4">
                <div className="relative w-12 h-12 flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full border-2 border-amber-500/20 border-t-amber-400 animate-spin" />
                    <Sparkles className="w-5 h-5 text-amber-400" />
                </div>
                <div className="text-center">
                    <p className="text-sm font-semibold text-white">Memuat Parameter Sistem...</p>
                    <p className="text-xs text-slate-500 mt-1">Mengambil konfigurasi VIP, iklan, dan tata letak provider</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-20">
            {/* Header Sticky Bar */}
            <div className="sticky top-20 z-20 -mx-6 sm:-mx-8 px-6 sm:px-8 py-4 bg-[#07090E]/85 backdrop-blur-xl border-b border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                        <span className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                            <Settings size={20} />
                        </span>
                        <h1 className="text-2xl font-bold tracking-tight text-white">System & App Configuration</h1>
                    </div>
                    <p className="text-xs text-slate-400">
                        Pusat kendali operasional AsianDrama: Identitas branding, monetisasi VIP, iklan, dan tata letak rotasi provider.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="gold-btn px-6 py-2.5 rounded-xl flex items-center gap-2 text-xs font-bold shadow-lg"
                    >
                        {saving ? (
                            <><Loader2 size={16} className="animate-spin text-black" /> Menyimpan...</>
                        ) : (
                            <><Save size={16} /> Simpan Pengaturan</>
                        )}
                    </button>
                </div>
            </div>

            {/* Segmented Luxury Navigation Tabs */}
            <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-white/[0.03] border border-white/[0.06] overflow-x-auto">
                {[
                    { key: 'identity' as const, label: 'Identitas & Branding', icon: Shield },
                    { key: 'vip' as const, label: 'Paket VIP & Koin', icon: Crown },
                    { key: 'ads' as const, label: 'Iklan & Free Mode', icon: Tv },
                    { key: 'layout' as const, label: 'Rotasi Provider Drama', icon: Layers },
                ].map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.key;
                    return (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                                isActive
                                    ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-md'
                                    : 'text-slate-400 hover:text-white hover:bg-white/[0.03] border border-transparent'
                            }`}
                        >
                            <Icon size={14} className={isActive ? 'text-amber-400' : 'text-slate-500'} />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* TAB CONTENT 1: IDENTITAS & BRANDING */}
            {activeTab === 'identity' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    <div className="lg:col-span-8 space-y-6">
                        <div className="glass-panel p-6 sm:p-7 space-y-6">
                            <div className="pb-4 border-b border-white/[0.06]">
                                <h2 className="text-base font-bold text-white tracking-tight">Identitas Aplikasi</h2>
                                <p className="text-xs text-slate-400 mt-1">
                                    Konfigurasi nama resmi dan logo utama yang tampil di seluruh antarmuka mobile app.
                                </p>
                            </div>

                            <div className="space-y-5">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-2">Nama Aplikasi</label>
                                    <input
                                        type="text"
                                        value={appName}
                                        onChange={(e) => setAppName(e.target.value)}
                                        className="w-full bg-[#0B0F17] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-400/60 transition-colors"
                                    />
                                </div>

                                {/* App Icon Card */}
                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-2">Icon / Logo Aplikasi</label>
                                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
                                        <div className="w-20 h-20 rounded-2xl bg-black/60 border border-white/15 overflow-hidden flex items-center justify-center flex-shrink-0 shadow-lg relative group">
                                            {appIcon ? (
                                                <img src={appIcon} alt="App Icon" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110" />
                                            ) : (
                                                <ImageIcon className="text-slate-600" size={32} />
                                            )}
                                        </div>

                                        <div className="space-y-2 flex-1">
                                            <input
                                                ref={fileInputRef}
                                                type="file"
                                                accept=".jpg,.jpeg,.png"
                                                onChange={handleIconUpload}
                                                className="hidden"
                                            />
                                            <div className="flex items-center gap-3">
                                                <button
                                                    type="button"
                                                    onClick={() => fileInputRef.current?.click()}
                                                    disabled={uploading}
                                                    className="px-4 py-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] border border-white/10 text-xs font-semibold text-white flex items-center gap-2 transition-colors disabled:opacity-50"
                                                >
                                                    {uploading ? (
                                                        <><Loader2 size={14} className="animate-spin text-amber-400" /> Mengunggah...</>
                                                    ) : (
                                                        <><Upload size={14} /> Ganti Icon Aplikasi</>
                                                    )}
                                                </button>
                                                {appIcon && (
                                                    <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                                                        <CheckCircle2 size={12} /> Icon Aktif
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-[11px] text-slate-500">Format PNG atau JPG dengan rasio 1:1 persegi, maksimal 2MB.</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Reward Banner Subtitle */}
                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-2">
                                        Teks Pengumuman Banner Hadiah (Tab Hadiah)
                                    </label>
                                    <textarea
                                        value={rewardBottomText}
                                        onChange={(e) => setRewardBottomText(e.target.value)}
                                        rows={3}
                                        className="w-full bg-[#0B0F17] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-400/60 transition-colors resize-none leading-relaxed"
                                    />
                                    <p className="text-[11px] text-slate-500 mt-1">Ditampilkan di footer halaman klaim reward koin mobile app.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Maintenance Mode Card */}
                    <div className="lg:col-span-4">
                        <div className={`glass-panel p-6 sm:p-7 space-y-4 border transition-all ${
                            maintenanceMode ? 'border-rose-500/40 bg-rose-500/[0.04]' : 'border-white/[0.06]'
                        }`}>
                            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                                <div className="flex items-center gap-2 text-xs font-bold text-white">
                                    <AlertTriangle size={16} className={maintenanceMode ? 'text-rose-400' : 'text-slate-400'} />
                                    Mode Pemeliharaan (Maintenance)
                                </div>
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                    maintenanceMode ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-white/[0.04] text-slate-500'
                                }`}>
                                    {maintenanceMode ? 'ON' : 'OFF'}
                                </span>
                            </div>

                            <p className="text-xs text-slate-400 leading-relaxed">
                                Jika diaktifkan, seluruh pengguna mobile app akan diarahkan ke layar maintenance dan dilarang mengakses konten video sementara waktu.
                            </p>

                            <div className="pt-2">
                                <button
                                    type="button"
                                    onClick={() => setMaintenanceMode(!maintenanceMode)}
                                    className={`w-full py-3 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                                        maintenanceMode 
                                            ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' 
                                            : 'bg-white/[0.05] hover:bg-white/[0.08] text-slate-300 border border-white/10'
                                    }`}
                                >
                                    {maintenanceMode ? 'Matikan Mode Maintenance' : 'Aktifkan Mode Maintenance'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB CONTENT 2: PAKET VIP & KOIN */}
            {activeTab === 'vip' && (
                <div className="space-y-8">
                    {/* Feature Toggles */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Real Money VIP Gateway */}
                        <div className="glass-panel p-6 space-y-4">
                            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                                <div className="flex items-center gap-2.5">
                                    <div className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                                        <CreditCard size={16} />
                                    </div>
                                    <div>
                                        <h3 className="text-xs font-bold text-white">Gerbang VIP Uang Asli</h3>
                                        <p className="text-[10px] text-slate-400">In-App Purchase & RevenueCat</p>
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    onClick={() => setVipMoneyEnabled(!vipMoneyEnabled)}
                                    className={`w-12 h-6 rounded-full transition-colors relative ${
                                        vipMoneyEnabled ? 'bg-amber-500' : 'bg-white/10'
                                    }`}
                                >
                                    <span className={`w-4 h-4 rounded-full bg-black absolute top-1 transition-transform ${
                                        vipMoneyEnabled ? 'left-7' : 'left-1'
                                    }`} />
                                </button>
                            </div>

                            {!vipMoneyEnabled && (
                                <div className="space-y-1.5 p-3 rounded-xl bg-rose-500/[0.05] border border-rose-500/20">
                                    <label className="text-[11px] font-semibold text-rose-300">Pesan Pop-up Saat Dimatikan:</label>
                                    <input
                                        type="text"
                                        value={vipMoneyMsg}
                                        onChange={(e) => setVipMoneyMsg(e.target.value)}
                                        className="w-full bg-[#0B0F17] border border-rose-500/30 rounded-lg px-3 py-1.5 text-xs text-white"
                                    />
                                </div>
                            )}
                            <p className="text-[11px] text-slate-500">
                                Aktifkan untuk memunculkan tombol beli langganan VIP via Google Play Store.
                            </p>
                        </div>

                        {/* Coin Exchange VIP Gateway */}
                        <div className="glass-panel p-6 space-y-4">
                            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                                <div className="flex items-center gap-2.5">
                                    <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                                        <Coins size={16} />
                                    </div>
                                    <div>
                                        <h3 className="text-xs font-bold text-white">Tukar Koin ke VIP</h3>
                                        <p className="text-[10px] text-slate-400">Fitur Reward Gamifikasi</p>
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    onClick={() => setVipCoinEnabled(!vipCoinEnabled)}
                                    className={`w-12 h-6 rounded-full transition-colors relative ${
                                        vipCoinEnabled ? 'bg-emerald-500' : 'bg-white/10'
                                    }`}
                                >
                                    <span className={`w-4 h-4 rounded-full bg-black absolute top-1 transition-transform ${
                                        vipCoinEnabled ? 'left-7' : 'left-1'
                                    }`} />
                                </button>
                            </div>

                            {!vipCoinEnabled && (
                                <div className="space-y-1.5 p-3 rounded-xl bg-rose-500/[0.05] border border-rose-500/20">
                                    <label className="text-[11px] font-semibold text-rose-300">Pesan Pop-up Saat Dimatikan:</label>
                                    <input
                                        type="text"
                                        value={vipCoinMsg}
                                        onChange={(e) => setVipCoinMsg(e.target.value)}
                                        className="w-full bg-[#0B0F17] border border-rose-500/30 rounded-lg px-3 py-1.5 text-xs text-white"
                                    />
                                </div>
                            )}
                            <p className="text-[11px] text-slate-500">
                                Izinkan user menukar koin yang dikumpulkan dari nonton/claim menjadi durasi VIP Pass.
                            </p>
                        </div>
                    </div>

                    {/* Pricing Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Real Money Pricing */}
                        <div className="glass-panel p-6 sm:p-7 space-y-5">
                            <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
                                <div>
                                    <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                                        <CreditCard size={16} className="text-amber-400" /> Tarif VIP Uang Asli (IDR)
                                    </h3>
                                    <p className="text-xs text-slate-400 mt-0.5">Digunakan sebagai patokan harga resmi langganan.</p>
                                </div>
                                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                    Rupiah (Rp)
                                </span>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">VIP 1 Bulan</label>
                                    <div className="relative">
                                        <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-500">Rp</span>
                                        <input
                                            type="number"
                                            value={vipMonthlyPrice}
                                            onChange={(e) => setVipMonthlyPrice(e.target.value)}
                                            className="w-full bg-[#0B0F17] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-amber-400/60"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">VIP 3 Bulan</label>
                                    <div className="relative">
                                        <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-500">Rp</span>
                                        <input
                                            type="number"
                                            value={vip3MonthPrice}
                                            onChange={(e) => setVip3MonthPrice(e.target.value)}
                                            className="w-full bg-[#0B0F17] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-amber-400/60"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">VIP 1 Tahun</label>
                                    <div className="relative">
                                        <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-500">Rp</span>
                                        <input
                                            type="number"
                                            value={vip1YearPrice}
                                            onChange={(e) => setVip1YearPrice(e.target.value)}
                                            className="w-full bg-[#0B0F17] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-amber-400/60"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Coin Exchange Pricing */}
                        <div className="glass-panel p-6 sm:p-7 space-y-5">
                            <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
                                <div>
                                    <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                                        <Coins size={16} className="text-emerald-400" /> Tarif Tukar Koin ke VIP
                                    </h3>
                                    <p className="text-xs text-slate-400 mt-0.5">Jumlah saldo koin yang dipotong saat user menukar.</p>
                                </div>
                                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                    Koin Saldo
                                </span>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">Tukar VIP 1 Bulan</label>
                                    <div className="relative">
                                        <Coins size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                                        <input
                                            type="number"
                                            value={vipCoin1Month}
                                            onChange={(e) => setVipCoin1Month(e.target.value)}
                                            className="w-full bg-[#0B0F17] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-400/60"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">Tukar VIP 3 Bulan</label>
                                    <div className="relative">
                                        <Coins size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                                        <input
                                            type="number"
                                            value={vipCoin3Month}
                                            onChange={(e) => setVipCoin3Month(e.target.value)}
                                            className="w-full bg-[#0B0F17] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-400/60"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">Tukar VIP 1 Tahun</label>
                                    <div className="relative">
                                        <Coins size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                                        <input
                                            type="number"
                                            value={vipCoin1Year}
                                            onChange={(e) => setVipCoin1Year(e.target.value)}
                                            className="w-full bg-[#0B0F17] border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-400/60"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB CONTENT 3: IKLAN & FREE MODE */}
            {activeTab === 'ads' && (
                <div className="max-w-3xl space-y-6">
                    <div className="glass-panel p-6 sm:p-7 space-y-6">
                        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
                            <div>
                                <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                                    <Tv size={18} className="text-amber-400" /> Mesin Iklan Interstitial Video
                                </h2>
                                <p className="text-xs text-slate-400 mt-1">
                                    Atur frekuensi penayangan iklan saat perpindahan episode bagi pengguna reguler (non-VIP).
                                </p>
                            </div>

                            <button
                                type="button"
                                onClick={() => setAdEnabled(!adEnabled)}
                                className={`w-12 h-6 rounded-full transition-colors relative ${
                                    adEnabled ? 'bg-amber-500' : 'bg-white/10'
                                }`}
                            >
                                <span className={`w-4 h-4 rounded-full bg-black absolute top-1 transition-transform ${
                                    adEnabled ? 'left-7' : 'left-1'
                                }`} />
                            </button>
                        </div>

                        <div className="space-y-5">
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                                    Batas Episode Gratis Awal (Tanpa Iklan)
                                </label>
                                <input
                                    type="number"
                                    value={freeEpisodes}
                                    onChange={(e) => setFreeEpisodes(e.target.value)}
                                    min="0"
                                    className="w-full bg-[#0B0F17] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-amber-400/60"
                                />
                                <p className="text-[11px] text-slate-500 mt-1">
                                    Episode 1 hingga episode ke-{freeEpisodes} bebas iklan agar user baru betah menonton hook awal drama.
                                </p>
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                                    Interval Pemutaran Iklan (Setiap N Episode)
                                </label>
                                <input
                                    type="number"
                                    value={adInterval}
                                    onChange={(e) => setAdInterval(e.target.value)}
                                    min="1"
                                    className="w-full bg-[#0B0F17] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-amber-400/60"
                                />
                                <p className="text-[11px] text-slate-500 mt-1">
                                    Iklan interstitial akan diputar setiap {adInterval} episode sekali setelah kuota episode gratis terlampaui.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* TAB CONTENT 4: ROTASI PROVIDER DRAMA */}
            {activeTab === 'layout' && (
                <div className="max-w-4xl space-y-6">
                    <div className="glass-panel p-6 sm:p-7 space-y-6">
                        <div className="pb-4 border-b border-white/[0.06]">
                            <div className="flex items-center justify-between">
                                <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                                    <Layers size={18} className="text-amber-400" /> Urutan Tayang Provider di "Semua Drama"
                                </h2>
                                <span className="text-[11px] text-amber-400 font-semibold bg-amber-500/10 px-2.5 py-1 rounded-lg border border-amber-500/20">
                                    Drag Baris Untuk Ubah Urutan
                                </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-1">
                                Algoritma agregator menarik judul drama secara bergiliran per batch. Geser posisi baris untuk menentukan prioritas provider utama.
                            </p>
                        </div>

                        <div className="space-y-3">
                            {providerOrder.map((providerId, index) => {
                                const conf = PROVIDER_NAMES[providerId] || { label: providerId, badge: 'PD', color: 'bg-white/10 text-white' };
                                const stateVals: Record<string, { val: string, set: (v: string) => void }> = {
                                    dramabox: { val: layoutDramabox, set: setLayoutDramabox },
                                    netshort: { val: layoutNetshort, set: setLayoutNetshort },
                                    flickreels: { val: layoutFlickreels, set: setLayoutFlickreels },
                                    dramanova: { val: layoutDramanova, set: setLayoutDramanova },
                                    dramawave: { val: layoutDramawave, set: setLayoutDramawave },
                                    melolo: { val: layoutMelolo, set: setLayoutMelolo }
                                };
                                const state = stateVals[providerId];
                                if (!state) return null;

                                return (
                                    <div 
                                        key={providerId}
                                        draggable
                                        onDragStart={() => { dragItem.current = index; }}
                                        onDragEnter={() => { dragOverItem.current = index; }}
                                        onDragEnd={handleSort}
                                        onDragOver={(e) => e.preventDefault()}
                                        className="flex items-center gap-4 bg-[#0B0F17] hover:bg-[#101622] border border-white/10 hover:border-amber-500/40 rounded-xl px-4 py-3 cursor-grab active:cursor-grabbing transition-all group shadow-md"
                                    >
                                        <div className="p-1 rounded-lg text-slate-500 group-hover:text-amber-400 transition-colors">
                                            <GripVertical size={18} />
                                        </div>

                                        <div className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-xs font-bold text-amber-400">
                                            #{index + 1}
                                        </div>

                                        <div className="flex-1 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                            <div className="flex items-center gap-2.5">
                                                <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold border ${conf.color}`}>
                                                    {conf.badge}
                                                </span>
                                                <span className="text-xs font-bold text-white tracking-tight">
                                                    {conf.label}
                                                </span>
                                            </div>

                                            <div className="flex items-center gap-2 self-end sm:self-center">
                                                <label className="text-[11px] text-slate-400 font-medium">Batas Tarik:</label>
                                                <div className="relative">
                                                    <input 
                                                        type="number" 
                                                        value={state.val} 
                                                        onChange={e => state.set(e.target.value)} 
                                                        min="1" 
                                                        className="w-20 bg-black/60 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-white text-center focus:outline-none focus:border-amber-400/60" 
                                                    />
                                                </div>
                                                <span className="text-[10px] text-slate-500">drama/giliran</span>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            )}

            {/* Luxury Toast Notification */}
            {toast && toast.show && (
                <div className={`fixed bottom-6 right-6 flex items-center gap-3 px-6 py-4 rounded-2xl shadow-2xl z-50 backdrop-blur-xl border transition-all duration-300 ${
                    toast.type === 'success' 
                        ? 'bg-[#0B1510]/90 border-emerald-500/40 text-emerald-300' 
                        : 'bg-[#180B0D]/90 border-rose-500/40 text-rose-300'
                }`}>
                    {toast.type === 'success' ? (
                        <CheckCircle2 size={20} className="text-emerald-400" />
                    ) : (
                        <XCircle size={20} className="text-rose-400" />
                    )}
                    <span className="text-xs font-semibold">{toast.message}</span>
                </div>
            )}
        </div>
    );
}
