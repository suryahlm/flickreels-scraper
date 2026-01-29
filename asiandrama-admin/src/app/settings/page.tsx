'use client';

import { useState, useEffect, useRef } from 'react';
import { Save, ToggleLeft, ToggleRight, Upload, Image as ImageIcon } from 'lucide-react';
import { supabase } from '@/lib/supabase';

export default function SettingsPage() {
    const [appName, setAppName] = useState('AsianDrama');
    const [appIcon, setAppIcon] = useState<string | null>(null);
    const [maintenanceMode, setMaintenanceMode] = useState(false);
    const [coinPrice, setCoinPrice] = useState('10000');
    const [vipMonthlyPrice, setVipMonthlyPrice] = useState('49000');
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

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
            alert('Hanya file JPG atau PNG yang diperbolehkan');
            return;
        }

        // Validate file size (max 2MB)
        if (file.size > 2 * 1024 * 1024) {
            alert('Ukuran file maksimal 2MB');
            return;
        }

        setUploading(true);

        try {
            // Upload to Supabase Storage
            const fileName = `app-icon-${Date.now()}.${file.name.split('.').pop()}`;
            const { data, error } = await supabase.storage
                .from('assets')
                .upload(fileName, file, { upsert: true });

            if (error) throw error;

            // Get public URL
            const { data: urlData } = supabase.storage.from('assets').getPublicUrl(fileName);
            setAppIcon(urlData.publicUrl);

            alert('Icon berhasil diupload!');
        } catch (error: any) {
            console.error('Upload error:', error);
            alert('Gagal upload: ' + error.message);
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
        ];

        for (const setting of settings) {
            await supabase
                .from('app_settings')
                .upsert({ key: setting.key, value: setting.value, updated_at: new Date().toISOString() });
        }

        alert('Settings saved!');
    };

    if (loading) return <div className="text-center py-20">Loading...</div>;

    return (
        <div>
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

                {/* Save Button */}
                <button
                    onClick={handleSave}
                    className="bg-amber-500 hover:bg-amber-600 px-6 py-3 rounded-lg flex items-center gap-2"
                >
                    <Save size={20} /> Simpan Settings
                </button>
            </div>
        </div>
    );
}
