// src/lib/utils/processBarChartData.js
export function processBarChartData(fullData, startYear, endYear, selectedView, flagSum) {
    const sliceData = fullData.filter(d => d.startYear >= startYear && d.startYear <= endYear);

    const genreCounts = {};

    sliceData.forEach(d => { 
        d.genres.forEach(genre => {
            if (genre) {
                if (flagSum) {
                    genreCounts[genre] = (genreCounts[genre] || 0) + ((d[selectedView] || 0) > 0 ? 1 : 0);
                } else {
                    genreCounts[genre] = (genreCounts[genre] || 0) + (d[selectedView] || 0);
                }
            }
        });
    });

    const genres = Object.keys(genreCounts);
    const values = Object.values(genreCounts);

    const sorted = genres
        .map((genre, i) => ({ genre, value: values[i] }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 10);

    return {
        genres: sorted.map(d => d.genre),
        values: sorted.map(d => d.value)
    };
}
