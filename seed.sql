-- LEA seed data: one sample album with 4 tracks

INSERT INTO albums (title, artist, price_cents, cover_art_url, release_date, description) VALUES (
    'Midnight Sessions',
    'The Wandering Hour',
    1200,
    '/static/img/midnight-sessions.jpg',
    '2026-05-01',
    'Recorded over three nights in an abandoned chapel outside Asheville. A meditation on solitude, memory, and the way certain hours of the night belong to no one.'
);

INSERT INTO tracks (album_id, title, track_number, audio_url, duration_seconds, lyrics, notes) VALUES
    (1, 'Before the Wake', 1, '/static/audio/01-before-the-wake.mp3', 247, 'Lyrics for track 1...', 'Written in one sitting at 3am. The piano was slightly out of tune and we left it that way.'),
    (1, 'Salt and Smoke', 2, '/static/audio/02-salt-and-smoke.mp3', 312, 'Lyrics for track 2...', 'This song is about my grandmother. The harmonies on the chorus were recorded outside, you can hear cicadas.'),
    (1, 'Houses That Used to Be Ours', 3, '/static/audio/03-houses.mp3', 289, 'Lyrics for track 3...', 'Originally a B-side. We almost cut it but it became the heart of the record.'),
    (1, 'Nothing Stays', 4, '/static/audio/04-nothing-stays.mp3', 401, 'Lyrics for track 4...', 'The longest take. One pass, no overdubs.');