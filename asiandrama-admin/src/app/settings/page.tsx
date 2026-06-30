'use client';

import { supabase } from '@/lib/supabase';
import { Image as ImageIcon, Save, ToggleLeft, ToggleRight, Upload, CheckCircle2, XCircle, GripVertical } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export default function SettingsPage() {
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
                throw new Error(data.error || 'Failed to save settings');
            }

            showToast('Settings saved successfully!', 'success');
        } catch (error: any) {
            console.error('Save error:', error);
            showToast('Failed to save settings: ' + error.message, 'error');
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

                        {/* Reward Bottom Text */}
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Teks Banner Hadiah VIP (Tab Hadiah)</label>
                            <textarea
                                value={rewardBottomText}
                                onChange={(e) => setRewardBottomText(e.target.value)}
                                rows={2}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-amber-500"
                            />
                        </div>

                        {/* Maintenance Mode Toggle */}
                        <div className="flex items-center justify-between pt-4 border-t border-gray-800">
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
                            <label className="block text-sm text-gray-400 mb-2">Harga VIP 1 Bulan dengan Uang Asli (Rp)</label>
                            <input
                                type="number"
                                value={vipMonthlyPrice}
                                onChange={(e) => setVipMonthlyPrice(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Harga VIP 3 Bulan dengan Uang Asli (Rp)</label>
                            <input
                                type="number"
                                value={vip3MonthPrice}
                                onChange={(e) => setVip3MonthPrice(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Harga VIP 1 Tahun dengan Uang Asli (Rp)</label>
                            <input
                                type="number"
                                value={vip1YearPrice}
                                onChange={(e) => setVip1YearPrice(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                            <p className="text-xs text-gray-500 mt-2">Harga-harga VIP ini digunakan sebagai referensi jika koneksi Google Play tertunda.</p>
                        </div>

                        {/* Divider */}
                        <div className="border-t border-gray-700 my-4"></div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Harga VIP 1 Bulan dengan Koin</label>
                            <input
                                type="number"
                                value={vipCoin1Month}
                                onChange={(e) => setVipCoin1Month(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Harga VIP 3 Bulan dengan Koin</label>
                            <input
                                type="number"
                                value={vipCoin3Month}
                                onChange={(e) => setVipCoin3Month(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Harga VIP 1 Tahun dengan Koin</label>
                            <input
                                type="number"
                                value={vipCoin1Year}
                                onChange={(e) => setVipCoin1Year(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-amber-500"
                            />
                        </div>
                    </div>
                </div>

                {/* VIP Feature Toggles */}
                <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
                    <h2 className="font-semibold mb-4">Pengaturan Akses Fitur VIP</h2>

                    <div className="space-y-6">
                        {/* VIP Real Money */}
                        <div className="space-y-4 pb-4 border-b border-gray-800">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="font-medium">Tombol VIP Uang Asli</p>
                                    <p className="text-sm text-gray-500">Aktifkan atau matikan fitur bayar dengan uang asli (RevenueCat)</p>
                                </div>
                                <button
                                    onClick={() => setVipMoneyEnabled(!vipMoneyEnabled)}
                                    className={`text-3xl ${vipMoneyEnabled ? 'text-green-500' : 'text-gray-600'}`}
                                >
                                    {vipMoneyEnabled ? <ToggleRight /> : <ToggleLeft />}
                                </button>
                            </div>
                            
                            {!vipMoneyEnabled && (
                                <div className="mt-2">
                                    <label className="block text-sm text-gray-400 mb-2">Pesan Peringatan (saat dimatikan)</label>
                                    <input
                                        type="text"
                                        value={vipMoneyMsg}
                                        onChange={(e) => setVipMoneyMsg(e.target.value)}
                                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-red-500"
                                        placeholder="Fitur VIP sedang dalam pengembangan."
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Pesan ini akan muncul sebagai pop-up ketika user klik tombol Upgrade.</p>
                                </div>
                            )}
                        </div>

                        {/* VIP Coin Exchange */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="font-medium">Tombol Tukar VIP (Koin)</p>
                                    <p className="text-sm text-gray-500">Aktifkan atau matikan fitur tukar koin ke VIP</p>
                                </div>
                                <button
                                    onClick={() => setVipCoinEnabled(!vipCoinEnabled)}
                                    className={`text-3xl ${vipCoinEnabled ? 'text-green-500' : 'text-gray-600'}`}
                                >
                                    {vipCoinEnabled ? <ToggleRight /> : <ToggleLeft />}
                                </button>
                            </div>

                            {!vipCoinEnabled && (
                                <div className="mt-2">
                                    <label className="block text-sm text-gray-400 mb-2">Pesan Peringatan (saat dimatikan)</label>
                                    <input
                                        type="text"
                                        value={vipCoinMsg}
                                        onChange={(e) => setVipCoinMsg(e.target.value)}
                                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-red-500"
                                        placeholder="Fitur Tukar Koin sedang dalam perbaikan."
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Pesan ini akan muncul sebagai pop-up ketika user klik tombol Tukar VIP.</p>
                                </div>
                            )}
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
                        Tentukan jumlah maksimal drama yang ditarik per giliran rotasi. Drag baris untuk mengubah urutan tayang.
                    </p>
                    <div className="space-y-3">
                        {providerOrder.map((providerId, index) => {
                            const labels: Record<string, string> = {
                                dramabox: 'Dramabox',
                                netshort: 'Netshort',
                                flickreels: 'FlickReels',
                                dramanova: 'DramaNova',
                                dramawave: 'DramaWave',
                                melolo: 'Melolo'
                            };
                            const stateVals: Record<string, { val: string, set: (v: string) => void }> = {
                                dramabox: { val: layoutDramabox, set: setLayoutDramabox },
                                netshort: { val: layoutNetshort, set: setLayoutNetshort },
                                flickreels: { val: layoutFlickreels, set: setLayoutFlickreels },
                                dramanova: { val: layoutDramanova, set: setLayoutDramanova },
                                dramawave: { val: layoutDramawave, set: setLayoutDramawave },
                                melolo: { val: layoutMelolo, set: setLayoutMelolo }
                            };
                            
                            const label = labels[providerId] || providerId;
                            const state = stateVals[providerId];
                            if (!state) return null;

                            return (
                                <div 
                                    key={providerId}
                                    draggable
                                    onDragStart={(e) => { dragItem.current = index; }}
                                    onDragEnter={(e) => { dragOverItem.current = index; }}
                                    onDragEnd={handleSort}
                                    onDragOver={(e) => e.preventDefault()}
                                    className="flex items-center gap-4 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 cursor-grab active:cursor-grabbing hover:border-amber-500/50 transition-colors"
                                >
                                    <GripVertical size={20} className="text-gray-500" />
                                    <div className="flex-1 flex items-center justify-between">
                                        <span className="font-medium text-gray-300">
                                            {index + 1}. {label}
                                        </span>
                                        <div className="flex items-center gap-3">
                                            <label className="text-sm text-gray-500">Maks. ditarik:</label>
                                            <input 
                                                type="number" 
                                                value={state.val} 
                                                onChange={e => state.set(e.target.value)} 
                                                min="1" 
                                                className="w-20 bg-gray-900 border border-gray-700 rounded-md px-3 py-1.5 focus:outline-none focus:border-amber-500 text-center" 
                                            />
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
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
