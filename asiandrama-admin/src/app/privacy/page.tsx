import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Privacy Policy - AsianDrama",
    description: "Privacy Policy for the AsianDrama mobile application",
};

export default function PrivacyPolicy() {
    return (
        <div className="max-w-3xl mx-auto px-6 py-12">
            <h1 className="text-3xl font-bold mb-2">Privacy Policy</h1>
            <p className="text-gray-400 mb-8">Last updated: February 17, 2026</p>

            <div className="space-y-8 text-gray-300 leading-relaxed">
                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">1. Introduction</h2>
                    <p>
                        Welcome to AsianDrama (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;). We are committed to protecting your privacy.
                        This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you
                        use our mobile application (&quot;App&quot;). Please read this policy carefully.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">2. Information We Collect</h2>
                    <h3 className="text-lg font-medium text-gray-200 mb-2">2.1 Personal Information</h3>
                    <p className="mb-3">When you create an account, we may collect:</p>
                    <ul className="list-disc pl-6 space-y-1">
                        <li>Email address</li>
                        <li>Display name</li>
                        <li>Profile picture (if provided via Google Sign-In)</li>
                    </ul>

                    <h3 className="text-lg font-medium text-gray-200 mb-2 mt-4">2.2 Usage Data</h3>
                    <p className="mb-3">We automatically collect certain information when you use the App:</p>
                    <ul className="list-disc pl-6 space-y-1">
                        <li>Watch history and bookmarks</li>
                        <li>App interaction data</li>
                        <li>Device type and operating system</li>
                    </ul>

                    <h3 className="text-lg font-medium text-gray-200 mb-2 mt-4">2.3 Advertising Data</h3>
                    <p>
                        We use Google AdMob to display advertisements. AdMob may collect device identifiers and
                        usage data for personalized advertising. You can opt out of personalized ads through your
                        device settings.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">3. How We Use Your Information</h2>
                    <p className="mb-3">We use the collected information to:</p>
                    <ul className="list-disc pl-6 space-y-1">
                        <li>Provide and maintain the App</li>
                        <li>Manage your account and preferences</li>
                        <li>Track watch history and bookmarks</li>
                        <li>Operate the coin reward system</li>
                        <li>Send important notifications about app updates or maintenance</li>
                        <li>Improve user experience and app performance</li>
                        <li>Display relevant advertisements</li>
                    </ul>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">4. Data Storage & Security</h2>
                    <p>
                        Your data is stored securely using Supabase, which provides enterprise-grade security with
                        Row Level Security (RLS) policies. We implement appropriate technical and organizational
                        measures to protect your personal information against unauthorized access, alteration,
                        disclosure, or destruction.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">5. Third-Party Services</h2>
                    <p className="mb-3">Our App uses the following third-party services:</p>
                    <ul className="list-disc pl-6 space-y-1">
                        <li><strong>Google Sign-In</strong> — for authentication</li>
                        <li><strong>Google AdMob</strong> — for displaying advertisements</li>
                        <li><strong>Supabase</strong> — for data storage and authentication</li>
                        <li><strong>Cloudflare R2</strong> — for content delivery</li>
                    </ul>
                    <p className="mt-3">
                        Each of these services has their own privacy policies. We encourage you to review their
                        respective policies.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">6. Children&apos;s Privacy</h2>
                    <p>
                        Our App is not intended for children under the age of 13. We do not knowingly collect
                        personal information from children under 13. If we discover that a child under 13 has
                        provided us with personal information, we will delete it immediately.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">7. Your Rights</h2>
                    <p className="mb-3">You have the right to:</p>
                    <ul className="list-disc pl-6 space-y-1">
                        <li>Access your personal data</li>
                        <li>Update or correct your information</li>
                        <li>Delete your account and associated data</li>
                        <li>Opt out of personalized advertising</li>
                    </ul>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">8. Data Retention</h2>
                    <p>
                        We retain your personal information for as long as your account is active or as needed to
                        provide you services. You may request deletion of your account at any time by contacting us.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">9. Changes to This Policy</h2>
                    <p>
                        We may update this Privacy Policy from time to time. We will notify you of any changes by
                        posting the new Privacy Policy on this page and updating the &quot;Last updated&quot; date.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">10. Contact Us</h2>
                    <p>
                        If you have any questions about this Privacy Policy, please contact us at:
                    </p>
                    <p className="mt-2 text-purple-400">suryahalim26@gmail.com</p>
                </section>
            </div>

            <div className="mt-12 pt-6 border-t border-gray-800 text-center text-gray-500 text-sm">
                © 2026 AsianDrama. All rights reserved.
            </div>
        </div>
    );
}
