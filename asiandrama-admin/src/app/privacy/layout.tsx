export default function PrivacyLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-gray-950 text-white">
            {children}
        </div>
    );
}
