// Test episode generation logic (mimics parseDramasData)
const sampleDrama = {
    id: "894",
    title: "Adik lpar Memanjakanku（Dubbing）",
    total_episodes: 52,
    cover_url: "/api/stream/flickreels/...",
};

console.log('Input drama:', sampleDrama);

// Generate episodes (same logic as parseDramasData)
const totalEpisodes = sampleDrama.total_episodes;
const episodes = Array.from({ length: totalEpisodes }, (_, i) => ({
    chapter_id: `${sampleDrama.id}_ep${i + 1}`,
    title: `Episode ${i + 1}`,
    chapter_num: i + 1,
    duration: 0,
    cover_url: sampleDrama.cover_url,
    is_free: true,
    is_vip: false,
    cost_coin: 0,
    hls_url: '',
}));

console.log('\nGenerated episodes count:', episodes.length);
console.log('First episode:', episodes[0]);
console.log('Last episode:', episodes[episodes.length - 1]);

// Check for duplicate keys
const keys = episodes.map(ep => ep.chapter_id);
const uniqueKeys = new Set(keys);
console.log('\nUnique keys:', uniqueKeys.size, '/ Total:', keys.length);
console.log('Has duplicates:', uniqueKeys.size !== keys.length);
