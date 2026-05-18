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
    (1, 'Actress Enter Scene', 1, '/static/audio/88bpm actress enter scene.mp3', NULL, NULL, NULL),
    (1, 'An Ocean Breeze in 3025', 2, '/static/audio/an ocean breeze in 3025.mp3', NULL, NULL, NULL),
    (1, 'Endlessly Empathy', 3, '/static/audio/07.27 endlessly empathy 116bpm demo.mp3', NULL, NULL, NULL),
    (1, 'HEART 2 MACHINE', 4, '/static/audio/HEART 2 MACHINE.mp3', NULL, NULL, NULL);