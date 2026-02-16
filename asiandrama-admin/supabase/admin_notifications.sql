-- ============================================
-- Admin Notifications Table
-- ============================================

CREATE TABLE IF NOT EXISTS admin_notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'info' CHECK (type IN ('info', 'warning', 'maintenance')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- When a new notification is activated, deactivate all others
CREATE OR REPLACE FUNCTION deactivate_old_notifications()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = true THEN
        UPDATE admin_notifications 
        SET is_active = false, updated_at = NOW()
        WHERE id != NEW.id AND is_active = true;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_deactivate_old_notifications
    AFTER INSERT OR UPDATE OF is_active ON admin_notifications
    FOR EACH ROW
    WHEN (NEW.is_active = true)
    EXECUTE FUNCTION deactivate_old_notifications();

-- RLS Policies
ALTER TABLE admin_notifications ENABLE ROW LEVEL SECURITY;

-- Everyone can read active notifications (for mobile app)
CREATE POLICY "Anyone can read active notifications"
    ON admin_notifications
    FOR SELECT
    USING (true);

-- Only authenticated admins can insert/update/delete
CREATE POLICY "Admins can manage notifications"
    ON admin_notifications
    FOR ALL
    USING (auth.role() = 'service_role');

-- Index for quick lookup of active notification
CREATE INDEX idx_admin_notifications_active 
    ON admin_notifications (is_active, created_at DESC) 
    WHERE is_active = true;
